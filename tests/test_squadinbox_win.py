"""T2a: squad-inbox on Windows: no fcntl, msvcrt lock, binary fds, no select on stdin, UTF-8 and LF."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from test_squadinbox import Base, CLI, ROOT, env, run

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "bin"))
import squadinbox  # noqa: E402

SITE = '''import fcntl, sys
sys.modules["_real_fcntl"] = fcntl
sys.modules["fcntl"] = None
'''
# A fake Windows lock backed by flock; every call is counted in $FAKE_MSVCRT_LOG.
MSVCRT = '''import os, sys
fcntl = sys.modules["_real_fcntl"]
LK_LOCK, LK_UNLCK = 2, 0
def locking(fd, mode, n):
    with open(os.environ["FAKE_MSVCRT_LOG"], "a") as f:
        f.write("%d\\n" % mode)
    if os.environ.get("FAKE_MSVCRT_FAIL"):
        raise OSError(36, "Resource deadlock avoided")
    fcntl.flock(fd, fcntl.LOCK_UN if mode == LK_UNLCK else fcntl.LOCK_EX)
'''
EMOJI = "→ 🦀 é < |"


@unittest.skipIf(sys.platform == "win32", "NoFcntl fakes Windows on top of a real fcntl, which real Windows does not have")
class NoFcntl(Base):
    def setUp(self):
        super().setUp()
        self.fake = Path(self.tmp) / "fake"
        self.fake.mkdir()
        (self.fake / "sitecustomize.py").write_text(SITE, encoding="utf-8")
        (self.fake / "msvcrt.py").write_text(MSVCRT, encoding="utf-8")
        self.log = Path(self.tmp) / "lock.log"
        self.log.write_text("", encoding="utf-8")

    def fenv(self, **extra):
        return env(PYTHONPATH=str(self.fake), FAKE_MSVCRT_LOG=str(self.log), **extra)

    def cli(self, home, *args, **extra):
        return subprocess.run([sys.executable, "-B", CLI, "--home", str(home)] + list(args), text=True,
                              capture_output=True, input="body", env=self.fenv(**extra), encoding="utf-8")

    def test_imports_and_lists_without_fcntl(self):  # AC1
        r = subprocess.run([sys.executable, "-B", "-c", "import sys; sys.modules['fcntl']=None; sys.path.insert(0, %r); import squadinbox; assert squadinbox.fcntl is None" % str(ROOT / "bin")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.cli(self.home, "list", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_eight_writers_through_the_windows_lock(self):  # AC2
        h = self.empty_home()
        procs = [subprocess.Popen([sys.executable, "-B", CLI, "--home", str(h), "add", "--kind", "read", "--title", "t%d" % i],
                                  stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=self.fenv(), encoding="utf-8") for i in range(8)]
        for p in procs:
            p.stdin.write("body")
            p.stdin.close()
        for p in procs:
            self.assertEqual(p.wait(30), 0, p.stderr.read())
        lines = (h / "inbox.jsonl").read_bytes().split(b"\n")
        self.assertEqual(lines[-1], b"")
        titles = sorted(json.loads(l)["title"] for l in lines[:-1] if json.loads(l)["ev"] == "add")
        self.assertEqual(titles, sorted("t%d" % i for i in range(8)))
        calls = self.log.read_text(encoding="utf-8").split()
        self.assertGreaterEqual(calls.count("2"), 8)
        self.assertGreaterEqual(calls.count("0"), 8)

    def test_lock_timeout_is_refused(self):  # AC2
        h = self.empty_home()
        r = self.cli(h, "add", "--kind", "read", "--title", "x", FAKE_MSVCRT_FAIL="1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("the inbox is locked by another squad-inbox", r.stderr)
        self.assertFalse((h / "inbox.jsonl").exists())


class Fds(unittest.TestCase):
    def test_o_binary_reaches_os_open(self):  # AC3
        seen = []
        real = os.open

        def spy(path, flags, *a):
            seen.append(flags)
            return real(path, flags & ~0x40000000, *a)

        with tempfile.TemporaryDirectory() as d, mock.patch.object(os, "O_BINARY", 0x40000000, create=True), \
                mock.patch.object(os, "open", spy):
            squadinbox.append_events(os.path.join(d, "inbox.jsonl"), [{"ev": "x"}])
            with squadinbox.locked(d):
                pass
        self.assertEqual(len(seen), 2)
        self.assertTrue(all(f & 0x40000000 for f in seen), seen)


class WindowsStdin(Base):
    def stdin(self, data):
        return mock.patch.object(sys, "stdin", io.TextIOWrapper(io.BytesIO(data)))

    def test_no_select_when_windows_and_ready_only(self):  # AC4
        with mock.patch.object(squadinbox, "IS_WINDOWS", True), self.stdin(b"hello"), \
                mock.patch.dict(sys.modules, {"select": None}):
            self.assertEqual(squadinbox.stdin_text(only_if_ready=True), "")
            self.assertEqual(squadinbox.stdin_text(only_if_ready=False), "hello")

    def answer(self, **kw):
        a = Namespace(**dict(dict(id="E8", option=None, note=None, text=None, source="pane"), **kw))
        with mock.patch.dict(os.environ, {"SQUAD_ROLE": "manager"}):
            return squadinbox.cmd_answer(str(self.home), a)

    def test_answer_text_on_stdin(self):  # AC4
        with mock.patch.object(squadinbox, "IS_WINDOWS", True), self.stdin(b"from the pane"):
            self.assertEqual(self.answer(), 0)
        ev = [json.loads(l) for l in (self.home / "inbox.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()][-1]
        self.assertEqual(ev["text"], "from the pane")

    def test_note_with_open_empty_pipe_does_not_hang(self):  # AC4
        r, w = os.pipe()
        self.addCleanup(os.close, w)
        with os.fdopen(r, "rb") as rf, mock.patch.object(squadinbox, "IS_WINDOWS", True), \
                mock.patch.object(sys, "stdin", io.TextIOWrapper(rf)):
            self.assertEqual(self.answer(note="x"), 0)


class Cp1252(Base):
    def cp(self, *args, stdin=b""):
        return subprocess.run([sys.executable, "-B", CLI, "--home", str(self.home)] + [a.encode("utf-8") for a in args], capture_output=True, input=stdin,
                              env=env(PYTHONUTF8="0", LC_ALL="C", PYTHONIOENCODING="cp1252"))

    def test_bytes_and_no_cr(self):  # AC5, AC6, B0, B4
        for args in (("list",), ("list", "--json"), ("list", "--open")):
            r = self.cp(*args)
            self.assertEqual((r.returncode, r.stderr), (0, b""), args)
        r = self.cp("add", "--kind", "read", "--title", EMOJI, stdin=b"body")
        self.assertEqual((r.returncode, r.stderr), (0, b""))
        r = self.cp("answer", "E8", "--note", EMOJI, "--source", "pane")
        self.assertEqual((r.returncode, r.stderr), (0, b""), r.stderr)
        log = (self.home / "inbox.jsonl").read_bytes()
        table = (self.home / "escalations.md").read_bytes()
        self.assertIn(("\"title\": \"%s\"" % EMOJI).encode("utf-8"), log.replace(b'"title":"', b'"title": "'))
        self.assertIn(EMOJI.encode("utf-8").replace(b"|", b"\\|"), table)
        self.assertNotIn(b"\r", log)
        self.assertNotIn(b"\r", table)
        out = self.cp("list", "--json").stdout
        self.assertIn(EMOJI.encode("utf-8"), out)
        self.assertNotIn(b"\r", out)


if __name__ == "__main__":
    unittest.main()
