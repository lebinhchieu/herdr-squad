import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "agents/manager.md").read_text(encoding="utf-8")
BULLET = next(l for l in TEXT.splitlines() if l.startswith("- **Inbox.**"))


class ManagerInboxReadTest(unittest.TestCase):
    def test_a_note_with_nothing_to_decide_goes_through_kind_read(self):
        self.assertIn("A note with nothing to decide", BULLET)
        self.assertIn("goes through `squad-inbox add --kind read`", BULLET)

    def test_a_note_is_never_a_hand_written_row(self):
        self.assertIn("never a hand-written row in `escalations.md`", BULLET)
        self.assertIn("only `--kind answer` makes a row, and the command writes it", BULLET)

    def test_a_resolved_question_is_withdrawn(self):
        self.assertIn('`squad-inbox withdraw E<n> --reason "<why>"`), not left open', BULLET)

    def test_the_hand_written_row_licence_is_gone(self):
        self.assertNotIn("rows written by hand still work", TEXT.lower())

    def test_existing_rules_of_the_bullet_stay(self):
        for s in ("One `squad-inbox add` per Bash call, never two.", '`--blocks ""`', "no pipe and no unquoted heredoc"):
            self.assertIn(s, BULLET)


if __name__ == "__main__":
    unittest.main()
