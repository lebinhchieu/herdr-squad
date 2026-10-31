"""The team model of the process files: sizes.md and teams.md rules act on present roles for every team, `who` lists the
acting roles per duty value, pointers resolve, and each role composes the rules it must own (ticket 10b cut the S/M/L era)."""
import itertools
import re
import sys
import unittest
from pathlib import Path

from rulesview import ROOT, composed, who

sys.path.insert(0, str(ROOT / "bin"))
import squadrules as sr  # noqa: E402

PDIR = sr.process_dir(str(ROOT))
MY_FILES = ("sizes.md", "teams.md")
ALL_TEAMS = [frozenset(c) for n in range(8) for c in itertools.combinations(sr.TEAM_KEYS, n)]
# Done rules are broadcast to every pod role of the team: their `roles:` may list a role this team lacks (nobody acts for it)
DONE_BROADCAST = {"SIZE-2", "TEAM-1", "TEAM-2", "TEAM-3"}


def my_rules():
    rules, tombs, errs = sr.load_rules(PDIR, str(ROOT))
    return [r for r in rules if Path(r.file).name in MY_FILES], tombs


def present_roles(team):
    return {"manager", "dev", "token-coach"} | {r for r in sr.ROLES if sr.ROLE_KEY.get(r, r) in team}


class TeamRules(unittest.TestCase):
    def test_no_rule_of_the_two_files_acts_on_an_absent_role_for_any_of_the_128_teams(self):
        rules, _ = my_rules()
        bad, orphan = set(), set()
        for team in ALL_TEAMS:
            facts, here = sr.team_facts(team), present_roles(team)
            for r in rules:
                if not sr.matches(r.when, facts):
                    continue
                acting = set(r.roles)
                if not acting & here:
                    orphan.add(r.id)
                if r.id not in DONE_BROADCAST and acting - here:
                    bad.add(f"{r.id} acts on {sorted(acting - here)} for team {sorted(team)}")
        self.assertEqual(sorted(bad), [])
        self.assertEqual(sorted(orphan), [])

    def test_who_lists_exactly_the_acting_roles_per_duty_fact_and_value(self):
        rules, _ = my_rules()
        checked = 0
        for r in rules:
            conds = list(sr._conditions(r.when)) if r.when else []
            duty = [(k, v) for k, v in conds if k in sr.DUTIES]
            if not duty:
                continue
            key, values = duty[0]
            lines = who(r.id)
            for value in sr.DUTIES[key]:
                if value == "qas":
                    continue
                want = tuple(r.roles) if value in values else ()
                self.assertEqual(lines[f"{key} = {value}"][0], want, f"{r.id} {key} = {value}")
                checked += 1
        self.assertGreater(checked, 40)

    def test_every_duty_has_a_rule_per_acting_role_in_sizes_md(self):
        rules, _ = my_rules()
        by = {}
        for r in rules:
            for k, vals in (sr._conditions(r.when) if r.when else []):
                if k in sr.DUTIES:
                    by.setdefault(k, set()).update(vals)
        for duty in ("plan-owner", "business-ac", "code-check", "behaviour-check", "ui-check", "doubt-owner", "tech-ac", "promote-owner"):
            self.assertTrue(by.get(duty), duty)
        self.assertEqual(by["business-ac"], {"ticket", "ba"})
        self.assertEqual(by["behaviour-check"], {"manager", "qa-black", "qa-white"})
        self.assertEqual(by["code-check"], {"manager", "qa-white", "tech-lead"})

    def test_text_never_says_size(self):
        for name in MY_FILES:
            text = Path(PDIR, name).read_text(encoding="utf-8")
            hits = re.findall(r"(?i)\bsize\b(?!-\d)", text)
            self.assertEqual(hits, [], name)
        self.assertNotRegex(composed("manager", team="qa-white"), r"(?i)\bsizes?\b(?!-\d)\s+(?:of|S|M|L)\b")

    def test_manager_proposal_has_a_row_for_every_role(self):
        sizes = Path(PDIR, "sizes.md").read_text(encoding="utf-8")
        table = sizes.split("## SIZE-1 ")[1].split("\n## ")[0]
        for role in ("BA", "Tech Lead", "Team Lead", "QA whitebox", "QA blackbox", "Designer", "Architect"):
            self.assertRegex(table, rf"(?m)^\| {role} \|", role)
        for team in ((), ("qa-white", "qa-black"), tuple(sr.TEAM_KEYS)):
            self.assertIn("## SIZE-1 Proposing the team", composed("manager", team=team))

    def test_chain_table_names_every_duty_and_ends_the_chains(self):
        body = Path(PDIR, "sizes.md").read_text(encoding="utf-8").split("## SIZE-22 ")[1].split("\n## ")[0]
        rows = [l for l in body.splitlines() if l.startswith("| ") and not l.startswith(("| Duty", "|---"))]
        self.assertEqual(len(rows), 12)
        for l in rows:
            self.assertRegex(l, r"Manager|Developer|ticket|PO decides")

    def test_every_pointer_to_a_size_rule_in_the_templates_resolves(self):
        rules, tombs, _ = sr.load_rules(PDIR, str(ROOT))
        ids = {r.id for r in rules}
        for f in Path(PDIR).glob("*.md"):
            for cited in re.findall(r"\[(SIZE-\d+[a-z]?|TEAM-\d+[a-z]?)\]", f.read_text(encoding="utf-8")):
                self.assertIn(cited, ids, f"{f.name} cites {cited}")


# The net: one composed-per-role structure test. A rule dropped from a role, or sent to another role, fails here by ID.
# IDs only, no sentences. The team has every optional role, so every role composes its full set.
FULL_TEAM = "ba, team-lead, tech-lead, qa-white, qa-black, designer, architect"
ROLE_NET = {
    "manager": "SIZE-1 SIZE-22 START-3 START-18 WHO-5 WHO-6 WHO-8 MSG-1 MSG-2 LC-1 REV-15 EVID-1 PROMO-1 CLOSE-1 SPAWN-1 SPAWN-4 MRG-1 SAFE-1b",
    "team-lead": "SIZE-6b START-2b START-15 WHO-3b WHO-8c LC-2 LC-7b REV-3 EVID-3b COST-4b SPAWN-5b SPAWN-8b",
    "tech-lead": "SIZE-23d START-16 WHO-2 WHO-2c PROMO-2 LC-8 REV-4 REV-7 EVID-2c SUITE-1 SUITE-3 COST-4c",
    "qa-whitebox": "SIZE-7b SIZE-23c START-14 PROMO-8 LC-3b REV-2 REV-3 REV-7 REV-10 REV-17 SUITE-2b SAFE-9",
    "qa-blackbox": "SIZE-8b START-13 LC-3b REV-3 REV-8 REV-9 REV-11 REV-17 SUITE-2b SAFE-10",
    "ba": "SIZE-5b START-11 PROMO-3a WHO-2c WHO-7 REV-8 FILE-1",
    "designer": "SIZE-9 START-12 MSG-16b MSG-17 LC-23 SAFE-8 WHO-4",
    "dev": "START-10 MSG-11b LC-3a LC-18 LC-20b REV-13b REV-14a EVID-2a EVID-2b COST-5 SAFE-1a SAFE-11 SUITE-2a",
    "token-coach": "START-17 ITER-7 ITER-8 ITER-9 ITER-13 ITER-14",
    "architect": "SIZE-9a START-20 WHO-2e MSG-20b",
}
HAS_DUTIES_LINE = ("manager", "team-lead", "tech-lead")


class ComposedPerRole(unittest.TestCase):
    def test_each_role_composes_its_header_duties_line_and_must_own_rule_ids(self):
        for role, ids in ROLE_NET.items():
            with self.subTest(role=role):
                text = composed(role, team=FULL_TEAM)
                self.assertIn(f"role: {role} ", text)
                self.assertEqual("duties: plan-owner=" in text, role in HAS_DUTIES_LINE, f"{role}: duties line")
                have = set(re.findall(r"## ([A-Z]+-[0-9]+[a-z]?) ", text))
                self.assertEqual(sorted(set(ids.split()) - have), [], f"{role} lost rules")


if __name__ == "__main__":
    unittest.main()
