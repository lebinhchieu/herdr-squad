import json
import unittest
from pathlib import Path

TEXT = (Path(__file__).resolve().parent.parent / "agents/team-lead.md").read_text()


class TeamLeadRoleTest(unittest.TestCase):
    def test_exists_in_m_and_l_and_takes_the_handover(self):
        self.assertIn("**M and L**", TEXT)
        self.assertIn("## Handover", TEXT)

    def test_spawns_and_retires_dev_only(self):
        self.assertIn("Spawn and retire Developers, only Developers", TEXT)
        self.assertIn("Spawn or retire any role but `dev`", TEXT)
        self.assertIn("squad-spawn dev", TEXT)
        self.assertIn("squad-retire", TEXT)

    def test_old_spawn_route_is_gone(self):
        self.assertNotIn("ASK manager: spawn dev", TEXT)
        self.assertNotIn("The Manager spawns one Developer", TEXT)

    def test_cap_share_rule(self):
        for s in ("the next task waits as `ready`", "A finished scope's share goes to the scopes still running",
                  "next briefing or respawn", "The cap is a rule, not a lock"):
            self.assertIn(s, TEXT)

    def test_no_relay_and_no_routine_manager_message(self):
        self.assertIn("Relay a blocked pane or a permission prompt", TEXT)
        self.assertIn("Message the Manager for a routine matter", TEXT)

    def test_final_rule_and_summary(self):
        self.assertIn("start it with `FINAL:`", TEXT)
        self.assertIn("iterations/<n>.summary.md", TEXT)
        self.assertIn("at most 40 lines", TEXT)

    def test_respawn_reads(self):
        for s in ("notes", "the plan", "roster.md", "herdr agent list"):
            self.assertIn(s, TEXT.split("## State lives in files")[1])

    def test_keeps_model_and_notes_block(self):
        self.assertNotIn("model:", TEXT.split("---")[1])  # T9: model and effort live in settings/team-lead.json
        cfg = json.loads((Path(__file__).resolve().parent.parent / "templates/squad/settings/team-lead.json").read_text())
        self.assertEqual((cfg["model"], cfg["effortLevel"]), ("sonnet", "medium"))
        self.assertIn("## Start of every session", TEXT)
        self.assertIn("## Notes", TEXT)

    def test_party_to_dispute_does_not_settle_it(self):
        self.assertIn("yourself a party to a plan, order or assignment dispute, do not settle it; after the two-round rule it goes to the Manager", TEXT)

    def test_summary_names_passed_sha_and_checkers(self):
        self.assertIn("each task's final passed sha and the checkers that passed it", TEXT)


if __name__ == "__main__":
    unittest.main()
