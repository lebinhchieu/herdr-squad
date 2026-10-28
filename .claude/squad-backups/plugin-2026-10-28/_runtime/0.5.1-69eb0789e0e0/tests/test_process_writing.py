"""The process.md template obeys its own Writing rule on every suite run (bin/processlint.py, design §9)."""
import inspect
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import processlint  # noqa: E402

TEMPLATE = ROOT / "templates/squad/process.md"

# (check, line-text prefix, reason): each one approved by the BA. None yet.
EXCEPTIONS = []

# design §9
RULE = """**Writing rule for `process.md`.** Every agent reads it, so:
- **Decide a rule's level first.** A rule a teammate without the squad must also follow (the project's code, tools, test commands, conventions) goes into the instructions file `project.md` names, through a task the PO merges, never into `process.md`. `process.md` holds only how the squad works, true for any project.
- One rule per bullet, stated once in the section that owns it; elsewhere a pointer of at most one clause, never a copy.
- Each rule names who acts, when, and the limit or outcome, in must / never / at most. No hedges.
- No history, dates or incidents. A reason only as one short clause; an example only where it fixes a format; no sentence that only announces or restates.
- At most 60 words per bullet, paragraph or table cell, and at most one bold label of 15 words per bullet.
- Before an edit, run `python3 <plugin>/bin/processlint.py <file>`; the `process-log.md` row says it passed.
"""
MANAGER = ROOT / "agents/manager.md"


class ProcessWritingTest(unittest.TestCase):
    def test_template_lints_clean(self):
        self.assertEqual(processlint.lint(TEMPLATE.read_text(), exceptions=EXCEPTIONS), [])

    def test_every_exception_has_a_reason(self):
        for exc in EXCEPTIONS:
            self.assertEqual(len(exc), 3, exc)
            self.assertTrue(exc[2].strip(), exc)

    def test_manager_card_holds_the_writing_stance(self):  # was test_manager_holds_the_rule_verbatim: the card keeps a short stance, lint enforces the rest
        text = MANAGER.read_text()
        self.assertIn("## Writing a rule", text)
        self.assertIn("Decide a rule's level first", text)
        self.assertIn("`squad-process lint`", text)

    def test_level_bullet_is_first_in_manager_and_rule(self):
        first = "- **Decide a rule's level first.**"
        block = RULE.split("Every agent reads it, so:\n", 1)[1]
        self.assertTrue(block.startswith(first), RULE[:80])
        self.assertIn("level first", MANAGER.read_text())

    def test_rule_block_lints_clean_as_text(self):
        self.assertEqual(processlint.lint("# Rule\n\n## Block\n\n" + RULE), [])

    def test_no_byte_budget_anywhere(self):
        self.assertNotIn("budget", inspect.signature(processlint.lint).parameters)
        self.assertNotRegex(MANAGER.read_text(), r"stays within [\d,]+ bytes")

    def test_version_line_is_line_3(self):
        self.assertRegex(TEMPLATE.read_text().splitlines()[2], r"^process-version: [1-9]\d*$")


if __name__ == "__main__":
    unittest.main()
