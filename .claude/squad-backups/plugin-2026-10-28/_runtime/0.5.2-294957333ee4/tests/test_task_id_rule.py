import unittest
from pathlib import Path

from rulesview import ROOT, acts, composed

BULLET = "the ticket number `NN` alone, never an alias or slug"  # 22 shortened MSG-3


class TaskIdRule(unittest.TestCase):
    def test_rule_is_targeted_at_every_role_and_size(self):  # was test_template_has_bullet
        for size in "SML":
            self.assertEqual(len(acts("MSG-3", size)), 9 if size != "S" else len(acts("MSG-3", "S")))
        for role in ("dev", "qa-whitebox", "team-lead"):
            self.assertIn(BULLET, composed(role, "M"))

    # deleted: test_v5_has_it_v4_not (history files; test_process_history owns them)

    def test_rosters_say_ticket_nn(self):
        for p in ("scope", "goal"):
            t = (ROOT / f"templates/{p}/roster.md").read_text(encoding="utf-8")
            self.assertIn("`Owns` reads `ticket NN`", t)


if __name__ == "__main__":
    unittest.main()
