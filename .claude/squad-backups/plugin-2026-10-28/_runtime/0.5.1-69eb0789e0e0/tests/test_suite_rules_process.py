"""Suite rules: the size's owner runs the full suite once on the final sha (S Developer, M QA whitebox, L Tech Lead); checked on the SUITE rules."""
import unittest

from rulesview import ROOT, acts, composed, run, who


class SuiteRulesTest(unittest.TestCase):
    # deleted: test_suites_bullet_replaces_long_suites (asserted a v6 heading; SUITE-* rules are linted)

    def test_the_size_owner_runs_it_and_others_never(self):
        self.assertIn("Only the Tech Lead runs the full suite.", composed("tech-lead", "L"))
        self.assertIn("the full suite is the Tech Lead's", composed("dev", "L"))
        self.assertIn("the full suite is QA whitebox's", composed("dev", "M"))
        self.assertIn("You run the full suite for the scope, once, on the final sha", composed("qa-whitebox", "M"))
        self.assertIn("never run the suite", composed("qa-blackbox", "M"))
        self.assertIn("then the full suite once on your final sha", composed("dev", "S"))
        self.assertEqual(acts("SUITE-3", "L"), ("tech-lead",))
        self.assertEqual(acts("SUITE-3b", "M"), ("qa-whitebox",))
        self.assertEqual(acts("SUITE-3", "M"), ())

    def test_every_size_has_a_suite_owner(self):
        for size, rid, role in (("S", "SUITE-2d", "dev"), ("M", "SUITE-1b", "qa-whitebox"), ("L", "SUITE-1", "tech-lead")):
            self.assertEqual(acts(rid, size), (role,), (rid, size))

    def test_claude_md_names_the_size_owner(self):
        text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("S the Developer, M QA whitebox, L the Tech Lead", text)
        self.assertNotIn("Only the Tech Lead runs the full suite", text)

    def test_no_overlap(self):
        self.assertIn("two suite runs never overlap", composed("dev", "M"))
        self.assertIn("two suite runs never overlap", composed("dev", "L"))
        self.assertIn("two suite runs never overlap", composed("qa-blackbox", "L"))
        self.assertIn("no two suite runs overlap", composed("qa-blackbox", "M"))

    def test_timing(self):
        self.assertIn("once for a batch of tasks, or at the end of the scope or iteration", composed("tech-lead", "L"))
        self.assertIn("Run it once every task of the scope has passed, on the scope's final sha", composed("qa-whitebox", "M"))

    def test_receipt_first_line(self):
        self.assertIn("first line `sha <git rev-parse HEAD> clean=<yes|no>`", composed("tech-lead", "L"))
        self.assertIn("first line `sha <git rev-parse HEAD> clean=<yes|no>`", composed("qa-whitebox", "M"))

    def test_failure_returns_the_task(self):
        self.assertIn("name the task whose files fail", composed("tech-lead", "L"))
        self.assertIn("`FAIL` the task whose files fail", composed("qa-whitebox", "M"))

    def test_integration_and_light_lines_do_not_make_dev_or_qa_run_it(self):
        # 22: GOAL-6b is on demand for the Developer (the task file cites it): read it with `squad-process rule`
        self.assertIn("runs the targeted tests", run("rule", "GOAL-6b").stdout)
        self.assertNotIn("and runs the full suite", run("rule", "GOAL-6b").stdout)
        self.assertIn("QA runs the targeted tests", composed("qa-whitebox", "M", qa="light"))
        self.assertNotIn("failing suite", composed("qa-whitebox", "M", qa="light"))

    def test_claude_md_points_at_process(self):  # CLAUDE.md is not a card; it names the rules now
        claude = (ROOT / "CLAUDE.md").read_text()
        self.assertIn("process.md", claude)
        self.assertNotIn("agents/dev.md", claude)
        self.assertIn("python3 tests/run_suite.py --receipt", claude)

    def test_cards_no_longer_hold_suite_text(self):  # was test_role_files_cite_the_rule: the rule is attached, not cited
        for f in ("dev", "tech-lead"):
            self.assertNotIn("Long suites", (ROOT / f"agents/{f}.md").read_text())

    def test_integration_task_runs_targeted_tests(self):  # was test_integration_task_in_role_files_runs_targeted_tests
        dev = run("rule", "GOAL-6b").stdout  # 22: on demand for the Developer
        self.assertIn("runs the targeted tests for the changed files and is handed in", dev)
        self.assertIn("the suite owner runs the full suite after", dev)  # 30: owner by size, no absent role named
        tl = composed("tech-lead", "L", goal="yes")
        self.assertIn("runs the targeted tests", tl)
        self.assertNotIn("and runs the full suite", tl)
        self.assertIn("You decide when the full suite runs", tl)


if __name__ == "__main__":
    unittest.main()
