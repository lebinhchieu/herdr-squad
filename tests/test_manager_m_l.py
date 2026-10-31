"""Manager rules: Team Lead runs the pod in M and L; S text differs. Checked on the composed Manager rules."""
import unittest

from rulesview import composed

MS = composed("manager", "S")
MM = composed("manager", "L")  # Team Lead exists at L only
MG = composed("manager", "L", goal="yes")


class ManagerMLTest(unittest.TestCase):
    def test_s_keeps_developer_spawning_and_routing(self):
        self.assertIn("## SPAWN-5a Developers, Manager plans", MS)
        self.assertIn("## SPAWN-5a", composed("manager", "M"))
        self.assertIn("## MSG-18 Routing, Manager", MS)
        self.assertNotIn("## SPAWN-5a", MM)
        self.assertNotIn("## MSG-18", MM)

    def test_manager_three_returns_rule_per_team_shape(self):
        """Every Manager gets a three-returns rule when it is the plan owner; the Team Lead's shape only hears of it."""
        import re
        from test_dev_rules_size import compose
        def ids(size):
            return set(re.findall(r"(?m)^## (LC-7[a-z]?) ", compose("manager", size).decode()))
        def body(size):
            return compose("manager", size).decode().split("## LC-7a")[1].split("\n## ")[0]
        self.assertEqual(ids("S") & {"LC-7a", "LC-7b", "LC-7c"}, {"LC-7a"})
        self.assertIn("you step in; with QAs on the team", body("S"))  # conditional, so valid with no QA
        self.assertEqual(ids("M") & {"LC-7a", "LC-7b", "LC-7c"}, {"LC-7a"})  # qa-white + qa-black, no Team Lead
        self.assertIn("with QAs on the team the 3rd failing QA sends you `BLOCKED NN: 3 returns`", body("M"))
        self.assertEqual(ids("L") & {"LC-7a", "LC-7b", "LC-7c"}, {"LC-7b"})  # aware only: the Team Lead decides

    def test_retained_duties(self):
        for token in ("Adding a role", "Merge only on the PO's request", "squad-inbox add", "Token Coach", "squad-close <squad> --scope"):
            self.assertIn(token, MG)


if __name__ == "__main__":
    unittest.main()
