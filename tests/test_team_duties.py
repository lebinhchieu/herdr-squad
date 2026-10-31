"""Team vocabulary of squadrules (drop-scope-size 01): DUTIES, resolve_duties, parse_team, ROLE_KEY, lint of keys."""
import itertools
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadrules as sr  # noqa: E402

class Sweep(unittest.TestCase):
    def test_all_128_sets_have_one_present_owner_per_duty(self):
        n = 0
        for r in range(8):
            for combo in itertools.combinations(sr.TEAM_KEYS, r):
                n += 1
                got = sr.resolve_duties(combo)
                self.assertEqual(set(got), set(sr.DUTIES), combo)
                for fact, owner in got.items():
                    ok = owner in ("manager", "dev", "ticket") or owner in combo \
                        or (owner == "qas" and ("qa-white" in combo or "qa-black" in combo))
                    self.assertTrue(ok, f"{combo}: {fact} -> {owner} is not present")
        self.assertEqual(n, 128)

    def test_thirteen_duties_every_chain_ends_at_manager_dev_or_ticket(self):
        self.assertEqual(len(sr.DUTIES), 13)
        for fact, chain in sr.DUTIES.items():
            self.assertIn(chain[-1], ("manager", "dev", "ticket"), fact)

    def test_new_when_keys_are_the_presence_keys_and_duties(self):
        for key in ("ba", "team-lead", "tech-lead", "qa-white", "qa-black"):
            self.assertEqual(sr.WHEN_KEYS[key], ("yes", "no"))
        for fact in sr.DUTIES:
            self.assertIn(fact, sr.WHEN_KEYS)
        self.assertEqual(sr.WHEN_KEYS["behaviour-check"], ("qa-black", "qa-white", "manager"))
        for gone in ("qa-b", "size", "qa-whitebox"):  # the old language is gone (ticket 12)
            self.assertNotIn(gone, sr.WHEN_KEYS)

    def test_matches_with_duty_keys(self):
        facts = sr.team_facts(["ba", "qa-black"])
        self.assertTrue(sr.matches("business-ac = ba and qa-black = yes", facts))
        self.assertFalse(sr.matches("business-ac = ticket", facts))
        self.assertTrue(sr.matches("handin-target in qas, team-lead", facts))
        with self.assertRaises(ValueError):
            sr.matches("business-ac = qa-black", facts)


class RoleKey(unittest.TestCase):
    def test_maps_both_and_no_other(self):
        self.assertEqual(sr.ROLE_KEY, {"qa-whitebox": "qa-white", "qa-blackbox": "qa-black"})
        for role in sr.ROLES:
            self.assertEqual(sr.role_key(role), sr.ROLE_KEY.get(role, role))
        self.assertEqual(sr.role_key("qa-whitebox"), "qa-white")
        self.assertEqual(sr.role_key("designer"), "designer")
        with self.assertRaises(ValueError):
            sr.role_key("qa-white")

    def test_team_keys_are_the_seven_optional_roles(self):
        self.assertEqual(len(sr.TEAM_KEYS), 7)
        self.assertEqual({sr.role_key(r) for r in sr.ROLES} - set(sr.IMPLICIT_ROLES), set(sr.TEAM_KEYS))


class ParseTeam(unittest.TestCase):
    def test_edge_cases(self):
        self.assertIsNone(sr.parse_team(""))
        self.assertIsNone(sr.parse_team("   "))
        self.assertIsNone(sr.parse_team(None))
        self.assertIsNone(sr.parse_team("  (waiting for the PO)"))
        self.assertEqual(sr.parse_team("none"), [])
        self.assertEqual(sr.parse_team("none  (confirmed minimal)"), [])
        self.assertEqual(sr.parse_team("qa-white, ba  (PO 2026-10-27, no QA blackbox)"), ["ba", "qa-white"])
        self.assertEqual(sr.parse_team("architect,designer,qa-black,qa-white,tech-lead,team-lead,ba"), list(sr.TEAM_KEYS))

    def test_crlf_value(self):
        self.assertEqual(sr.parse_team("qa-white, qa-black\r"), ["qa-white", "qa-black"])
        self.assertEqual(sr.parse_team("none\r"), [])
        self.assertIsNone(sr.parse_team("\r"))

    def test_errors_carry_the_where(self):
        for value, needle in (("ba, ba", "twice"), ("ba, wizard", "unknown team token 'wizard'"),
                              ("manager, ba", "always on the team"), ("dev", "always on the team"),
                              ("token-coach", "always on the team")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    sr.parse_team(value, "scope.md:7")
                self.assertTrue(str(cm.exception).startswith("scope.md:7:"), str(cm.exception))
                self.assertIn(needle, str(cm.exception))

    def test_role_names_are_not_tokens(self):
        for role, token in (("qa-whitebox", "qa-white"), ("qa-blackbox", "qa-black")):
            with self.assertRaises(ValueError) as cm:
                sr.parse_team(f"ba, {role}", "scope.md:3")
            self.assertIn(token, str(cm.exception))
            self.assertIn(role, str(cm.exception))

    def test_none_mixed_with_roles_is_unknown_token(self):
        with self.assertRaises(ValueError):
            sr.parse_team("none, ba")

    def test_hostile_values_stay_data(self):
        for value in ("qa-white; touch X", "$(touch X)", "`touch X`", "ba && rm -rf /"):
            with self.assertRaises(ValueError):
                sr.parse_team(value)


def lint_rule(when, rid="TEAM-1"):
    text = f"## {rid} Title\nroles: manager\nwhen: {when}\ntopic: teams\n\nBody.\n"
    problems = []
    rules = sr.parse_rule_file(text, "templates/squad/process/teams.md", problems)
    sr._structure(rules, [], problems)
    return problems


class LintWhen(unittest.TestCase):
    def test_duty_plus_orthogonal_passes(self):
        self.assertEqual(lint_rule("business-ac = ba and qa-black = yes"), [])
        self.assertEqual(lint_rule("code-check = qa-white and goal = no and qa = full and design = yes and architecture = no"), [])
        self.assertEqual(lint_rule("qa-black = yes and design = yes"), [])
        self.assertEqual(lint_rule("handin-target in qas, team-lead"), [])
        self.assertEqual(lint_rule("ba = yes"), [])

    def test_two_duty_keys_fail_naming_the_rule(self):
        out = lint_rule("business-ac = ba and code-check = qa-white", "TEAM-7")
        self.assertEqual(len(out), 1, out)
        self.assertIn("TEAM-7", out[0])
        self.assertIn("business-ac", out[0])
        self.assertIn("code-check", out[0])

    def test_duty_and_role_key_fail(self):
        self.assertEqual(len(lint_rule("tech-ac = tech-lead and ba = yes")), 1)
        self.assertEqual(len(lint_rule("ba = yes and tech-lead = yes")), 1)

    def test_new_key_with_old_key_fails(self):
        for when in ("business-ac = ba and size = L", "ba = yes and qa-b = yes"):
            out = lint_rule(when)
            self.assertEqual(len(out), 1, (when, out))

    def test_old_language_is_a_lint_error(self):
        for when in ("size = L and qa-b = yes", "size in M, L and qa-b = no", "size = M and architecture = yes",
                     "qa-whitebox = yes"):
            out = lint_rule(when)
            self.assertEqual(len(out), 1, (when, out))
            self.assertIn("is gone", out[0])

    def test_value_outside_the_key_set_fails(self):
        self.assertTrue(lint_rule("business-ac = qa-black"))
        self.assertTrue(lint_rule("ba = maybe"))
        self.assertTrue(lint_rule("qa-black = qa-white"))
        self.assertTrue(lint_rule("wizard = yes"))

    def test_overlay_ops_are_linted_too(self):
        text = "## add SQ-1 Local\nroles: manager\nwhen: business-ac = ba and code-check = qa-white\ntopic: x\n\nBody text.\n"
        problems = []
        ops = sr.parse_overlay(text, "process.local.md", problems)
        out = sr._lint_ops(ops, {})
        self.assertTrue(any("SQ-1" in line and "business-ac" in line for line in out), out)

    def test_team_file_stem_is_known(self):
        self.assertIn(("TEAM", "teams"), sr.FILE_ORDER)
        self.assertLess(sr.FILE_ORDER.index(("SIZE", "sizes")), sr.FILE_ORDER.index(("TEAM", "teams")))
        self.assertIn("TEAM", sr.PREFIXES)


if __name__ == "__main__":
    unittest.main()
