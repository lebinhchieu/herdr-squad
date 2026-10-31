"""The Team Lead model in the rules (M and L); S text differs. Old template/V3/V6 history assertions: deleted,
the v6 template and its history copies are checked by test_process_history until ticket 09 retires them."""
import unittest

from rulesview import acts


class PodRulesTest(unittest.TestCase):
    def test_m_roles_include_team_lead_and_l_is_as_m(self):  # was test_m_roles_include_team_lead_and_l_is_as_m
        self.assertIn("team-lead", acts("MSG-5", "plan-owner = team-lead"))
        self.assertEqual(acts("MSG-5", "plan-owner = manager"), ())  # the Team Lead plans only when the team has one

    def test_plan_duty_is_manager_in_s_and_m(self):  # was test_plan_duty_row_is_tech_lead_in_s_only
        self.assertIn("manager", acts("SIZE-6a", "S"))
        self.assertEqual(acts("LC-15", "plan-owner = team-lead"), ("team-lead",))
        self.assertEqual(acts("LC-15", "plan-owner = manager"), ())
        self.assertEqual(acts("LC-17b", "plan-owner = manager"), ("manager",))


if __name__ == "__main__":
    unittest.main()
