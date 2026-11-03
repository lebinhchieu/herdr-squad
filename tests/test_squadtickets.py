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

    def test_report_tasks_uses_the_same_function(self):
        self.assertIs(st._find_tickets, sti.find_tickets)


if __name__ == "__main__":
    unittest.main()
