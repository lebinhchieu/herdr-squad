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

    def test_watchdog_blind_state_line_is_read_when_no_status(self):
        for text, want in (("State: ready (no Developer yet)", "ready"), ("State: handed in (5bc3126); QA next", "handed in"),
                           ("State: ready\nStatus: done", "done"), ("Status: done\nState: ready", "done"),
                           ("\n" * 12 + "State: ready", "")):
            self.assertEqual(sti.status_of(text), want, text)

    def test_T28_AC13_TA1_I_coach_and_summary_files_are_not_tasks(self):
        tk = self.home / "tasks"
        for n in ("03-x.md", "03-x.coach.md", "05-y.summary.md", "07.md"):
            self.put(tk / n, "# %s\n" % n)
        r = self.run_()
        self.assertEqual([(t["id"], t["where"].rsplit("/", 1)[1]) for t in r["tasks"]], [("03", "03-x.md"), ("07", "07.md")])

    def test_T28_TA13_TA1_H_plan_is_capped_and_iteration_plan_is_read_newest_first(self):
        self.put(self.home / "iterations" / "1.md", "| 1 | Old |\n")
        self.put(self.home / "iterations" / "2.md", "| id | t |\n|---|---|\n| 9 | Nine |\n" + "x" * (sti.TEXT_MAX * 2))
        r = self.run_()
        self.assertEqual((r["source"], r["tasks"][0]["id"], r["tasks"][0]["where"]), ("plan", "09", "plan table, 2.md"))
        self.put(self.home / "plan.md", ("| id | t |\n" + "junk\n" * (sti.TEXT_MAX // 5 + 10)) + "| 5 | Past the cap |\n")
        self.assertEqual(self.run_()["tasks"][0]["id"], "09")   # plan.md has no row inside the cap: next candidate



import subprocess  # noqa: E402
from unittest import mock  # noqa: E402

GENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import squadboard_git as sbg  # noqa: E402


class TicketMerge(unittest.TestCase):
    """Ticket 01: copies of a ticket on main, unmerged scope branches and drafts merge by number (real git repo)."""
    clock = 1_700_000_000

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name).resolve()
        self.home = self.root / ".claude" / "squads" / "s" / "scopes" / "foo"
        (self.home / "tasks").mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.put(".scratch/foo/issues/01-one.md", "# 01 One\nStatus: ready-for-agent\n")
        self.put(".scratch/foo/issues/02-two.md", "# 02 Two v1\nStatus: ready-for-agent\n")
        self.put(".scratch/foo/issues/05-five.md", "# 05 Five main\nStatus: ready-for-agent\n")
        self.commit("main")
        sti._TREES.clear()
        sti._BASES.clear()
        sti._HEADS.clear()
        sti._BLOBS.clear()

    def tearDown(self):
        self.td.cleanup()

    def git(self, *a, date=None):
        env = dict(GENV)
        if date:
            env.update(GIT_AUTHOR_DATE="@%d +0000" % date, GIT_COMMITTER_DATE="@%d +0000" % date)
        return subprocess.run(["git", "-C", str(self.root), *a], check=True, capture_output=True, text=True, env=env).stdout

    def put(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, msg, date=None):
        self.git("add", "-A", ".scratch")
        self.git("commit", "-q", "-m", msg, date=date or self.clock)

    def branch(self, name, files, date):
        """A branch off main holding `files` ({rel: text}); main is checked out again after."""
        self.git("checkout", "-q", "-b", name, "main")
        for rel, text in files.items():
            self.put(rel, text)
        self.commit(name, date)
        self.git("checkout", "-q", "main")

    def tasks(self, **kw):
        sti._HEADS.clear()
        r = sti.scope_tasks(self.home, self.root, "foo", **kw)
        return {t["id"]: t for t in r["tasks"]}

    def test_AC1_main_branch_and_draft_tickets_listed_once_each(self):
        self.branch("squad/s/foo/dev-03", {".scratch/foo/issues/03-three.md": "# 03 Three\nStatus: building\n"}, self.clock + 10)
        self.put(".claude/squads/s/scopes/foo/tasks/04-ticket.md", "# 04 Four\n")
        r = sti.scope_tasks(self.home, self.root, "foo")
        self.assertEqual([t["id"] for t in r["tasks"]], ["01", "02", "03", "04", "05"])
        o = {t["id"]: (t["origin"], t["origin_ref"], t["on_main"]) for t in r["tasks"]}
        self.assertEqual(o["01"], ("main", "", True))
        self.assertEqual(o["03"], ("branch", "squad/s/foo/dev-03", False))
        self.assertEqual(o["04"], ("draft", "", False))
        self.assertEqual(r["source"], "scratch")
        self.assertNotIn("abs", self.tasks()["03"])   # branch-only: no file on disk to open
        self.assertIn("abs", self.tasks()["04"])

    def test_AC2_T01_2_pick_order_own_branch_then_newest_other_then_main_then_draft(self):
        self.branch("squad/s/foo/other", {".scratch/foo/issues/05-five.md": "# 05 Five other\nStatus: returned\n"}, self.clock + 50)
        self.branch("squad/s/foo/dev-05", {".scratch/foo/issues/05-five.md": "# 05 Five own\nStatus: building\n"}, self.clock + 10)
        self.put(".claude/squads/s/scopes/foo/tasks/05-ticket.md", "# 05 Five draft\n")
        t = self.tasks()["05"]
        self.assertEqual((t["title"], t["status"], t["origin_ref"], t["on_main"]), ("Five own", "building", "squad/s/foo/dev-05", True))
        self.git("branch", "-D", "squad/s/foo/dev-05")
        self.assertEqual(self.tasks()["05"]["title"], "Five other")   # newest other branch
        self.git("branch", "-D", "squad/s/foo/other")
        t = self.tasks()["05"]
        self.assertEqual((t["title"], t["origin"]), ("Five main", "main"))   # main beats the draft

    def test_T01_2_branch_copy_equal_to_main_is_main_and_merged_branch_is_ignored(self):
        self.branch("squad/s/foo/dev-01", {".scratch/foo/issues/09-nine.md": "# 09 Nine\n"}, self.clock + 5)   # 01 untouched: same blob
        self.assertEqual(self.tasks()["01"]["origin"], "main")
        self.branch("squad/s/foo/old", {".scratch/foo/issues/02-two.md": "# 02 Two v0\n"}, self.clock + 6)
        self.git("merge", "-q", "--no-ff", "-m", "m", "squad/s/foo/old")
        self.put(".scratch/foo/issues/02-two.md", "# 02 Two v2\n")
        self.commit("v2", self.clock + 20)
        t = self.tasks()["02"]
        self.assertEqual((t["title"], t["origin"]), ("Two v2", "main"))   # the merged branch holds an older copy

    def test_T01_3_no_git_and_spent_budget_give_the_non_git_rows_and_no_raise(self):
        self.branch("squad/s/foo/dev-03", {".scratch/foo/issues/03-three.md": "# 03 Three\n"}, self.clock + 10)
        empty = tempfile.mkdtemp(dir=self.td.name)
        with mock.patch.dict(os.environ, {"PATH": empty}):
            self.assertEqual(sorted(self.tasks()), ["01", "02", "05"])
        with mock.patch.object(sti.time, "monotonic", side_effect=[0, 100, 200, 300, 400, 500]):
            self.assertEqual(sorted(self.tasks()), ["01", "02", "05"])
        with mock.patch.object(sti, "GIT_BUDGET_S", 0):   # a spent budget: non-git rows, and the budget stays under the reader's 3 s
            self.assertEqual(sorted(self.tasks()), ["01", "02", "05"])
        self.assertLess(sti.GIT_BUDGET_S, 3.0)
        self.assertEqual(sorted(self.tasks(git=False)), ["01", "02", "05"])
        self.assertEqual(sorted(self.tasks()), ["01", "02", "03", "05"])

    def test_T01_4_helpers_refuse_anything_but_a_40_hex_sha(self):
        for bad in ("main", "--output=x", "HEAD", "abc", "g" * 40, None):
            self.assertIsNone(sbg.ls_tree_blobs(self.root, bad, ".scratch/foo/issues"))
            self.assertIsNone(sbg.show_blob(self.root, bad))

    def test_T01_6_second_call_for_the_same_tip_is_served_from_the_cache(self):
        self.branch("squad/s/foo/dev-03", {".scratch/foo/issues/03-three.md": "# 03 Three\n"}, self.clock + 10)
        self.tasks()
        with mock.patch.object(sbg, "ls_tree_blobs", side_effect=AssertionError("ls-tree")), \
                mock.patch.object(sbg, "show_blob", side_effect=AssertionError("show")):
            self.assertEqual(self.tasks()["03"]["origin"], "branch")

    def test_AC3_report_picker_and_panel_list_the_same_tickets(self):
        self.branch("squad/s/foo/dev-03", {".scratch/foo/issues/03-three.md": "# 03 Three\n"}, self.clock + 10)
        self.put(".claude/squads/s/scopes/foo/tasks/04-ticket.md", "# 04 Four\n")
        import squadboard_list
        import squadboard_tasks
        report = sorted(sti.find_tickets(SimpleNamespace(scope_home=str(self.home), name="foo"), [])[0])
        squad = SimpleNamespace(repo_root=self.root)
        picker = sorted(squadboard_list._tickets(squad, self.home, "", None))
        prow = squadboard_tasks.read_scope("s", "foo", self.home, self.root, 0, 0)[0]
        panel = sorted(t["id"] for t in prow)
        self.assertEqual({t["id"]: (t["origin"], t["on_main"]) for t in prow}["03"], ("branch", False))   # row fields reach the panel
        self.assertEqual(report, ["01", "02", "03", "04", "05"])
        self.assertEqual((picker, panel), (report, report))

    def test_T01_8_watchdog_and_reviewpack_skip_git(self):
        for f in ("bin/squad-watchdog", "bin/squadreviewpack.py"):
            self.assertIn("git=False", Path(HERE, "..", f).read_text(encoding="utf-8"))
