"""The Team Lead role: identity on the card, duties in the rules attached for M and L."""
import json
import unittest
from pathlib import Path

from rulesview import ROOT, acts, composed

CARD = (ROOT / "agents/team-lead.md").read_text()
RULES = composed("team-lead", "L")

    def test_exists_when_the_team_lists_it_and_takes_the_handover(self):
        self.assertIn("lists `team-lead`", CARD)  # 06: no size in the card
    def test_exists_in_m_and_l_and_takes_the_handover(self):
        self.assertIn("**M and L**", CARD)
        self.assertIn("## Handover", RULES)
        self.assertIn("team-lead", acts("SIZE-17b", "L"))

    def test_spawns_and_retires_dev_only(self):
        self.assertIn("squad-spawn dev", RULES)
        self.assertIn("squad-retire", RULES)
        self.assertEqual(acts("SPAWN-9", "L"), ("team-lead",))
        self.assertIn("no", RULES.split("## SPAWN-9")[1].split("##")[0].lower())

    def test_old_spawn_route_is_gone(self):
        self.assertNotIn("ASK manager: spawn dev", RULES + CARD)
        self.assertNotIn("The Manager spawns one Developer", RULES + CARD)

    def test_cap_share_rule(self):
        for s in ("the next task waits as `ready`", "A finished scope's share goes to the scopes still running",
                  "next briefing or respawn", "The cap is a rule, not a lock"):
            self.assertIn(s, RULES)

    def test_no_relay_and_no_routine_manager_message(self):
        self.assertIn("Never relay a permission, approval or blocked pane", RULES)
        self.assertIn("never for a routine matter", RULES)
        self.assertIn("Never relay a blocked pane or a permission prompt", CARD)  # stance, kept on the card

    def test_final_rule_and_summary(self):
        self.assertIn("`FINAL:`", RULES)
        self.assertIn("iterations/<n>.summary.md", RULES)
        self.assertIn("at most 40 lines", RULES)

    def test_respawn_reads(self):  # was: the card's "State lives in files" section
        notes = RULES.split("## NOTE-3")[1].split("##")[0]
        for s in ("notes", "plan", "roster.md", "herdr agent list"):
            self.assertIn(s, notes)

    def test_keeps_model_and_notes_block(self):
        self.assertNotIn("model:", CARD.split("---")[1])  # T9: model and effort live in settings/team-lead.json
        cfg = json.loads((ROOT / "templates/squad/settings/team-lead.json").read_text())
        self.assertEqual((cfg["model"], cfg["effortLevel"]), ("sonnet", "medium"))
        self.assertIn("## START-15 Team Lead start", RULES)
        self.assertIn("## NOTE-1 Notes file", RULES)

    def test_party_to_dispute_does_not_settle_it(self):
        self.assertIn("When you are yourself a party to such a dispute, do not settle it", RULES)

    def test_summary_names_passed_sha_and_checkers(self):
        self.assertIn("each task's final passed sha, the checkers that passed it and the returns per task", RULES)


if __name__ == "__main__":
    unittest.main()
