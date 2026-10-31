"""The process.md template obeys its own Writing rule on every suite run (bin/processlint.py, design §9)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import processlint  # noqa: E402


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

    def test_rule_block_lints_clean_as_text(self):
        self.assertEqual(processlint.lint("# Rule\n\n## Block\n\n" + RULE), [])


if __name__ == "__main__":
    unittest.main()
