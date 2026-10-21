"""Suite rules: only the Tech Lead runs the full suite (PO note 2026-10-17); now checked on the SUITE rules."""
import unittest

from rulesview import ROOT, acts, composed, run, who


class SuiteRulesTest(unittest.TestCase):
    # deleted: test_suites_bullet_replaces_long_suites (asserted a v6 heading; SUITE-* rules are linted)

    def test_tech_lead_runs_it_and_others_never(self):
        self.assertIn("Only the Tech Lead runs the full suite.", composed("tech-lead", "M"))
        self.assertIn("the full suite is the Tech Lead's", composed("dev", "M"))
        self.assertIn("never runs the suite", composed("qa-whitebox", "M"))
        self.assertEqual(acts("SUITE-3", "M"), ("tech-lead",))

    def test_no_overlap(self):
        self.assertIn("two suite runs never overlap", composed("dev", "M"))
        self.assertIn("two suite runs never overlap", composed("qa-blackbox", "M"))

    def test_timing(self):
        self.assertIn("once for a batch of tasks, or at the end of the scope or iteration", composed("tech-lead", "M"))

    def test_receipt_first_line(self):
        self.assertIn("first line `sha <git rev-parse HEAD> clean=<yes|no>`", composed("tech-lead", "M"))

    def test_failure_returns_the_task(self):
        self.assertIn("name the task whose files fail", composed("tech-lead", "M"))

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
        self.assertIn("runs the targeted tests for the changed files and hands in", dev)
        self.assertIn("the Tech Lead runs the full suite after", dev)
        tl = composed("tech-lead", "M", goal="yes")
        self.assertIn("runs the targeted tests", tl)
        self.assertNotIn("and runs the full suite", tl)
        self.assertIn("You decide when the full suite runs", tl)


if __name__ == "__main__":
    unittest.main()
