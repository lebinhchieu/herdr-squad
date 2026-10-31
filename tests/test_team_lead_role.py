"""The Team Lead role: identity on the card, duties in the rules attached for M and L."""
import unittest

from rulesview import ROOT, acts, composed

CARD = (ROOT / "agents/team-lead.md").read_text()
RULES = composed("team-lead", "L")


class TeamLeadRoleTest(unittest.TestCase):
    def test_exists_when_the_team_lists_it_and_takes_the_handover(self):
        self.assertIn("lists `team-lead`", CARD)  # 06: no size in the card
        self.assertIn("## Handover", RULES)
        self.assertIn("team-lead", acts("SIZE-17b", "L"))

    def test_spawns_and_retires_dev_only(self):
        self.assertIn("squad-spawn dev", RULES)
        self.assertIn("squad-retire", RULES)
        self.assertEqual(acts("SPAWN-9", "L"), ("team-lead",))
        self.assertIn("no", RULES.split("## SPAWN-9")[1].split("##")[0].lower())

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


if __name__ == "__main__":
    unittest.main()
