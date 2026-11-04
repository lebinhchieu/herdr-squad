"""squadtickets: ticket folder finder moved out of squadreport_tasks; no folder gives ({}, None)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import squadreport_tasks as st  # noqa: E402
import squadtickets as sti  # noqa: E402


class FindTickets(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name).resolve()
        iss = self.root / ".scratch" / "feat" / "issues"
        iss.mkdir(parents=True)
        (iss / "01-first.md").write_text("# 01: First thing\n", encoding="utf-8")
        (iss / "02-second.md").write_text("no heading\n", encoding="utf-8")
        home = self.root / ".claude" / "squads" / "s" / "scopes" / "x"
        home.mkdir(parents=True)
        self.c = SimpleNamespace(scope_home=str(home), name="feat")

    def tearDown(self):
        self.td.cleanup()

    def test_finds_titles_and_dir(self):
        out, d = sti.find_tickets(self.c, ["01", "02-second"])
        self.assertEqual(out, {"01": "First thing", "02": "second"})
        self.assertEqual(d, ".scratch/feat")

    def test_no_scratch_is_unknown(self):
        with tempfile.TemporaryDirectory() as other:
            if any((p / ".scratch").is_dir() for p in [Path(other).resolve(), *Path(other).resolve().parents]):
                self.skipTest(".scratch above the temp dir")
            c = SimpleNamespace(scope_home=other, name="feat")
            self.assertEqual(sti.find_tickets(c, ["01"]), ({}, None))

    def test_empty_folder_is_unknown(self):
        (self.root / ".scratch" / "feat" / "issues" / "01-first.md").unlink()
        (self.root / ".scratch" / "feat" / "issues" / "02-second.md").unlink()
        self.assertEqual(sti.find_tickets(self.c, ["01"]), ({}, None))

    def test_T07_TA5_tickets_line_wins_over_guess(self):
        other = self.root / ".scratch" / "other" / "issues"
        other.mkdir(parents=True)
        (other / "01-x.md").write_text("# 01: Other\n", encoding="utf-8")
        (Path(self.c.scope_home) / "scope.md").write_bytes(b"Tickets: other\r\n")
        out, d = sti.find_tickets(self.c, ["01", "02-second"])  # tokens favour `feat`, the line still wins
        self.assertEqual((out, d), ({"01": "Other"}, ".scratch/other"))

    def test_T07_TA5_line_with_missing_folder_falls_back(self):
        (Path(self.c.scope_home) / "scope.md").write_text("tickets: nope\n", encoding="utf-8")
        self.assertEqual(sti.find_tickets(self.c, [])[1], ".scratch/feat")
        self.assertEqual(sti.declared_folder(self.c.scope_home), "nope")

    def test_report_tasks_uses_the_same_function(self):
        self.assertIs(st._find_tickets, sti.find_tickets)


if __name__ == "__main__":
    unittest.main()


class ScopeTasksRule(unittest.TestCase):
    """T28: one rule (scope_tasks) over the layouts; no guess from other scopes."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name).resolve()
        (self.root / ".scratch").mkdir()
        self.home = self.root / ".claude" / "squads" / "s" / "scopes" / "foo"
        (self.home / "tasks").mkdir(parents=True)

    def tearDown(self):
        self.td.cleanup()

    def put(self, path, text):
        p = self.root / path if not str(path).startswith("/") else Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run_(self):
        return sti.scope_tasks(self.home, self.root, "foo")

    def test_T28_TA1_source_order_and_fall_through(self):
        tk = self.home / "tasks"
        self.put(tk / "01.md", "# 01 Repro: what it meets\nStatus: done (Manager-confirmed; QA)\n")
        self.put(tk / "TEMPLATE.md", "# t\n")
        self.put(tk / "03-evidence" / "evidence.md", "x\n")
        r = self.run_()  # E/B: scope's own files; heading without separator
        self.assertEqual((r["source"], [t["id"] for t in r["tasks"]]), ("scope", ["01"]))
        self.assertEqual((r["tasks"][0]["title"], r["tasks"][0]["status"]), ("Repro: what it meets", "done"))
        self.assertEqual(r["tasks"][0]["where"], ".claude/squads/s/scopes/foo/tasks/01.md")
        self.assertIn("abs", r["tasks"][0])
        self.put(".scratch/foo/issues/05-x.md", "# 05 x\n")  # C: .scratch/<scope> beats the scope's files
        self.assertEqual(self.run_()["source"], "scratch")
        self.put(".scratch/slug/issues/NOTES.md", "n\n")  # F: tickets: line, folder without ticket files, falls through
        self.put(self.home / "scope.md", "tickets: slug\n")
        self.assertEqual(self.run_()["source"], "scratch")
        self.put(".scratch/slug/issues/02-y.md", "# 02 y\n")  # A: declared wins
        r = self.run_()
        self.assertEqual((r["source"], [t["id"] for t in r["tasks"]]), ("declared", ["02"]))

    def test_T28_AC14_drafts_and_plan_and_looked(self):
        self.put(self.home / "tasks" / "issues" / "01-a.md", "# 01 a\nStatus: handed in abc, x\n")
        r = self.run_()
        self.assertEqual((r["source"], r["tasks"][0]["status"]), ("scope", "handed in"))
        for f in (self.home / "tasks" / "issues").iterdir():
            f.unlink()
        self.put(self.home / "plan.md", "| id | title |\n|---|---|\n| 07 | Seven |\n")
        r = self.run_()
        self.assertEqual((r["source"], r["tasks"][0]["where"]), ("plan", "plan table, plan.md"))
        (self.home / "plan.md").unlink()
        r = self.run_()
        self.assertEqual((r["source"], r["tasks"], bool(r["looked"])), (None, [], True))

    def test_T28_TA2_no_guess_from_other_scope(self):
        self.put(".scratch/other/issues/01-x.md", "# 01 x\n")
        c = SimpleNamespace(scope_home=str(self.home), name="foo")
        self.assertEqual(sti.find_tickets(c, ["01"]), ({}, None))

    def test_T28_TA5_status_word(self):
        for text, want in (("Status: done (x; y)", "done"), ("Status: Done", "done"), ("Status: handed in e8a, x", "handed in"),
                           ("Status: in progress", "in progress"), ("Status: ready-for-agent", "ready-for-agent"),
                           ("# t", ""), ("\n" * 12 + "Status: done", "")):
            self.assertEqual(sti.status_of(text), want, text)
