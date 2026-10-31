import unittest
from rulesview import acts, composed

BULLET = "the ticket number `NN` alone, never an alias or slug"  # 22 shortened MSG-3


class TaskIdRule(unittest.TestCase):
    def test_rule_is_targeted_at_every_role_and_size(self):  # was test_template_has_bullet
        for size in "SML":
            self.assertEqual(len(acts("MSG-3", size)), 9 if size != "S" else len(acts("MSG-3", "S")))
        for role in ("dev", "qa-whitebox", "team-lead"):
            self.assertIn(BULLET, composed(role, "M"))


if __name__ == "__main__":
    unittest.main()
