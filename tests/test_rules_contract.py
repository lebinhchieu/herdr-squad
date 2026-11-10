"""Rule contract: which roles a rule acts on or reaches, per team facts (`squad-process who`, `rules:` of a composed file).
One home for the small per-ticket files it replaces (advisor, pod, retro, suite, task id, designer, team lead, contact routes)."""
import itertools
import unittest

from rulesview import ROLES, ROOT, acts, composed, rule_ids

import squadrules as sr  # noqa: E402 (rulesview puts bin/ on sys.path)

ALL = {r for r in ROLES if r != "token-coach"}
RULES = sr.load_rules(str(ROOT / "templates/squad/process"), str(ROOT))[0]
BY_ID = {r.id: r for r in RULES}
CARD = (ROOT / "agents/team-lead.md").read_text()
TL, MG = "team-lead, qa-white", "qa-white"


class WhoActsTest(unittest.TestCase):
    """Rows `rule, key -> acting roles` (from advisor, pod, retro, suite, designer, team-lead tests)."""

    def test_who_shows_the_acting_roles(self):
        for rid, key, want in (
                ("LC-26", "S", ("manager", "tech-lead")), ("LC-26", "M", ("manager", "tech-lead")), ("LC-26", "L", ("manager", "tech-lead")),
                ("MSG-5", "plan-owner = manager", ()),
                ("SIZE-6a", "S", None),  # manager must be among them
                ("LC-15", "plan-owner = team-lead", ("team-lead",)), ("LC-15", "plan-owner = manager", ()),
                ("LC-17b", "plan-owner = manager", ("manager",)),
                ("ITER-13", "S", ("token-coach",)), ("ITER-13", "M", ("token-coach",)), ("ITER-13", "L", ("token-coach",)),
                ("ITER-14", "S", ("token-coach",)), ("ITER-14", "M", ("token-coach",)), ("ITER-14", "L", ("token-coach",)),
                ("ITER-15", "S", ("manager",)), ("ITER-15", "M", ("manager",)), ("ITER-15", "L", ("manager",)),
                ("ITER-16", "S", ("manager",)), ("ITER-16", "M", ("manager",)), ("ITER-16", "L", ("manager",)),
                ("SUITE-3", "suite-owner = tech-lead", ("tech-lead",)), ("SUITE-3b", "suite-owner = qa-white", ("qa-whitebox",)),
                ("SUITE-3", "suite-owner = qa-white", ()),
                ("SPAWN-9", "L", ("team-lead",)),
                ):
            with self.subTest(rid=rid, key=key):
                if want is None:
                    self.assertIn("manager", acts(rid, key))
                else:
                    self.assertEqual(acts(rid, key), want)
        for size in "SML":
            self.assertEqual(set(acts("LC-25", size)), ALL)
        self.assertIn("team-lead", acts("MSG-5", "plan-owner = team-lead"))
        self.assertIn("tech-lead", acts("LC-11", "L"))
        self.assertIn("manager", acts("LC-11b", "M"))
        self.assertIn("team-lead", acts("SIZE-17b", "L"))

    def test_task_id_rule_reaches_every_role_and_size(self):
        for size in "SML":
            self.assertEqual(len(acts("MSG-3", size)), 9 if size != "S" else len(acts("MSG-3", "S")))

    def test_every_suite_owner_value_has_a_rule(self):
        for key, rid, role in (("dev", "SUITE-2d", "dev"), ("qa-white", "SUITE-1b", "qa-whitebox"), ("tech-lead", "SUITE-1", "tech-lead")):
            self.assertEqual(acts(rid, f"suite-owner = {key}"), (role,), (rid, key))
            for other in {"dev", "qa-white", "tech-lead"} - {key}:
                self.assertEqual(acts(rid, f"suite-owner = {other}"), (), (rid, other))


class ComposedRulesTest(unittest.TestCase):
    """Rows `team -> rule IDs a role composes` (suite, contact routes, team lead)."""

    def test_the_suite_owner_follows_the_team_chain(self):
        """suite-owner = tech-lead > qa-white > dev: the owner's rule composes for the owner and the Developer names it."""
        for team, dev_line in (("tech-lead, qa-white, qa-black", "the full suite is the Tech Lead's"),
                               ("qa-white, qa-black", "the full suite is QA whitebox's"),
                               ("team-lead, qa-black", "then once on your final sha")):
            self.assertIn(dev_line, composed("dev", team=team), team)
        self.assertIn("Only the Tech Lead runs the full suite.", composed("tech-lead", team="tech-lead"))
        self.assertNotIn("You own the full suite for the scope", composed("qa-whitebox", team="tech-lead, qa-white"))
        self.assertIn("You own the full suite for the scope", composed("qa-whitebox", team="qa-white"))
        self.assertIn("QA whitebox owns the full suite", composed("qa-blackbox", team="qa-white, qa-black"))
        self.assertIn("the full suite is the Tech Lead's", composed("qa-whitebox", team="tech-lead, qa-white"))

    def test_the_size_owner_runs_it_and_others_never(self):
        self.assertIn("Only the Tech Lead runs the full suite.", composed("tech-lead", "L"))
        self.assertIn("the full suite is the Tech Lead's", composed("dev", "L"))
        self.assertIn("the full suite is QA whitebox's", composed("dev", "M"))
        self.assertIn("You own the full suite for the scope", composed("qa-whitebox", "M"))
        self.assertIn("never run the suite", composed("qa-blackbox", "M"))
        self.assertIn("then once on your final sha", composed("dev", "S"))

    def test_qa_blackbox_gets_a_suites_rule_on_every_team_with_a_dev_owner(self):  # SUITE-2f, over the 128 teams
        n = 0
        for k in range(len(sr.TEAM_KEYS) + 1):
            for team in itertools.combinations(sr.TEAM_KEYS, k):
                facts = sr.team_facts(list(team))
                if "qa-black" not in team:
                    continue
                n += 1
                got = [r for r in ("SUITE-2e", "SUITE-2f", "SUITE-2b") if sr.matches(BY_ID[r].when, facts)]
                want = {"dev": ["SUITE-2f"], "qa-white": ["SUITE-2e"], "tech-lead": ["SUITE-2b"]}[facts.get("suite-owner")]
                self.assertEqual(got, want, (team, facts.get("suite-owner")))
        self.assertEqual(n, 64)
        self.assertIn("the Developer owns the full suite", composed("qa-blackbox", team="qa-black"))
        self.assertNotIn("SUITE-2f", composed("qa-blackbox", team="qa-black, qa-white").split(" rules: ", 1)[1].split(" ## ", 1)[0])

    def test_routes_follow_the_plan_owner_of_the_team(self):  # team language: plan-owner, doubt-owner, design-notes
        tl = TL
        self.assertIn("MSG-11b", rule_ids(composed("dev", team=tl)))
        self.assertNotIn("MSG-11a", rule_ids(composed("dev", team=tl)))
        self.assertIn("MSG-11a", rule_ids(composed("dev", team=MG)))
        self.assertNotIn("MSG-11b", rule_ids(composed("dev", team=MG)))
        self.assertIn("go to the Team Lead", composed("dev", team=tl))
        self.assertIn("go to the Manager", composed("dev", team=MG))
        self.assertIn("MSG-5", rule_ids(composed("team-lead", team=tl)))
        self.assertIn("MSG-6", rule_ids(composed("team-lead", team=tl)))
        self.assertIn("MSG-14", rule_ids(composed("tech-lead", team="tech-lead")))  # the Tech Lead answers gaps whoever plans
        self.assertIn("MSG-15", rule_ids(composed("tech-lead", team="tech-lead, ba")))
        self.assertNotIn("MSG-15", rule_ids(composed("tech-lead", team="tech-lead")))  # no BA to raise to
        self.assertIn("MSG-12", rule_ids(composed("ba", team="ba")))

    def test_doubts_go_to_the_doubt_owner(self):
        self.assertIn("MSG-16b", rule_ids(composed("designer", team="ba, designer")))
        self.assertNotIn("MSG-16a", rule_ids(composed("designer", team="ba, designer")))
        self.assertIn("MSG-16a", rule_ids(composed("designer", team="designer")))
        self.assertIn("MSG-20b", rule_ids(composed("architect", team="ba, architect")))
        self.assertIn("MSG-20a", rule_ids(composed("architect", team="architect")))
        self.assertIn("MSG-17", rule_ids(composed("designer", team="tech-lead, designer")))  # design-notes = tech-lead
        self.assertIn("MSG-17b", rule_ids(composed("designer", team="designer")))  # design-notes = dev
        a = composed("architect", team="architect")
        self.assertNotIn("moves the scope", a)
        self.assertNotIn("the BA", a.split("## MSG-20a")[1].split("##")[0])

    def test_team_lead_exists_when_the_team_lists_it_and_takes_the_handover(self):
        self.assertIn("lists `team-lead`", CARD)  # 06: no size in the card
        self.assertIn("## Handover", composed("team-lead", "L"))

    def test_team_lead_spawns_and_retires_dev_only(self):
        rules = composed("team-lead", "L")
        self.assertIn("squad-spawn dev", rules)
        self.assertIn("squad-retire", rules)
        self.assertIn("no", rules.split("## SPAWN-9")[1].split("##")[0].lower())

    def test_spawning_cost_and_safety_follow_the_team(self):  # spawning.md, cost.md, safety.md in the team language
        tl = "team-lead, tech-lead, qa-white, qa-black"
        self.assertIn("SPAWN-2b", rule_ids(composed("manager", team=tl)))
        self.assertIn("SPAWN-2c", rule_ids(composed("manager", team=tl)))
        self.assertNotIn("SPAWN-2a", rule_ids(composed("manager", team=tl)))
        self.assertIn("SPAWN-2a", rule_ids(composed("manager", team=MG)))
        self.assertNotIn("SPAWN-2b", rule_ids(composed("manager", team=MG)))
        self.assertIn("every other role on `team:`", composed("manager", team=MG))
        self.assertNotIn("SPAWN-5b", rule_ids(composed("manager", team=tl)))
        self.assertIn("SPAWN-5b", rule_ids(composed("team-lead", team=tl)))
        self.assertIn("SPAWN-9", rule_ids(composed("team-lead", team=tl)))
        self.assertIn("SPAWN-4", rule_ids(composed("manager", team="designer")))
        self.assertNotIn("SPAWN-4", rule_ids(composed("manager", team=MG)))
        self.assertIn("SPAWN-4a", rule_ids(composed("manager", team="architect")))
        self.assertIn("COST-5", rule_ids(composed("dev", team=tl)))
        self.assertIn("COST-5a", rule_ids(composed("dev", team=MG)))
        self.assertIn("COST-4a", rule_ids(composed("tech-lead", team="tech-lead")))
        self.assertIn("COST-6b", rule_ids(composed("team-lead", team=tl)))
        self.assertIn("COST-6a", rule_ids(composed("manager", team=MG)))
        self.assertIn("SAFE-9", rule_ids(composed("qa-whitebox", team=MG)))  # no `when:`: composed for the role that is on the team
        self.assertIn("SAFE-10", rule_ids(composed("qa-blackbox", team="qa-black")))

    def test_spawning_cost_and_safety_files_have_no_size_word(self):  # G4: no size word, no S/M/L tier, no qa-b in these rule files
        for f in ("messages", "cost", "suites", "spawning", "safety"):
            text = (ROOT / "templates/squad/process" / f"{f}.md").read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?i)\bsize\b(?!-\d)", f)
            self.assertNotRegex(text, r"\bqa-b\b", f)
            self.assertNotRegex(text, r"(?m)^when:.*\b(?:S|M|L)\b", f)

    def test_tech_lead_without_team_lead_respawns_per_cost_4c(self):  # over the 128 teams
        n = 0
        for k in range(len(sr.TEAM_KEYS) + 1):
            for team in itertools.combinations(sr.TEAM_KEYS, k):
                facts = sr.team_facts(list(team))
                if "tech-lead" not in team:
                    continue
                n += 1
                got = [i for i in ("COST-4b", "COST-4c") if sr.matches(BY_ID[i].when, facts)]
                self.assertEqual(got, ["COST-4b", "COST-4c"] if "team-lead" in team else ["COST-4c"], team)  # accepted: both for a Tech Lead with a Team Lead
        self.assertEqual(n, 64)
        self.assertIn("Respawn once your design and AC are in files.", composed("tech-lead", team="tech-lead"))
        self.assertIn("COST-4c", rule_ids(composed("tech-lead", team="tech-lead, team-lead")))


if __name__ == "__main__":
    unittest.main()


class PhaseContractTest(unittest.TestCase):
    """Ticket 10, live (no snapshot): only the Manager loses rules, exactly those with a `phase:`; a must-have list stays."""
    import squadcompose as sc
    MUST_ATTACH = {"manager": ("MRG-1", "CLOSE-1", "ITER-6"), "tech-lead": ("CLOSE-3a",), "dev": ("LC-3a", "LC-25")}
    SHAPES = {"none": ((), "no"), "qas": (("qa-white", "qa-black"), "no"),
              "tech-qas": (("tech-lead", "qa-white", "qa-black"), "no"),
              "team-lead": (("team-lead", "tech-lead", "qa-white", "qa-black"), "no"),
              "full": (("ba", "team-lead", "tech-lead", "qa-white", "qa-black", "designer", "architect"), "no"),
              "goal": (("team-lead", "tech-lead", "qa-white", "qa-black"), "yes")}

    def test_phase_rules_are_the_only_difference_and_only_for_their_acting_role(self):
        sc = self.sc
        rules = sc.load_rules(str(ROOT), None)[0]
        for shape, (team, goal) in self.SHAPES.items():
            facts = {**sr.team_facts(list(team)), "goal": goal, "qa": "full"}
            for role in ROLES:
                with self.subTest(shape=shape, role=role):
                    full = {e.id for e in sc.attached(rules, role, facts, with_phases=True)}
                    got = {e.id for e in sc.attached(rules, role, facts)}
                    want = {e.id for e in sc.choose(rules, role, facts) if e.phase and "manager" in e.roles}
                    self.assertEqual(full - got, want)
                    if role != "manager":
                        self.assertEqual(full, got)
                    for rid in self.MUST_ATTACH.get(role, ()):
                        if any(e.id == rid for e in sc.choose(rules, role, facts)):
                            self.assertIn(rid, got)
        for rid in ("MRG-1", "CLOSE-1", "ITER-6"):
            self.assertFalse(BY_ID[rid].phase)
        for r in RULES:
            if r.phase:
                self.assertEqual(r.roles, ["manager"], r.id)
