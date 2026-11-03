"""Ticket 06: squad-inbox park / unpark / resolve write open-questions.md and nothing else."""
import hashlib
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from test_squadinbox import ROOT, run, run_proc

sys.path.insert(0, str(ROOT / "bin"))
import squadinbox  # noqa: E402

NOW = {"SQUAD_INBOX_NOW": "2026-11-04T10:00:00Z"}
GOLDEN = (
    "## Q1\nStatus: parked\nParked: 2026-11-04T10:00:00Z\nIs the API versioned?\nBlocks: ticket 7\nFrom: E3 #2\n\n"
    "## Q2\nStatus: resolved\nParked: 2026-11-04T10:00:00Z\nWhich port?\n"
    "Resolved: 2026-11-04T10:00:00Z 8080\n"
)


class ParkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.f = self.home / "open-questions.md"
        (self.home / "escalations.md").write_text("| # | date | question |\n|---|---|---|\n| 1 | 2026-11-01 | q? |\n", encoding="utf-8")
        (self.home / "inbox.jsonl").write_text("", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def r(self, *a, **kw):
        return run(self.home, *a, **{**NOW, **kw})

    def sums(self):
        return [hashlib.sha256((self.home / n).read_bytes()).hexdigest() for n in ("escalations.md", "inbox.jsonl")]

    def test_golden_and_inbox_untouched(self):  # AC1, AC3, TA1, TA2
        before = self.sums()
        for a in (["park", "--text", "Is the API versioned?", "--blocks", "ticket 7", "--from", "E3 #2"],
                  ["park", "--text", "Which port?"], ["resolve", "Q2", "--answer", "8080"]):
            self.assertEqual(self.r(*a, SCOPE_DIR=str(self.home)).returncode, 0)
        self.assertEqual(self.f.read_text(encoding="utf-8"), GOLDEN)
        self.assertEqual(self.sums(), before)

    def test_unpark_then_count(self):  # AC2
        self.r("park", "--text", "a", SCOPE_DIR=str(self.home))
        self.r("park", "--text", "b", SCOPE_DIR=str(self.home))
        self.assertEqual(self.r("unpark", "Q1", SCOPE_DIR=str(self.home)).returncode, 0)
        entries, w = squadinbox.parse_open_questions(self.f.read_text(encoding="utf-8"))
        self.assertEqual([e["status"] for e in entries], ["unparked", "parked"])
        self.assertEqual(w, [])

    def test_broken_block_skipped_and_kept(self):  # AC5, TA4
        broken = "## Q2\nStatus: banana\nlost words\n"
        text = "## Q1\nstatus: PARKED  \nParked: 2026-11-04T09:00:00Z\nline one\nline two\n\n" + broken + "\n## Q3\nStatus: parked\nx\n"
        self.f.write_text(text, encoding="utf-8")
        entries, w = squadinbox.parse_open_questions(text, "P/open-questions.md")
        self.assertEqual([e["n"] for e in entries], [1, 3])
        self.assertEqual(entries[0]["text"], "line one\nline two")
        self.assertEqual(len(w), 1)
        self.assertTrue(w[0].startswith("open-questions.md unreadable: P/open-questions.md"))
        self.r("park", "--text", "new", SCOPE_DIR=str(self.home))
        out = self.f.read_text(encoding="utf-8")
        self.assertIn(broken, out)
        self.assertIn("## Q4\n", out)  # max+1, gaps never reused

    def test_crlf_file_keeps_blocks(self):  # TA3
        self.f.write_bytes(GOLDEN.replace("\n", "\r\n").encode())
        self.assertEqual(self.r("unpark", "Q1", SCOPE_DIR=str(self.home)).returncode, 0)
        data = self.f.read_bytes()
        self.assertNotIn(b"\r", data)
        entries, _ = squadinbox.parse_open_questions(data.decode())
        self.assertEqual([e["status"] for e in entries], ["unparked", "resolved"])

    def test_parallel_park(self):  # TA3
        out = []
        ts = [threading.Thread(target=lambda i=i: out.append(run_proc(self.home, "park", "--text", "q%d" % i, SCOPE_DIR=str(self.home)).returncode)) for i in range(4)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(out, [0] * 4)
        entries, w = squadinbox.parse_open_questions(self.f.read_text(encoding="utf-8"))
        self.assertEqual(sorted(e["n"] for e in entries), [1, 2, 3, 4])
        self.assertEqual(w, [])

    def test_errors_leave_file_unchanged(self):  # TA5
        env = dict(SCOPE_DIR=str(self.home))
        self.assertNotEqual(self.r("unpark", "Q1", **env).returncode, 0)  # file missing
        self.r("park", "--text", "a", **env)
        before = self.f.read_bytes()
        for a, kw in ((["unpark", "Q9"], env), (["park", "--text", "  "], env), (["park", "--text", "x", "--from", "bogus"], env)):
            r = self.r(*a, **kw)
            self.assertNotEqual(r.returncode, 0, a)
            self.assertEqual(len(r.stderr.strip().splitlines()), 1, a)
        import os, subprocess
        from test_squadinbox import CLI
        e = {k: v for k, v in os.environ.items() if k not in ("GOAL_DIR", "SCOPE_DIR")}
        g = subprocess.run([sys.executable, "-B", CLI, "park", "--text", "x", "--level", "goal"], env=e, capture_output=True, text=True)
        self.assertEqual((g.returncode, len(g.stderr.strip().splitlines())), (2, 1))
        self.assertEqual(self.f.read_bytes(), before)
        self.r("resolve", "Q1", "--answer", "z", **env)
        done = self.f.read_bytes()
        self.assertNotEqual(self.r("resolve", "Q1", "--answer", "again", **env).returncode, 0)
        self.assertNotEqual(self.r("unpark", "Q1", **env).returncode, 0)
        self.assertEqual(self.f.read_bytes(), done)
        self.assertNotEqual(before, done)


if __name__ == "__main__":
    unittest.main()
