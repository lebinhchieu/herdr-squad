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

# design §9; {N} is the byte budget
RULE = """**Writing rule for `process.md`.** Every agent reads it, so:
- One rule per bullet, stated once in the section that owns it; elsewhere a pointer of at most one clause, never a copy.
- Each rule names who acts, when, and the limit or outcome, in must / never / at most. No hedges.
- No history, dates or incidents. A reason only as one short clause; an example only where it fixes a format; no sentence that only announces or restates.
- At most 60 words per bullet, paragraph or table cell, and at most one bold label of 15 words per bullet.
- The file stays within {N} bytes. A new rule replaces or merges with an existing one, or the PO raises the budget and logs it in `process-log.md`.
- Before an edit, run `python3 <plugin>/bin/processlint.py <file>`; the `process-log.md` row says it passed.
"""
MANAGER = ROOT / "agents/manager.md"


def manager_budget(text=None):
    m = re.search(r"stays within ([\d,]+) bytes", text if text is not None else MANAGER.read_text())
    return int(m.group(1).replace(",", ""))


class ProcessWritingTest(unittest.TestCase):
    def test_template_lints_clean(self):
        self.assertEqual(processlint.lint(TEMPLATE.read_text(), exceptions=EXCEPTIONS), [])

    def test_every_exception_has_a_reason(self):
        for exc in EXCEPTIONS:
            self.assertEqual(len(exc), 3, exc)
            self.assertTrue(exc[2].strip(), exc)

    def test_manager_holds_the_rule_verbatim_modulo_n(self):
        n = manager_budget()
        self.assertIn(RULE.replace("{N}", f"{n:,}"), MANAGER.read_text())

    def test_rule_block_lints_clean_as_text(self):
        block = RULE.replace("{N}", f"{manager_budget():,}")
        self.assertEqual(processlint.lint("# Rule\n\n## Block\n\n" + block), [])

    def test_budget_is_one_figure_everywhere(self):
        n = manager_budget()
        default = inspect.signature(processlint.lint).parameters["budget"].default
        self.assertEqual(n, default)
        self.assertEqual(n % 500, 0)
        self.assertGreaterEqual(n, len(TEMPLATE.read_bytes()))

    def test_version_line_is_line_3(self):
        self.assertRegex(TEMPLATE.read_text().splitlines()[2], r"^process-version: [1-9]\d*$")


if __name__ == "__main__":
    unittest.main()
