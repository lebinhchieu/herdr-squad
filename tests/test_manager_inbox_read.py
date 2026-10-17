import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "agents/manager.md").read_text(encoding="utf-8")
BULLET = next(l for l in TEXT.splitlines() if l.startswith("- **Inbox.**"))
ANSWER = next(l for l in TEXT.splitlines() if l.startswith("- **A PO answer in chat**"))
CARRIES = next(l for l in TEXT.splitlines() if l.startswith("- **The inbox carries only"))
CHECKIN = next(l for l in TEXT.splitlines() if l.startswith("- **Check-in**"))


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


class ManagerCheckinInInboxTest(unittest.TestCase):
    def test_checkin_is_one_inbox_item(self):
        for s in ("squad-inbox add", "--kind read", "--kind answer"):
            self.assertIn(s, CHECKIN)

    def test_checkin_lists_each_step_the_po_must_take(self):
        self.assertIn("lists each step the PO must take", CHECKIN)

    def test_checkin_is_not_a_chat_report(self):
        low = CHECKIN.lower()
        self.assertIn("never as a chat report", low)
        self.assertNotIn("tell the po in chat", low)
        self.assertEqual(low.count("report"), 1)

    def test_checkin_keeps_its_contents_and_cleanup(self):
        for s in ("evidence links", "3 returns", "open escalations", "proposed role-instruction changes",
                  "delete its row from `escalations.md`"):
            self.assertIn(s, CHECKIN)

    def test_carries_only_allows_the_merge_words_in_the_checkin(self):
        self.assertIn("to merge, ask in chat", CARRIES)

    def test_carries_only_existing_sentences_stay(self):
        for s in ("Never offer a merge, push or deploy as an item", "needs their explicit request here",
                  "that stays the PO's explicit request in this chat"):
            self.assertIn(s, CARRIES)

    def test_a_chat_reply_never_lists_steps_for_the_po(self):
        self.assertIn("A chat reply to the PO never lists steps for the PO", BULLET)

    def test_inbox_and_answer_bullets_keep_their_wording_rules(self):
        self.assertIn("One `squad-inbox add` per Bash call, never two.", BULLET)
        self.assertIn("your reply is the printed line and nothing else", BULLET)
        self.assertIn("never answer from memory of what is open.", ANSWER)


if __name__ == "__main__":
    unittest.main()
