"""The Team Lead role: identity on the card, duties in the rules attached for M and L."""
import json
import unittest
from pathlib import Path

from rulesview import ROOT, acts, composed

CARD = (ROOT / "agents/team-lead.md").read_text()
RULES = composed("team-lead", "L")


class TeamLeadRoleTest(unittest.TestCase):
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


    def test_spawning_cost_and_safety_follow_the_team(self):  # spawning.md, cost.md, safety.md in the team language
        def ids(text):
            return text.split(" rules: ", 1)[1].split(" ## ", 1)[0].split()
        tl, mg = "team-lead, tech-lead, qa-white, qa-black", "qa-white"
        self.assertIn("SPAWN-2b", ids(composed("manager", team=tl)))
        self.assertIn("SPAWN-2c", ids(composed("manager", team=tl)))
        self.assertNotIn("SPAWN-2a", ids(composed("manager", team=tl)))
        self.assertIn("SPAWN-2a", ids(composed("manager", team=mg)))
        self.assertNotIn("SPAWN-2b", ids(composed("manager", team=mg)))
        self.assertIn("every other role on `team:`", composed("manager", team=mg))
        self.assertNotIn("SPAWN-5b", ids(composed("manager", team=tl)))
        self.assertIn("SPAWN-5b", ids(composed("team-lead", team=tl)))
        self.assertIn("SPAWN-9", ids(composed("team-lead", team=tl)))
        self.assertIn("SPAWN-4", ids(composed("manager", team="designer")))
        self.assertNotIn("SPAWN-4", ids(composed("manager", team=mg)))
        self.assertIn("SPAWN-4a", ids(composed("manager", team="architect")))
        self.assertIn("COST-5", ids(composed("dev", team=tl)))
        self.assertIn("COST-5a", ids(composed("dev", team=mg)))
        self.assertIn("COST-4a", ids(composed("tech-lead", team="tech-lead")))
        self.assertIn("COST-6b", ids(composed("team-lead", team=tl)))
        self.assertIn("COST-6a", ids(composed("manager", team=mg)))
        self.assertIn("SAFE-9", ids(composed("qa-whitebox", team=mg)))  # no `when:`: composed for the role that is on the team
        self.assertIn("SAFE-10", ids(composed("qa-blackbox", team="qa-black")))
        for f in ("messages", "cost", "suites", "spawning", "safety"):  # G4: no size word, no S/M/L tier, no qa-b in these rule files
            text = (ROOT / "templates/squad/process" / f"{f}.md").read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?i)\bsize\b(?!-\d)", f)
            self.assertNotRegex(text, r"\bqa-b\b", f)
            self.assertNotRegex(text, r"(?m)^when:.*\b(?:S|M|L)\b", f)


    def test_tech_lead_without_team_lead_respawns_per_cost_4c(self):  # over the 128 teams
        import itertools
        import squadrules as sr
        rules = {r.id: r for r in sr.load_rules(str(ROOT / "templates/squad/process"), str(ROOT))[0]}
        n = 0
        for k in range(len(sr.TEAM_KEYS) + 1):
            for team in itertools.combinations(sr.TEAM_KEYS, k):
                facts = sr.team_facts(list(team))
                if "tech-lead" not in team:
                    continue
                n += 1
                got = [i for i in ("COST-4b", "COST-4c") if sr.matches(rules[i].when, facts)]
                self.assertEqual(got, ["COST-4b", "COST-4c"] if "team-lead" in team else ["COST-4c"], team)  # accepted: both for a Tech Lead with a Team Lead
        self.assertEqual(n, 64)
        self.assertIn("Respawn once your design and AC are in files.", composed("tech-lead", team="tech-lead"))
        self.assertIn("COST-4c", composed("tech-lead", team="tech-lead, team-lead").split(" rules: ", 1)[1].split(" ## ", 1)[0])


# Golden from base 6389642 (rules as keyed on size/qa-b): per rule, for the 7 shapes (S; M; M qa-b no; L; L qa-b no; M design; L architecture),
# which of manager ba team-lead tech-lead qa-whitebox qa-blackbox designer architect dev compose it. SPAWN-2a/2b/2c and COST-4c (new, tech-lead = yes) are not here: the old
# per-size spawn lists became one list per plan owner (changelog v9), M and L without qa-b had none.
SHAPES = (("S", "yes", "no", "no"), ("M", "yes", "no", "no"), ("M", "no", "no", "no"), ("L", "yes", "no", "no"),
          ("L", "no", "no", "no"), ("M", "yes", "yes", "no"), ("L", "yes", "no", "yes"))
GOLDEN_ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "architect", "dev")
GOLDEN = {
    "MSG-1": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "MSG-2": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "MSG-3": "100000001 100011001 100010001 111111001 111110001 100011101 111111011",
    "MSG-4a": "100000001 100011001 100010001 000000000 000000000 100011101 000000000",
    "MSG-4b": "000000000 000000000 000000000 111111001 111110001 000000000 111111011",
    "MSG-5": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "MSG-6": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "MSG-7a": "100000000 100011000 100010000 000000000 000000000 100011100 000000000",
    "MSG-7b": "000000000 000000000 000000000 111111000 111110000 000000000 111111010",
    "MSG-8a": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "MSG-8b": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "MSG-9": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "MSG-10": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "MSG-11a": "000000001 000000001 000000001 000000000 000000000 000000001 000000000",
    "MSG-11b": "000000000 000000000 000000000 000000001 000000001 000000000 000000001",
    "MSG-12": "000000000 000000000 000000000 010000000 010000000 000000000 010000000",
    "MSG-13": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "MSG-14": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "MSG-15": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "MSG-16a": "000000000 000000000 000000000 000000000 000000000 000000100 000000000",
    "MSG-16b": "000000000 000000000 000000000 000000000 000000000 000000000 000000000",
    "MSG-17": "000000000 000000000 000000000 000000000 000000000 000000000 000000000",
    "MSG-17b": "000000000 000000000 000000000 000000000 000000000 000000100 000000000",
    "MSG-18": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "MSG-19": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "MSG-20": "000000000 000000000 000000000 000000000 000000000 000000000 101110010",
    "MSG-20a": "000000000 000000000 000000000 000000000 000000000 000000000 000000000",
    "MSG-20b": "000000000 000000000 000000000 000000000 000000000 000000000 000000010",
    "COST-1": "000000000 000011000 000010000 011111000 011110000 000011100 011111010",
    "COST-2": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "COST-3": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "COST-4a": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "COST-4b": "000000000 000000000 000000000 001100000 001100000 000000000 001100000",
    "COST-5": "000000000 000000000 000000000 000000001 000000001 000000000 000000001",
    "COST-5a": "000000001 000000001 000000001 000000000 000000000 000000001 000000000",
    "COST-6a": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "COST-6b": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "COST-7": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "COST-8": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "COST-9": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "COST-10a": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "COST-10b": "000000000 000000000 000000000 101000000 101000000 000000000 101000000",
    "COST-11": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "COST-12": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "COST-13a": "000000000 000011000 000010000 000000000 000000000 000011100 000000000",
    "COST-13b": "000000000 000000000 000000000 011111000 011110000 000000000 011111010",
    "COST-14a": "000000000 000011000 000010000 000000000 000000000 000011100 000000000",
    "COST-14b": "000000000 000000000 000000000 011111000 011110000 000000000 011111010",
    "SUITE-1": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "SUITE-1b": "000000000 000010000 000010000 000000000 000000000 000010000 000000000",
    "SUITE-2a": "000000000 000000000 000000000 000000001 000000001 000000000 000000001",
    "SUITE-2c": "000000000 000000001 000000001 000000000 000000000 000000001 000000000",
    "SUITE-2d": "000000001 000000000 000000000 000000000 000000000 000000000 000000000",
    "SUITE-2b": "000000000 000000000 000000000 000011000 000010000 000000000 000011000",
    "SUITE-2e": "000000000 000001000 000000000 000000000 000000000 000001000 000000000",
    "SUITE-3": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "SUITE-4": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "SUITE-4b": "000000000 000010000 000010000 000000000 000000000 000010000 000000000",
    "SUITE-5": "000000000 000000000 000000000 000100000 000100000 000000000 000100000",
    "SUITE-5b": "000000000 000010000 000010000 000000000 000000000 000010000 000000000",
    "SUITE-3b": "000000000 000010000 000010000 000000000 000000000 000010000 000000000",
    "SUITE-6": "000000000 000000000 000000000 000011000 000010000 000000000 000011000",
    "SUITE-6b": "000000000 000001000 000000000 000000000 000000000 000001000 000000000",
    "SPAWN-1": "100000000 100000000 100000000 101000000 101000000 100000000 101000000",
    "SPAWN-3": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "SPAWN-4": "000000000 000000000 000000000 000000000 000000000 100000000 000000000",
    "SPAWN-4a": "000000000 000000000 000000000 000000000 000000000 000000000 100000000",
    "SPAWN-5a": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "SPAWN-5b": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "SPAWN-6": "100000000 100000000 100000000 101000000 101000000 100000000 101000000",
    "SPAWN-7": "100000000 100000000 100000000 101000000 101000000 100000000 101000000",
    "SPAWN-8a": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "SPAWN-8b": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "SPAWN-9": "000000000 000000000 000000000 001000000 001000000 000000000 001000000",
    "SPAWN-10a": "100000000 100000000 100000000 000000000 000000000 100000000 000000000",
    "SPAWN-10b": "000000000 000000000 000000000 100000000 100000000 000000000 100000000",
    "SPAWN-11": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "SAFE-1a": "000000001 000000001 000000001 000000001 000000001 000000001 000000001",
    "SAFE-1b": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "SAFE-2": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "SAFE-3": "100000001 100011001 100010001 111111001 111110001 100011101 111111011",
    "SAFE-4": "100000001 100011001 100010001 111111001 111110001 100011101 111111011",
    "SAFE-5": "100000000 100011000 100010000 111111000 111110000 100011100 111111010",
    "SAFE-6": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "SAFE-7": "100000000 100000000 100000000 100000000 100000000 100000000 100000000",
    "SAFE-8": "000000000 000000000 000000000 000000000 000000000 000000100 000000000",
    "SAFE-9": "000000000 000010000 000010000 000010000 000010000 000010000 000010000",
    "SAFE-10": "000000000 000001000 000000000 000001000 000000000 000001000 000001000",
    "SAFE-11": "000000001 000011001 000010001 000011001 000010001 000011001 000011001",
}


class SameRolesAsBase(unittest.TestCase):
    def test_every_rule_of_the_five_files_reaches_the_same_roles_in_the_7_shapes(self):  # AC 9 on rule level
        import squadcompose as sc
        import squadrules as sr
        rules = {r.id: r for r in sc.load_rules(str(ROOT), None)[0]}
        for rid, want in GOLDEN.items():
            r = rules[rid]
            got = []
            for size, qab, design, arch in SHAPES:
                team = sr.legacy_team(size, qab, design, arch)
                facts = sr.team_facts(team)
                facts.update(qa="full", goal="no")
                present = {"manager", "dev"} | {{"qa-white": "qa-whitebox", "qa-black": "qa-blackbox"}.get(k, k) for k in team}
                on = sr.matches(r.when, facts)
                got.append("".join("1" if on and (x in r.roles or "all" in r.roles) and x in present else "0" for x in GOLDEN_ROLES))
            with self.subTest(rule=rid):
                self.assertEqual(" ".join(got), want)


if __name__ == "__main__":
    unittest.main()
