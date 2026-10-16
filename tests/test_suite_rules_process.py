"""Suite rules: only the Tech Lead runs the full suite (PO note 2026-10-17)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = (ROOT / "templates/squad/process.md").read_text()
CLAUDE = (ROOT / "CLAUDE.md").read_text()
SAFETY = T[T.index("## Safety"):]
SUITES = SAFETY[SAFETY.index("- **Suites"):SAFETY.index("- **Close what you open")]


class SuiteRulesTest(unittest.TestCase):
    def test_suites_bullet_replaces_long_suites(self):
        self.assertIn("- **Suites: only the Tech Lead runs the full suite.**", T)
        self.assertNotIn("Long suites", T)

    def test_tech_lead_runs_it_and_others_never(self):
        self.assertIn("Developers and QAs run only the test files their diff touches. They never run the full suite", SUITES)
        self.assertIn("The Tech Lead decides when it runs", SUITES)
        self.assertIn("never runs the suite", SUITES)

    def test_no_overlap(self):
        self.assertIn("two suite runs never overlap", SUITES)

    def test_timing(self):
        self.assertIn("once for a batch of tasks, or at the end of the scope or iteration", SUITES)

    def test_receipt_first_line(self):
        self.assertIn("first line `sha <git rev-parse HEAD> clean=<yes|no>`", SUITES)

    def test_failure_returns_the_task(self):
        self.assertIn("names the task whose files fail", SUITES)

    def test_integration_and_light_lines_do_not_make_dev_or_qa_run_it(self):
        (integ,) = [l for l in T.splitlines() if "branches from the scope's base" in l]
        self.assertIn("runs the targeted tests and hands in; the Tech Lead then runs the full suite", integ)
        (light,) = [l for l in T.splitlines() if l.startswith("- **QA mode**")]
        self.assertIn("QA runs the targeted tests", light)
        self.assertNotIn("failing suite", light)

    def test_claude_md_points_at_process(self):
        self.assertIn("`process.md` → Safety → Suites", CLAUDE)
        self.assertNotIn("agents/dev.md", CLAUDE)
        self.assertIn("python3 tests/run_suite.py --receipt", CLAUDE)

    def test_role_files_cite_the_rule(self):
        for f in ("dev", "tech-lead"):
            self.assertIn("process.md` → Safety → Suites", (ROOT / f"agents/{f}.md").read_text())
        self.assertNotIn("Long suites", (ROOT / "agents/dev.md").read_text())
