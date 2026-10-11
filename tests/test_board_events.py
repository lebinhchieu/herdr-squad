"""BRD-06: GET /events (server-sent events) and the handler socket timeout (N3). Seam A only.

Every wait is a read with a deadline. The default timings (POLL_S 0.5, 3 s of quiet) are used
wherever the AC states a number; the env overrides are used only to make a long wait short.
"""
import json
import os
import select
import signal
import socket
import sys
import time
import unittest

from board_fixture import Fixture

CHANGE_DEADLINE_S = 5  # AC2
QUIET_S = 3  # AC3
FAST = {"SQUAD_BOARD_POLL_S": "0.05", "SQUAD_BOARD_KEEPALIVE_S": "0.2"}


def has_agent(name):
    """Predicate: a column for `name` exists. A message to an agent that is not on the roster adds
    one, which is how a new message shows in the state before the timeline (rows) is built."""
    return lambda state: any(c["agent"] == name for c in state["columns"])


def say(fx, to):
    fx.message(**{"from": "tech-board", "to": to})


def thread_count(server):
    try:
        return len(os.listdir("/proc/%d/task" % server.proc.pid))
    except OSError:
        raise unittest.SkipTest("needs /proc to count the server's threads")


class Stream:
    """A raw client of GET /events. Parses the status line, headers and SSE blocks."""

    def __init__(self, server, path="/events", rcvbuf=None):
        self.sock = socket.socket()
        if rcvbuf:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
        self.sock.settimeout(10)
        self.sock.connect(("127.0.0.1", server.port))
        self.sock.sendall(("GET %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n\r\n" % (path, server.port)).encode())
        self.buf = b""
        self.eof = False
        head = self._take(b"\r\n\r\n", 5)
        lines = head.decode("latin-1").split("\r\n")
        self.status = int(lines[0].split()[1])
        self.headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                self.headers[k.strip().lower()] = v.strip()

    def close(self):
        self.sock.close()

    def _take(self, sep, timeout):
        """Bytes up to and excluding `sep`, or None when the deadline passes first."""
        deadline = time.monotonic() + timeout
        while sep not in self.buf:
            left = deadline - time.monotonic()
            if left <= 0 or self.eof:
                return None
            if select.select([self.sock], [], [], left)[0]:
                chunk = self.sock.recv(65536)
                if not chunk:
                    self.eof = True
                self.buf += chunk
        head, _, self.buf = self.buf.partition(sep)
        return head

    def block(self, timeout):
        """The next SSE block as text, or None."""
        raw = self._take(b"\n\n", timeout)
        return None if raw is None else raw.decode("utf-8")

    def state(self, timeout):
        """The next `state` event's parsed data, skipping comments; None when the deadline passes."""
        deadline = time.monotonic() + timeout
        while True:
            block = self.block(max(deadline - time.monotonic(), 0))
            if block is None:
                return None
            if block.startswith("event: state\ndata: "):
                return json.loads(block.split("data: ", 1)[1])

    def state_where(self, predicate, timeout=CHANGE_DEADLINE_S):
        """The first state event satisfying `predicate`, or None at the deadline."""
        deadline = time.monotonic() + timeout
        while True:
            state = self.state(max(deadline - time.monotonic(), 0))
            if state is None or predicate(state):
                return state


class EventsBase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"},
                        {"agent": "tech-board", "role": "Tech Lead"},
                        {"agent": "dev-board-7", "role": "Developer"}])
        self.fx.scopes([{"scope": "board", "size": "S"}])
        self.fx.iteration(1)
        self.fx.message(**{"from": "manager", "to": "tech-board", "type": "ASK", "task": "BRD-06"})
        self.fx.activity(agent="manager", status="working")

    def start(self, **kw):
        kw.setdefault("now", "2026-10-12T12:00:00Z")
        server = self.fx.start(**kw)
        return server

    def stream(self, server, path="/events", **kw):
        s = Stream(server, path, **kw)
        self.addCleanup(s.close)
        self.assertEqual(s.status, 200, s.headers)
        return s

    def wait_for_threads(self, server, baseline, timeout=10):
        deadline = time.monotonic() + timeout
        while thread_count(server) > baseline:
            self.assertLess(time.monotonic(), deadline,
                            "threads %d > baseline %d" % (thread_count(server), baseline))
            time.sleep(0.05)

    def assert_event_after(self, server, change, predicate):
        s = self.stream(server)
        self.assertIsNotNone(s.state(5), "no first event")
        change()
        self.assertIsNotNone(s.state_where(predicate), "no event reflecting the change within 5 s")


class ConnectTest(EventsBase):
    def test_first_event_is_the_state_as_one_sse_frame(self):
        server = self.start()
        s = self.stream(server)
        # Q4: exact framing and headers
        self.assertEqual(s.headers["content-type"], "text/event-stream; charset=utf-8")
        self.assertEqual(s.headers["cache-control"], "no-store")
        self.assertNotIn("content-length", s.headers)
        block = s.block(5)
        lines = block.split("\n")
        self.assertEqual(len(lines), 2, block[:200])
        self.assertEqual(lines[0], "event: state")
        self.assertTrue(lines[1].startswith("data: "))
        self.assertEqual(json.loads(lines[1][len("data: "):]), server.state())

    def test_token_is_not_in_the_stream(self):
        server = self.start()
        s = self.stream(server)
        block = s.block(5)
        self.assertNotIn(server.token, block)
        self.assertNotIn(server.token, str(s.headers))

    def test_text_with_newlines_stays_on_one_data_line(self):
        self.fx.message(text="line1\nline2\r\nline3 end", **{"from": "tech-board", "to": "manager"})
        server = self.start()
        s = self.stream(server)
        block = s.block(5)
        self.assertEqual(len(block.split("\n")), 2)
        self.assertEqual(json.loads(block.split("data: ", 1)[1]), server.state())

    def test_connect_gets_the_current_state_not_the_last_polled_one(self):
        # the watcher polls every 30 s here: a change made a moment ago must still be in the first event
        server = self.start(env={"SQUAD_BOARD_POLL_S": "30"})
        self.stream(server).close()
        say(self.fx, "ghost-one")
        self.assertTrue(has_agent("ghost-one")(self.stream(server).state(5)))

    def test_iteration_query_is_honoured(self):
        self.fx.iteration(2)
        self.fx.activity(agent="only-in-two", iteration=2)
        server = self.start()
        s = self.stream(server, "/events?iteration=1")
        first = s.state(5)
        self.assertEqual(first["selected_iteration"], 1)
        self.assertEqual(first, server.state(1))
        self.assertNotEqual(first, server.state(2))

    def test_bad_iteration_is_400_before_any_stream(self):
        server = self.start()
        for query in ("iteration=abc", "iteration=", "iteration=99", "iteration=1&iteration=1", "iteration=-1"):
            with self.subTest(query):
                status, headers, body = server.get("/events?" + query)
                self.assertEqual(status, 400)
                self.assertTrue(headers["content-type"].startswith("application/json"))
                self.assertIn("error", json.loads(body))


class ChangeTest(EventsBase):
    def test_message_appended(self):
        server = self.start()
        self.assert_event_after(server, lambda: say(self.fx, "ghost-one"), has_agent("ghost-one"))

    def test_activity_appended(self):
        server = self.start()
        self.assert_event_after(
            server, lambda: self.fx.activity(agent="tech-board", status="blocked"),
            lambda st: any(c["agent"] == "tech-board" and c["status"] == "blocked" for c in st["columns"]))

    def test_roster_edited(self):
        server = self.start()
        self.assert_event_after(
            server, lambda: self.fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"},
                                            {"agent": "newcomer", "role": "Developer"}]),
            lambda st: any(c["agent"] == "newcomer" for c in st["columns"]))

    def test_scopes_edited(self):
        server = self.start()
        self.assert_event_after(
            server, lambda: self.fx.scopes([{"scope": "board", "size": "M"}]),
            lambda st: any(p["name"] == "board" and p["size"] == "M" for p in st["pods"]))

    def test_iteration_file_added(self):
        server = self.start()
        self.assert_event_after(server, lambda: self.fx.iteration(2), lambda st: st["iterations"] == [1, 2])

    def test_notes_file_added(self):
        server = self.start()
        self.assert_event_after(
            server, lambda: self.fx.write("roles/tech-board.notes.md", "memory\n"),
            lambda st: any(c["agent"] == "tech-board" and c["notes_path"] for c in st["columns"]))

    def test_atomic_replace_with_same_size_and_mtime(self):
        # an editor that writes a temp file and renames it: only the inode differs
        server = self.start()
        target = self.fx.root / "roster.md"
        old = target.stat()
        text = target.read_text().replace("dev-board-7", "dev-board-8")
        self.assertEqual(len(text), len(target.read_text()))

        def replace():
            tmp = self.fx.root / "roster.md.tmp"
            tmp.write_text(text)
            os.utime(tmp, ns=(old.st_atime_ns, old.st_mtime_ns))
            os.replace(tmp, target)
        self.assert_event_after(server, replace, lambda st: any(c["agent"] == "dev-board-8" for c in st["columns"]))

    def test_log_that_appears_later_and_disappears(self):
        log = self.fx.root / "messages.jsonl"
        log.unlink()
        server = self.start()
        s = self.stream(server)
        self.assertFalse(has_agent("ghost-one")(s.state(5)))
        say(self.fx, "ghost-one")
        self.assertIsNotNone(s.state_where(has_agent("ghost-one")), "created log not noticed")
        log.unlink()
        self.assertIsNotNone(s.state_where(lambda st: not has_agent("ghost-one")(st)), "deleted log not noticed")
        self.fx.activity(agent="tech-board", status="working")
        self.assertIsNotNone(s.state_where(lambda st: any(
            c["agent"] == "tech-board" and c["status"] == "working" for c in st["columns"])), "stream died")
        self.assertEqual(server.stderr(), "")

    def test_event_reflects_the_change_for_every_client(self):
        server = self.start()
        streams = [self.stream(server) for _ in range(3)]
        for s in streams:
            self.assertIsNotNone(s.state(5))
        say(self.fx, "ghost-all")
        for s in streams:
            self.assertIsNotNone(s.state_where(has_agent("ghost-all")))


class QuietTest(EventsBase):
    def test_untouched_files_send_no_second_event(self):
        server = self.start()
        s = self.stream(server)
        self.assertIsNotNone(s.state(5))
        self.assertIsNone(s.state(QUIET_S), "an event arrived although nothing changed")

    def test_touch_without_a_change_and_a_moving_clock_sends_nothing(self):
        # No --now and no logs: `now` is the wall clock and differs on every rebuild. Touching a
        # file makes the watcher rebuild the state; only `now` differs, so nothing is sent.
        (self.fx.root / "messages.jsonl").unlink()
        (self.fx.root / "activity.jsonl").unlink()
        server = self.start(now=None)
        s = self.stream(server)
        first = s.state(5)
        self.assertIsNotNone(first)
        self.assertIsNone(s.state(1.2), "clock tick alone sent an event")
        target = self.fx.root / "escalations.md"
        target.write_text("# Escalations\n")
        os.utime(target, ns=(1, 1))
        os.utime(target, None)
        self.assertIsNone(s.state(QUIET_S), "an event arrived although only `now` differed")
        self.fx.activity(agent="tech-board", status="working")
        later = s.state_where(lambda st: st["now"] != first["now"])
        self.assertIsNotNone(later, "the stream is not alive after the touch")


class KeepaliveTest(EventsBase):
    def test_keepalive_comment_arrives_and_no_state_event_with_it(self):
        server = self.start(env=FAST)
        s = self.stream(server)
        self.assertIsNotNone(s.state(5))
        deadline = time.monotonic() + 5
        seen = []
        while time.monotonic() < deadline and ": keepalive" not in seen:
            block = s.block(max(deadline - time.monotonic(), 0))
            self.assertIsNotNone(block, "stream closed or silent: %r" % seen)
            seen.append(block)
        self.assertEqual(seen[-1], ": keepalive")
        self.assertEqual(set(seen), {": keepalive"})

    def test_default_interval_is_15_seconds(self):
        server = self.start()
        s = self.stream(server)
        self.assertIsNotNone(s.state(5))
        began = time.monotonic()
        block = s.block(20)
        elapsed = time.monotonic() - began
        self.assertEqual(block, ": keepalive")
        self.assertTrue(14 <= elapsed <= 17, elapsed)


class IterationTest(EventsBase):
    def test_explicit_iteration_stays_fixed_for_the_connection(self):
        self.fx.iteration(2)
        server = self.start()
        s = self.stream(server, "/events?iteration=1")
        self.assertEqual(s.state(5)["selected_iteration"], 1)
        self.fx.iteration(3)
        event = s.state_where(lambda st: st["iterations"] == [1, 2, 3])
        self.assertIsNotNone(event)
        self.assertEqual(event["selected_iteration"], 1)
        self.fx.activity(agent="ghost-one", iteration=1)
        event = s.state_where(has_agent("ghost-one"))
        self.assertIsNotNone(event)
        self.assertEqual(event["selected_iteration"], 1)

    def test_pinned_iteration_that_disappears_is_logged_and_the_stream_survives(self):
        self.fx.iteration(2)
        server = self.start()
        s = self.stream(server, "/events?iteration=2")
        self.assertIsNotNone(s.state(5))
        (self.fx.root / "iterations" / "2.md").unlink()
        deadline = time.monotonic() + CHANGE_DEADLINE_S
        while "state not rebuilt" not in server.stderr():
            self.assertLess(time.monotonic(), deadline, "the failed rebuild was not logged")
            time.sleep(0.05)
        self.assertFalse(s.eof)
        self.fx.iteration(2)
        say(self.fx, "ghost-one")
        event = s.state_where(has_agent("ghost-one"))
        self.assertIsNotNone(event, "stream stopped after the failed rebuild")
        self.assertEqual(event["selected_iteration"], 2)

    def test_stream_without_a_query_follows_the_current_iteration(self):
        server = self.start()
        s = self.stream(server)
        self.assertEqual(s.state(5)["selected_iteration"], 1)
        self.fx.iteration(2)
        event = s.state_where(lambda st: st["iterations"] == [1, 2])
        self.assertEqual(event["selected_iteration"], 2)


class ConnectionTest(EventsBase):
    def test_disconnect_frees_the_thread_and_leaves_stderr_empty(self):
        server = self.start(env=FAST)
        time.sleep(0.3)  # let the server settle before counting its threads
        baseline = thread_count(server)
        s = self.stream(server)
        self.assertIsNotNone(s.state(5))
        self.assertGreater(thread_count(server), baseline)
        s.close()
        self.wait_for_threads(server, baseline)
        self.assertEqual(server.state()["selected_iteration"], 1)
        self.assertEqual(server.stderr(), "")

    def test_twenty_connect_disconnect_cycles_do_not_leak_threads(self):
        server = self.start(env=FAST)
        time.sleep(0.3)
        baseline = thread_count(server)
        for _ in range(20):
            s = Stream(server)
            self.assertIsNotNone(s.state(5))
            s.close()
        self.wait_for_threads(server, baseline)
        self.assertEqual(server.stderr(), "")

    def test_sigterm_with_open_streams(self):
        server = self.start()
        streams = [self.stream(server) for _ in range(3)]
        server.proc.send_signal(signal.SIGTERM)
        self.assertIn(server.proc.wait(2), (0, -signal.SIGTERM))
        self.assertTrue(streams)

    def test_sigint_with_open_streams_exits_zero(self):
        server = self.start()
        streams = [self.stream(server) for _ in range(3)]
        server.proc.send_signal(signal.SIGINT)
        self.assertEqual(server.proc.wait(2), 0)
        self.assertEqual(server.stderr(), "")
        self.assertTrue(streams)

    def test_slow_client_does_not_hold_back_the_others(self):
        # A client that never reads, with a tiny receive window. The state is big (an agent with a
        # 300 KB name), so its send buffer fills. A healthy client must still get every event, and
        # the stuck write must time out so that thread is freed while the connection stays open.
        self.fx.activity(agent="g" * 300_000, status="idle")
        server = self.start(env=dict(FAST, SQUAD_BOARD_REQUEST_TIMEOUT_S="1"))
        time.sleep(0.3)
        baseline = thread_count(server)
        slow = Stream(server, rcvbuf=2048)
        self.addCleanup(slow.close)
        healthy = self.stream(server)
        self.assertIsNotNone(healthy.state(5))
        for i in range(30):
            wanted = "working" if i % 2 == 0 else "idle"
            self.fx.activity(agent="tech-board", status=wanted)
            self.assertIsNotNone(
                healthy.state_where(lambda st: any(
                    c["agent"] == "tech-board" and c["status"] == wanted for c in st["columns"])),
                "event %d never reached the healthy client" % i)
        healthy.close()
        self.wait_for_threads(server, baseline)
        self.assertEqual(server.stderr(), "")


class SocketTimeoutTest(EventsBase):
    """N3: the handler reads the request line with a timeout (SQUAD_BOARD_REQUEST_TIMEOUT_S)."""

    def test_silent_and_half_sent_requests_are_dropped(self):
        server = self.start(env={"SQUAD_BOARD_REQUEST_TIMEOUT_S": "0.5"})
        time.sleep(0.3)
        baseline = thread_count(server)
        for sent in (b"", b"GET /sta"):
            with self.subTest(sent=sent):
                sock = socket.create_connection(("127.0.0.1", server.port))
                self.addCleanup(sock.close)
                sock.sendall(sent)
                began = time.monotonic()
                self.assertTrue(select.select([sock], [], [], 5)[0], "connection still held open")
                self.assertEqual(sock.recv(100), b"")
                self.assertLess(time.monotonic() - began, 4)
        deadline = time.monotonic() + 5
        while thread_count(server) > baseline:
            self.assertLess(time.monotonic(), deadline, "handler threads not freed")
            time.sleep(0.05)
        self.assertEqual(server.state()["selected_iteration"], 1)
        self.assertEqual(server.stderr(), "")

    def test_timeout_does_not_cut_a_quiet_stream(self):
        # an SSE connection only writes: 3x the read timeout with no event and no keepalive must
        # leave it open and able to deliver the next change
        server = self.start(env={"SQUAD_BOARD_REQUEST_TIMEOUT_S": "0.5", "SQUAD_BOARD_KEEPALIVE_S": "60"})
        s = self.stream(server)
        self.assertIsNotNone(s.state(5))
        self.assertIsNone(s.block(1.6))
        self.assertFalse(s.eof, "server closed the quiet stream")
        say(self.fx, "ghost-one")
        self.assertIsNotNone(s.state_where(has_agent("ghost-one")))


if __name__ == "__main__":
    unittest.main()
