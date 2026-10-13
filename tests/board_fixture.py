"""Shared helper for the squad-board Seam A tests.

Builds a squad folder in a temp dir, runs the real `bin/squad-board --replay` on it
and talks to it over HTTP. Tests never import the server's internals.
"""
import http.client
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

BIN = Path(__file__).resolve().parent.parent / "bin" / "squad-board"
STARTUP_DEADLINE_S = 10


def _cells(row, keys):
    return " | ".join(str(row[k]) for k in keys)


class Server:
    """A running `squad-board --replay` process."""

    def __init__(self, proc, stderr_file, line):
        self.proc = proc
        self._stderr_file = stderr_file
        self.startup_line = line
        # keep reading stdout so a chatty server can never block on a full pipe
        self._drain = threading.Thread(
            target=lambda: [None for _ in iter(lambda: proc.stdout.read(4096), b"")], daemon=True)
        self._drain.start()
        url = urlsplit(line.split(": ", 1)[1].strip())
        self.port = url.port
        self.base = "http://127.0.0.1:%d" % self.port
        # None until the server prints ?token=... (BRD-05)
        self.token = dict(p.split("=", 1) for p in url.query.split("&") if "=" in p).get("token")

    def get(self, path, headers=None):
        return self._request("GET", path, headers)

    def post(self, path, headers=None):
        return self._request("POST", path, headers)

    def _request(self, method, path, headers):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(method, path, headers=headers or {})
            resp = conn.getresponse()
            body = resp.read()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, body
        finally:
            conn.close()

    def state(self, iteration=None):
        path = "/state" if iteration is None else "/state?iteration=%s" % iteration
        status, _, body = self.get(path)
        if status != 200:
            raise AssertionError("GET %s -> %s: %r" % (path, status, body[:300]))
        return json.loads(body)

    def stderr(self):
        # pread leaves the shared file offset alone: a seek here would make the child overwrite earlier lines
        fd = self._stderr_file.fileno()
        chunks, offset = [], 0
        while True:
            chunk = os.pread(fd, 65536, offset)
            if not chunk:
                return b"".join(chunks).decode("utf-8", "replace")
            chunks.append(chunk)
            offset += len(chunk)

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self._drain.join(5)
        self.proc.stdout.close()

    def close(self):
        self.stop()
        self._stderr_file.close()


class Fixture:
    """A squad folder in a temp dir. Call close() (or addCleanup(fx.close))."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="board-fx-"))
        self._servers = []
        self._seq = 0

    def close(self):
        for server in self._servers:
            server.close()
        self._servers = []
        shutil.rmtree(self.root, ignore_errors=True)

    # --- raw writers -------------------------------------------------------

    def write(self, relpath, text):
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def append_jsonl(self, relpath, obj):
        """Append one line. A str is written verbatim (to plant bad lines)."""
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        line = obj if isinstance(obj, str) else json.dumps(obj)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _next_ts(self):
        """Strictly increasing default timestamps, 1 s apart, so order is explicit."""
        self._seq += 1
        secs = self._seq
        return "2026-10-12T10:%02d:%02d.000Z" % (secs // 60, secs % 60)

    # --- squad markdown ----------------------------------------------------

    def roster(self, rows):
        """rows: dicts with agent, role, scope, owns, status. Cells are written as given."""
        keys = ("agent", "role", "scope", "owns", "status")
        out = ["# Roster", "", "| Agent | Role | Scope | Owns | Status |", "|---|---|---|---|---|"]
        for row in rows:
            r = {"role": "Developer", "scope": "board", "owns": "x", "status": "live"}
            r.update(row)
            out.append("| " + _cells(r, keys) + " |")
        self.write("roster.md", "\n".join(out) + "\n")

    def scopes(self, rows, size_log=None):
        """rows: dicts with scope, size, signals, risk, confirmed, pod.
        size_log: raw table rows for the second (size-change) table."""
        keys = ("scope", "size", "signals", "risk", "confirmed", "pod")
        out = ["# Scopes", "",
               "| Scope | Size | Signals | Risk flags | PO confirmed | Pod (agents) |",
               "|---|---|---|---|---|---|"]
        for row in rows:
            r = {"size": "S", "signals": "x", "risk": "none", "confirmed": "2026-10-12", "pod": "x"}
            r.update(row)
            out.append("| " + _cells(r, keys) + " |")
        out += ["", "## Size changes", "",
                "| Date | Scope | From → To | Why | Reported to PO |", "|---|---|---|---|---|"]
        out += size_log or []
        self.write("scopes.md", "\n".join(out) + "\n")

    def escalations(self, rows):
        keys = ("num", "date", "question", "options", "rec", "blocks", "answer")
        out = ["# Escalations", "",
               "| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |",
               "|---|---|---|---|---|---|---|"]
        for i, row in enumerate(rows, 1):
            r = {"num": i, "date": "2026-10-12", "question": "q?", "options": "A) x",
                 "rec": "A", "blocks": "nothing", "answer": ""}
            r.update(row)
            out.append("| " + _cells(r, keys) + " |")
        self.write("escalations.md", "\n".join(out) + "\n")

    def iteration(self, n, text=None):
        if text is None:
            text = ("# Iteration %s\n\n## PO check-in\n- **Done (with evidence):**\n- **Next:**\n"
                    "- **Decisions from the PO:**\n" % n)
        self.write("iterations/%s.md" % n, text)

    # --- logs ----------------------------------------------------------------

    def message(self, **fields):
        rec = {"ts": self._next_ts(), "msg_id": "m-%d" % (self._seq), "from": "manager",
               "to": "tech-board", "type": None, "task": None, "text": "hello", "iteration": 1}
        rec.update(fields)
        self.append_jsonl("messages.jsonl", rec)
        return rec

    def activity(self, **fields):
        rec = {"ts": self._next_ts(), "agent": "manager", "status": "working", "iteration": 1}
        rec.update(fields)
        self.append_jsonl("activity.jsonl", rec)
        return rec

    # --- replay-only inputs --------------------------------------------------

    def herdr(self, agents):
        """agents: {name: session_id} or {name: {"session_id": id}}."""
        norm = {n: (v if isinstance(v, dict) else {"session_id": v}) for n, v in agents.items()}
        self.write("replay/herdr.json", json.dumps({"agents": norm}))

    def transcript(self, root, project, session_id, lines):
        """root: a `claude*` folder name under replay/. lines: dicts or raw strings."""
        text = "".join((ln if isinstance(ln, str) else json.dumps(ln)) + "\n" for ln in lines)
        self.write("replay/%s/projects/%s/%s.jsonl" % (root, project, session_id), text)

    # --- run -------------------------------------------------------------------

    def start(self, now=None, port=0, env=None):
        cmd = [sys.executable, str(BIN), "--replay", str(self.root), "--port", str(port)]
        if now is not None:
            cmd += ["--now", now]
        full_env = dict(os.environ)
        full_env.update(env or {})
        stderr_file = tempfile.TemporaryFile()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr_file, env=full_env,
                                bufsize=0)
        try:
            line = self._read_startup_line(proc, stderr_file)
        except BaseException:
            proc.kill()
            proc.wait()
            raise
        server = Server(proc, stderr_file, line)
        self._servers.append(server)
        return server

    @staticmethod
    def _read_startup_line(proc, stderr_file):
        deadline = time.monotonic() + STARTUP_DEADLINE_S
        buf = b""
        while b"\n" not in buf:
            left = deadline - time.monotonic()
            ready = select.select([proc.stdout], [], [], max(left, 0))[0] if left > 0 else []
            chunk = os.read(proc.stdout.fileno(), 4096) if ready else b""
            if not chunk:
                stderr_file.seek(0)
                raise AssertionError("no startup line (exit=%s): stdout=%r stderr=%r" % (
                    proc.poll(), buf, stderr_file.read().decode("utf-8", "replace")))
            buf += chunk
        return buf.split(b"\n", 1)[0].decode("utf-8")
