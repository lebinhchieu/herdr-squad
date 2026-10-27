"""The Team Lead model in the rules (M and L); S text differs. Old template/V3/V6 history assertions: deleted,
the v6 template and its history copies are checked by test_process_history until ticket 09 retires them."""
import unittest

from rulesview import acts, composed, who


class PodRulesTest(unittest.TestCase):
    def test_m_roles_include_team_lead_and_l_is_as_m(self):  # was test_m_roles_include_team_lead_and_l_is_as_m
        self.assertIn("team-lead", acts("MSG-5", "plan-owner = team-lead"))
        self.assertEqual(acts("MSG-5", "plan-owner = manager"), ())  # the Team Lead plans only when the team has one

    def test_plan_duty_is_manager_in_s_and_m(self):  # was test_plan_duty_row_is_tech_lead_in_s_only
        self.assertIn("manager", acts("SIZE-6a", "S"))
        self.assertEqual(acts("LC-15", "plan-owner = team-lead"), ("team-lead",))
        self.assertEqual(acts("LC-15", "plan-owner = manager"), ())
        self.assertEqual(acts("LC-17b", "plan-owner = manager"), ("manager",))

    # deleted: test_s_row_is_unchanged (compared the v6 size table with V3; the table is in SIZE rules, covered by test_squadrules)

    def test_pod_contact_and_team_lead_to_manager(self):  # was test_pod_contact_and_team_lead_to_manager_bullets
        # 22: MSG-5 left the Developer (carrier: MSG-4b/MSG-11b name the Team Lead); the QAs still get it as aware
        self.assertIn("Pod members message it, not the Manager.", composed("qa-whitebox", "L"))
        self.assertNotIn("MSG-5", composed("dev", "L"))
        tl = composed("team-lead", "L")
        self.assertIn("MSG-6 Team Lead to Manager", tl)
        self.assertIn('an "Always goes to PO" item', tl)

    def test_summary_file_row(self):
        self.assertIn("at most 40 lines", composed("team-lead", "L"))
        self.assertIn("team-lead", acts("ITER-3", "L"))
        # 06: sizes dropped; ITER-3 is the plan owner's, ITER-3b the Manager's when the Manager owns the plan
        self.assertEqual(acts("ITER-3b", "M"), ("manager",))
        self.assertIn("at most 40 lines", composed("manager", "M"))

    def test_cap_clause_has_goal_share(self):  # was test_cap_bullet_has_goal_share_clause
        self.assertIn("goal Manager divides", composed("manager", "M", goal="yes"))

    def test_final_rule_covers_the_team_lead(self):
        self.assertIn("A Manager or Team Lead ruling starts with `FINAL:` and is sent once.", composed("team-lead", "L"))

    def test_no_relay_rule(self):  # was test_no_relay_bullet
        self.assertIn("Never relay a permission, approval or blocked pane", composed("team-lead", "L"))

    def test_down_and_handover_clauses(self):
        self.assertIn("Retire the removed role's session", composed("manager", "M"))
        self.assertIn("the Manager writes a `## Handover` section", composed("manager", "L"))

    def test_s_keeps_the_confirm_gate_for_all_spawns(self):
        self.assertIn("PO confirms", composed("manager", "S"))

    # deleted: test_no_leftover_old_model, test_no_byte_budget (asserted absences in the v6 template text; the rule files are linted by `squad-process lint`)

    def test_team_lead_dispute_wording(self):  # was test_team_lead_to_manager_dispute_wording
        tl = composed("team-lead", "L")
        self.assertIn("the parties go to the Manager themselves; you are not a relay", tl)
        self.assertNotIn("cannot settle", tl)
        self.assertIn("When you are yourself a party", tl)


if __name__ == "__main__":
    unittest.main()
