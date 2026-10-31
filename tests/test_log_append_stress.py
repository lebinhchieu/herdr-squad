"""Ticket 06: concurrent hook appends keep every line of the log intact (ADR 0011).

Runs the real scripts: 8 parallel writers x 200 records into one log, for squad-log-message and
squad-usage-hook, once with short records and once with records over PIPE_BUF (4096 on Linux,
the size the code comment worries about). Linux locks with flock; Git Bash has none, so on Windows
this proves what plain O_APPEND gives.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"


def launch(script):
    """argv for a bin script: Windows cannot exec a shebang script, so name Git's bash (not System32's)."""
    if os.name != "nt":
        return [str(script)]
    root = shutil.which("git") or ""
    for _ in range(3):
        root = os.path.dirname(root)
        bash = os.path.join(root, "bin", "bash.exe")
        if os.path.exists(bash):
            return [bash, Path(script).as_posix()]
    raise RuntimeError("Git for Windows bash not found")


WRITERS = 8
RECORDS = 200
BIG = 9000  # > PIPE_BUF


LOST_MAX = WRITERS * RECORDS // 100  # launches Git Bash may lose (W11 fork failure); more means the log is lossy


def launched(argv, **kw):
    """Run a hook. A bash that hangs or dies before the script runs counts as lost, not as an error here."""
    try:
        return subprocess.run(argv, text=True, encoding="utf-8", capture_output=True, timeout=120, **kw)
    except subprocess.TimeoutExpired:
        return None


def run_all(fn):
    """fn(writer, i) for every writer in parallel, each writer sequential. Returns the failures."""
    def one(w):
        return [r for r in (fn(w, i) for i in range(RECORDS)) if r]
    with ThreadPoolExecutor(WRITERS) as ex:
        return [f for fails in ex.map(one, range(WRITERS)) for f in fails]


class StressBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / "squad"
        self.squad.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def env(self, **extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_DIR=str(self.squad), **extra)
        return env

    def read_log(self, log, key):
        lines = log.read_bytes().decode("utf-8").split("\n")
        self.assertEqual(lines.pop(), "", "log must end with a newline")
        return lines, [json.loads(l)[key] for l in lines]  # every line intact

    def stress(self, log, key, once):
        """Parallel pass, then re-run serially each id the log lacks (a launch bash lost), then check the log."""
        run_all(once)
        lines, ids = self.read_log(log, key)
        self.assertEqual(len(ids), len(set(ids)), "duplicate ids")
        want = [(w, i) for w in range(WRITERS) for i in range(RECORDS)]
        lost = [(w, i) for w, i in want if f"w{w}-{i}" not in set(ids)]
        print(f"\n{self.id()}: {len(ids)} intact lines after the parallel pass, {len(lost)} launches lost")
        self.assertLessEqual(len(lost), LOST_MAX)
        for w, i in lost:
            r = once(w, i)
            self.assertIsNone(r, r)
        lines, ids = self.read_log(log, key)
        self.assertEqual(sorted(ids), sorted(f"w{w}-{i}" for w, i in want))


class LogMessageStress(StressBase):
    def hook(self, w, i):
        pad = BIG if w == 0 else 0  # writer 0's records exceed PIPE_BUF
        msg = f"STATUS 06: writer {w} record {i} " + "x" * pad
        data = {"hook_event_name": "PostToolUse", "tool_name": "SendMessage", "session_id": "s",
                "tool_input": {"to": "tl", "message": msg},
                "tool_response": {"success": True, "msg_id": f"w{w}-{i}"}}
        r = launched(launch(BIN / "squad-log-message"), input=json.dumps(data), env=self.env(SQUAD_NAME=f"dev-{w}"))
        return None if r is None or r.returncode == 0 or "fatal error in forked" in r.stderr else (w, i, r.returncode, r.stderr)

    def test_eight_writers_keep_every_line(self):
        self.stress(self.squad / "messages.jsonl", "msg_id", self.hook)


class UsageHookStress(StressBase):
    def setUp(self):
        super().setUp()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.transcript = self.root / "t.jsonl"
        self.transcript.write_text(json.dumps({
            "type": "assistant", "timestamp": now, "effort": "medium",
            "message": {"id": "m", "model": "claude-sonnet-5-5",
                        "usage": {"input_tokens": 2, "cache_read_input_tokens": 130_000,
                                  "cache_creation_input_tokens": 0, "output_tokens": 10}}}) + "\n", encoding="utf-8")

    def hook(self, w, i):
        pad = BIG if w == 0 else 0  # writer 0's records exceed PIPE_BUF
        data = {"hook_event_name": "Stop", "session_id": f"w{w}-{i}", "transcript_path": str(self.transcript)}
        r = launched(launch(BIN / "squad-usage-hook"), input=json.dumps(data),
                     env=self.env(SQUAD_NAME=f"dev-{w}", SQUAD_ROLE="qa" + "x" * pad,
                                  CLAUDE_CONFIG_DIR=str(self.root / "cfg")))
        return None if r is None or r.returncode == 2 or "fatal error in forked" in r.stderr else (w, i, r.returncode, r.stderr)

    def test_eight_writers_keep_every_line(self):
        self.stress(self.squad / "usage-events.jsonl", "session", self.hook)


def no_flock_env(env, tmp):
    """env whose PATH has no flock, so the hooks take their mkdir-lock branch (Windows has none; Linux gets a symlink farm)."""
    if not shutil.which("flock", path=env.get("PATH")):
        return env
    farm = Path(tmp) / "noflock-bin"
    farm.mkdir(exist_ok=True)
    for tool in ("bash", "jq", "date", "dirname", "readlink", "cat", "basename", "python3", "sleep", "mkdir",
                 "rmdir", "env", "uname", "sed", "grep", "tr", "head", "sort", "wc", "id"):
        found = shutil.which(tool)
        if found and not (farm / tool).exists():
            (farm / tool).symlink_to(found)
    return {**env, "PATH": str(farm)}


class StaleLock(StressBase):
    """A lock dir left by a killed writer must not wedge the hook: it goes on, exits as usual, and clears it."""
    def check(self, log, argv, env, stdin, want_rc, stdin2=None):
        lock = Path(str(log) + ".lock")
        lock.mkdir()
        r = launched(argv, input=stdin, env=no_flock_env(env, self.root))
        self.assertEqual(r.returncode, want_rc, r.stderr)
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)
        self.assertFalse(lock.exists())
        r = launched(argv, input=stdin2 or stdin, env=no_flock_env(env, self.root))  # the next call is not delayed by a stale lock
        self.assertEqual(r.returncode, want_rc, r.stderr)
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 2)
        self.assertFalse(lock.exists())

    def test_log_message(self):
        data = {"hook_event_name": "PostToolUse", "tool_name": "SendMessage", "session_id": "s",
                "tool_input": {"to": "tl", "message": "STATUS 06: x"}, "tool_response": {"success": True, "msg_id": "m"}}
        self.check(self.squad / "messages.jsonl", launch(BIN / "squad-log-message"), self.env(SQUAD_NAME="dev-1"),
                   json.dumps(data), 0)

    def test_usage_hook(self):
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        tr = self.root / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "timestamp": now, "effort": "medium",
                                  "message": {"id": "m", "model": "claude-sonnet-5-5",
                                              "usage": {"input_tokens": 2, "cache_read_input_tokens": 130_000,
                                                        "cache_creation_input_tokens": 0, "output_tokens": 10}}}) + "\n",
                      encoding="utf-8")
        self.check(self.squad / "usage-events.jsonl", launch(BIN / "squad-usage-hook"),
                   self.env(SQUAD_NAME="dev-1", SQUAD_ROLE="qa", CLAUDE_CONFIG_DIR=str(self.root / "cfg")),
                   json.dumps({"hook_event_name": "Stop", "session_id": "s1", "transcript_path": str(tr)}), 2,
                   json.dumps({"hook_event_name": "Stop", "session_id": "s2", "transcript_path": str(tr)}))


if __name__ == "__main__":
    unittest.main()
