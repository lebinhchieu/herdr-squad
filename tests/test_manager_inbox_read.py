import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from rulesview import composed  # noqa: E402

TEXT = composed("manager", "M")  # the inbox lines moved from the card to ITER-4, ITER-5 and ITER-11


def rule(rid):
    return TEXT.split(f"## {rid} ")[1].split(" ## ")[0]


BULLET = rule("ITER-4")
CARRIES = rule("ITER-5")
CHECKIN = rule("ITER-11")


class ManagerInboxReadTest(unittest.TestCase):
    def test_a_note_with_nothing_to_decide_goes_through_kind_read(self):
        self.assertIn("A note with nothing to decide", BULLET)
        self.assertIn("goes through `squad-inbox add --kind read`", BULLET)

    def test_a_resolved_question_is_withdrawn(self):
        self.assertIn('`squad-inbox withdraw E<n> --reason "<why>"`), not left open', BULLET)

    def test_existing_rules_of_the_bullet_stay(self):
        for s in ("One `squad-inbox add` per Bash call, never two.", '`--blocks ""`', "no pipe and no unquoted heredoc"):
            self.assertIn(s, BULLET)


class ManagerCheckinInInboxTest(unittest.TestCase):
    def test_checkin_is_one_inbox_item(self):
        for s in ("squad-inbox add", "--kind read", "--kind answer"):
            self.assertIn(s, CHECKIN)

    def test_checkin_keeps_its_contents_and_cleanup(self):
        for s in ("evidence links", "3 returns", "open escalations", "proposed role-instruction changes",
                  "delete its row from `escalations.md`"):
            self.assertIn(s, CHECKIN)

    def test_carries_only_existing_sentences_stay(self):
        for s in ("Never offer a merge, push or deploy as an item",
                  "that stays the PO's explicit request in this chat"):
            self.assertIn(s, CARRIES)


if __name__ == "__main__":
    unittest.main()
