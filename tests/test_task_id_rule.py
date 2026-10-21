import unittest
from pathlib import Path

from rulesview import ROOT, acts, composed

BULLET = ("Every agent writes the ticket number `NN` alone as the task ID, "
          "never an alias, slug or prefix; a Developer's roster `Owns` reads `ticket NN`.")


class TaskIdRule(unittest.TestCase):
    def test_rule_is_targeted_at_every_role_and_size(self):  # was test_template_has_bullet
        for size in "SML":
            self.assertEqual(len(acts("MSG-3", size)), 8 if size != "S" else len(acts("MSG-3", "S")))
        for role in ("dev", "qa-whitebox", "team-lead"):
            self.assertIn(BULLET, composed(role, "M"))

    # deleted: test_v5_has_it_v4_not (history files; test_process_history owns them)

    def test_rosters_say_ticket_nn(self):
        for p in ("scope", "goal"):
            t = (ROOT / f"templates/{p}/roster.md").read_text(encoding="utf-8")
            self.assertIn("`Owns` reads `ticket NN`", t)


if __name__ == "__main__":
    unittest.main()
