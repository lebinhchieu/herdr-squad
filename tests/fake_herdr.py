"""A fake herdr socket for the squad-board recorder tests.

Speaks herdr's newline-delimited JSON, with shapes captured from herdr 0.9.3 on 2026-10-12 (read-only:
`herdr api snapshot` and a subscription that only listened; paths, ids and session values replaced):

  request   {"id": "...", "method": "session.snapshot", "params": {}}
  reply     {"id": "...", "result": {"type": "session_snapshot", "snapshot": {"agents": [...], ...}}}
  request   {"id": "...", "method": "events.subscribe", "params": {"subscriptions": [
                {"type": "pane.agent_status_changed", "pane_id": "wA:pD"}, {"type": "pane.created"}]}}
  reply     {"id": "...", "result": {"type": "subscription_started"}}
  event     {"data": {"agent": "claude", "agent_status": "working", "pane_id": "wA:pD",
                      "workspace_id": "wA"}, "event": "pane.agent_status_changed"}
  error     {"id": "...", "error": {"code": "invalid_request", "message": "..."}}

What the real socket does that the recorder must live with, and so does this fake:
  - a pane.agent_status_changed subscription without a pane_id is an error;
  - once a connection has subscribed it takes no more requests (herdr resets it), so snapshots
    need a connection of their own;
  - events carry no agent name and no time.
The pane.created event shape comes from herdr's schema (`data.pane`), not from a live capture: a
read-only capture cannot create a pane.

Tests give the snapshot rows; the fake never reads anything real.
"""
import json
import os
import socket
import threading
import time

WORKSPACE = "wA"
READY_DEADLINE_S = 10


def agent_entry(row):
    """A snapshot `agents[]` entry in herdr's shape from a test row."""
    return {
        "agent": "claude",
        "agent_session": {"agent": "claude", "kind": "id", "source": "herdr:claude",
                          "value": row.get("session") or "session-of-" + row["name"]},
        "agent_status": row["status"],
        "cwd": "/work/squad", "focused": False, "foreground_cwd": "/work/squad",
        "interactive_ready": True, "name": row["name"], "pane_id": row["pane_id"],
        "revision": 3, "state_change_seq": 1, "tab_id": WORKSPACE + ":t1",
        "terminal_id": "term_" + row["pane_id"].replace(":", ""),
        "terminal_title": row["name"], "terminal_title_stripped": row["name"],
        "workspace_id": WORKSPACE,
    }


class FakeHerdr:
    def __init__(self, path):
        self.path = str(path)
        self.rows = []
        self.log = []            # ("snapshot",) and ("subscribe", [subscription, ...]) in arrival order
        self.odd_agents = []     # raw entries added to the snapshot's agents[], as given
        self.stray = b""         # raw bytes sent ahead of every reply: frames that are not that reply
        self.ready_marks = 0     # snapshots that came after a subscribe: the recorder's sync is done
        self._since_subscribe = False
        self._lock = threading.Condition()
        self._listener = None
        self._acceptor = None
        self._streams = []       # [conn, send lock, pane ids, wants pane.created]

    # --- what the tests set up ------------------------------------------------------

    def add_pane(self, name, pane_id, status="idle", session=None):
        with self._lock:
            self.rows.append({"name": name, "pane_id": pane_id, "status": status, "session": session})
        return pane_id

    def set_status(self, pane_id, status):
        """Change what the next snapshot says, without an event (a change nobody was told about)."""
        with self._lock:
            self._row(pane_id)["status"] = status

    def emit_status(self, pane_id, status):
        self.set_status(pane_id, status)
        self.emit_event_for(pane_id, {"data": {"agent": "claude", "agent_status": status, "pane_id": pane_id,
                                                "workspace_id": WORKSPACE},
                                      "event": "pane.agent_status_changed"})

    def emit_created(self, pane_id):
        pane = {"pane_id": pane_id, "workspace_id": WORKSPACE, "agent": "claude"}
        self.send_raw(json.dumps({"data": {"pane": pane}, "event": "pane.created"}).encode() + b"\n",
                      only_created=True)

    def emit_event_for(self, pane_id, frame):
        data = json.dumps(frame).encode() + b"\n"
        for stream in self._snapshot_streams():
            if pane_id in stream[2]:
                self._send(stream, data)

    def send_raw(self, data, only_created=False):
        """Bytes straight to every subscribed connection: malformed frames, huge lines, no newline."""
        for stream in self._snapshot_streams():
            if not only_created or stream[3]:
                self._send(stream, data)

    # --- what the tests look at -----------------------------------------------------

    @property
    def snapshots(self):
        return sum(1 for entry in self.log if entry[0] == "snapshot")

    @property
    def subscribes(self):
        return [entry[1] for entry in self.log if entry[0] == "subscribe"]

    @property
    def open_streams(self):
        with self._lock:
            return len(self._streams)

    def wait_ready(self, count=1, timeout=READY_DEADLINE_S):
        """Block until the recorder has subscribed and then taken its sync snapshot `count` times in all."""
        deadline = time.monotonic() + timeout
        with self._lock:
            while self.ready_marks < count:
                left = deadline - time.monotonic()
                if left <= 0:
                    raise AssertionError("recorder not ready: log=%r" % (self.log,))
                self._lock.wait(left)

    # --- life cycle -----------------------------------------------------------------

    def start(self):
        if os.path.exists(self.path):
            os.unlink(self.path)
        listener = socket.socket(socket.AF_UNIX)
        listener.bind(self.path)
        listener.listen(8)
        self._listener = listener
        self._acceptor = threading.Thread(target=self._accept, args=(listener,), daemon=True)
        self._acceptor.start()

    def drop(self):
        """Cut every subscribed connection, as if herdr restarted; the socket keeps listening."""
        with self._lock:
            streams, self._streams = self._streams, []
        for stream in streams:
            self._close(stream[0])

    def stop(self):
        listener, self._listener = self._listener, None
        if listener is not None:
            # Wake the accepting thread and wait for it before closing: a thread that is only about to
            # call accept() on the closed descriptor could otherwise get a connection meant for the
            # next test's listener, which is given the same descriptor number.
            try:
                listener.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._acceptor.join(2)
            listener.close()
            if os.path.exists(self.path):
                os.unlink(self.path)
        self.drop()

    # --- internals ------------------------------------------------------------------

    def _row(self, pane_id):
        return next(r for r in self.rows if r["pane_id"] == pane_id)

    def _snapshot_streams(self):
        with self._lock:
            return list(self._streams)

    @staticmethod
    def _close(conn):
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()

    @staticmethod
    def _send(stream, data):
        try:
            with stream[1]:
                stream[0].sendall(data)
        except OSError:
            pass

    def _accept(self, listener):
        while True:
            try:
                conn, _ = listener.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn):
        buf = b""
        try:
            while True:
                while b"\n" not in buf:
                    chunk = conn.recv(65536)
                    if not chunk:
                        return
                    buf += chunk
                line, _, buf = buf.partition(b"\n")
                if self._answer(conn, line):
                    self._hold(conn)
                    return
        except OSError:
            return
        finally:
            conn.close()

    def _answer(self, conn, line):
        """Answer one request. True when the connection has become an event stream."""
        try:
            request = json.loads(line)
            method, req_id = request["method"], request["id"]
        except (ValueError, KeyError, TypeError):
            conn.sendall(self._error(None, "invalid request: not a request"))
            return False
        if method == "session.snapshot":
            with self._lock:
                self.log.append(("snapshot",))
                if self._since_subscribe:
                    self.ready_marks += 1
                    self._since_subscribe = False
                self._lock.notify_all()
                agents = [agent_entry(r) for r in self.rows] + self.odd_agents
            result = {"type": "session_snapshot", "snapshot": {"agents": agents, "protocol": 22, "version": "0.9.3"}}
            conn.sendall(self.stray + json.dumps({"id": req_id, "result": result}).encode() + b"\n")
            return False
        if method == "events.subscribe":
            subs = request.get("params", {}).get("subscriptions", [])
            panes, created = set(), False
            for sub in subs:
                if sub.get("type") == "pane.agent_status_changed":
                    if "pane_id" not in sub:
                        conn.sendall(self._error(req_id, "invalid request: missing field `pane_id`"))
                        return False
                    panes.add(sub["pane_id"])
                elif sub.get("type") == "pane.created":
                    created = True
            with self._lock:
                self.log.append(("subscribe", subs))
                self._since_subscribe = True
                stream = [conn, threading.Lock(), panes, created]
                self._streams.append(stream)
                self._lock.notify_all()
            self._send(stream, self.stray + json.dumps({"id": req_id, "result": {"type": "subscription_started"}}).encode() + b"\n")
            return True
        conn.sendall(self._error(req_id, "unknown method"))
        return False

    @staticmethod
    def _error(req_id, message):
        return json.dumps({"id": req_id, "error": {"code": "invalid_request", "message": message}}).encode() + b"\n"

    def _hold(self, conn):
        """Like herdr: a subscribed connection takes nothing more. Any byte from the client ends it."""
        try:
            data = conn.recv(65536)
        except OSError:
            data = b""
        with self._lock:
            self._streams = [s for s in self._streams if s[0] is not conn]
        if data:
            self._close(conn)
