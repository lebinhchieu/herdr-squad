"""Suite rules: the size's owner runs the full suite once on the final sha (S Developer, M QA whitebox, L Tech Lead); checked on the SUITE rules."""
import itertools
import unittest

from rulesview import ROOT, acts, composed

import squadrules as _sr
RULES = _sr.load_rules(str(ROOT / 'templates/squad/process'), str(ROOT))[0]


class SuiteRulesTest(unittest.TestCase):

    def test_the_size_owner_runs_it_and_others_never(self):
        self.assertIn("Only the Tech Lead runs the full suite.", composed("tech-lead", "L"))
        self.assertIn("the full suite is the Tech Lead's", composed("dev", "L"))
        self.assertIn("the full suite is QA whitebox's", composed("dev", "M"))
        self.assertIn("You run the full suite for the scope, once, on the final sha", composed("qa-whitebox", "M"))
        self.assertIn("never run the suite", composed("qa-blackbox", "M"))
        self.assertIn("then the full suite once on your final sha", composed("dev", "S"))
        self.assertEqual(acts("SUITE-3", "suite-owner = tech-lead"), ("tech-lead",))
        self.assertEqual(acts("SUITE-3b", "suite-owner = qa-white"), ("qa-whitebox",))
        self.assertEqual(acts("SUITE-3", "suite-owner = qa-white"), ())

    def test_every_suite_owner_value_has_a_rule(self):
        for key, rid, role in (("dev", "SUITE-2d", "dev"), ("qa-white", "SUITE-1b", "qa-whitebox"), ("tech-lead", "SUITE-1", "tech-lead")):
            self.assertEqual(acts(rid, f"suite-owner = {key}"), (role,), (rid, key))
            for other in {"dev", "qa-white", "tech-lead"} - {key}:
                self.assertEqual(acts(rid, f"suite-owner = {other}"), (), (rid, other))

    def test_the_suite_owner_follows_the_team_chain(self):
        """suite-owner = tech-lead > qa-white > dev: the owner's rule composes for the owner and the Developer names it."""
        for team, owner, dev_line in (("tech-lead, qa-white, qa-black", "tech-lead", "the full suite is the Tech Lead's"),
                                      ("qa-white, qa-black", "qa-whitebox", "the full suite is QA whitebox's"),
                                      ("team-lead, qa-black", "dev", "then the full suite once on your final sha")):
            self.assertIn(dev_line, composed("dev", team=team), team)
        self.assertIn("Only the Tech Lead runs the full suite.", composed("tech-lead", team="tech-lead"))
        self.assertNotIn("You run the full suite for the scope", composed("qa-whitebox", team="tech-lead, qa-white"))
        self.assertIn("You run the full suite for the scope", composed("qa-whitebox", team="qa-white"))
        self.assertIn("QA whitebox owns the full suite", composed("qa-blackbox", team="qa-white, qa-black"))
        self.assertIn("the full suite is the Tech Lead's", composed("qa-whitebox", team="tech-lead, qa-white"))

    def test_qa_blackbox_gets_a_suites_rule_on_every_team_with_a_dev_owner(self):  # SUITE-2f, over the 128 teams
        import squadrules as sr
        keys = sr.TEAM_KEYS
        n = 0
        for k in range(len(keys) + 1):
            for team in itertools.combinations(keys, k):
                facts = sr.team_facts(list(team))
                if "qa-black" not in team:
                    continue
                n += 1
                owner = facts.get("suite-owner")
                got = [r for r in ("SUITE-2e", "SUITE-2f", "SUITE-2b") if sr.matches(next(x.when for x in RULES if x.id == r), facts)]
                want = {"dev": ["SUITE-2f"], "qa-white": ["SUITE-2e"], "tech-lead": ["SUITE-2b"]}[owner]
                self.assertEqual(got, want, (team, owner))
        self.assertEqual(n, 64)
        self.assertIn("the Developer owns the full suite", composed("qa-blackbox", team="qa-black"))
        self.assertNotIn("SUITE-2f", composed("qa-blackbox", team="qa-black, qa-white").split(" rules: ", 1)[1].split(" ## ", 1)[0])


if __name__ == "__main__":
    unittest.main()
