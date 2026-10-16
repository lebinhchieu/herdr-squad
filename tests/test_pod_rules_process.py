"""The Team Lead model in the process.md template (M and L); S text stays as it was."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = (ROOT / "templates/squad/process.md").read_text()
V3 = (ROOT / "skills/squad-process-update/history/process-v3.md").read_text()


def row(text, start):
    (line,) = [l for l in text.splitlines() if l.startswith(start)]
    return line


class PodRulesTest(unittest.TestCase):
    def test_m_roles_include_team_lead_and_l_is_as_m(self):
        self.assertIn("+ BA, QA whitebox, QA blackbox, Team Lead |", row(T, "| **M**"))
        self.assertIn("| As M |", row(T, "| **L**"))

    def test_plan_duty_row_is_tech_lead_in_s_only(self):
        self.assertIn("| Plan, order, assignment | Tech Lead | Team Lead | Team Lead |", T)

    def test_s_row_is_unchanged(self):
        self.assertEqual(row(T, "| **S**"), row(V3, "| **S**"))

    def test_pod_contact_and_team_lead_to_manager_bullets(self):
        self.assertIn("**Pod contact (M, L):**", T)
        self.assertIn("Pod members message it, not the Manager.", T)
        self.assertRegex(T, r"\*\*Team Lead to Manager \(M, L\):\*\* only an \"Always goes to PO\" item")

    def test_summary_file_row(self):
        self.assertRegex(T, r"\| `iterations/<n>\.summary\.md` \| Team Lead \(M, L\) \|.*at most 40 lines")

    def test_cap_bullet_has_goal_share_clause(self):
        self.assertIn("in a goal the goal Manager divides it among running scopes in their briefings", T)

    def test_final_rule_covers_the_team_lead(self):
        self.assertIn("**A Manager or Team Lead ruling starts with `FINAL:` and is sent once.**", T)

    def test_no_relay_bullet(self):
        self.assertIn("Never relay a permission, approval or blocked pane", T)

    def test_down_and_handover_clauses(self):
        self.assertIn("the Manager retires the roles that drop out", T)
        self.assertIn("a joining Team Lead takes the plan over from it", T)

    def test_no_leftover_old_model(self):
        for old in ("Tech Lead in S and M", "The Manager never pushes `STATUS`"):
            self.assertNotIn(old, T)

    def test_no_byte_budget(self):
        self.assertNotRegex(T, r"\bbytes\b")


if __name__ == "__main__":
    unittest.main()
