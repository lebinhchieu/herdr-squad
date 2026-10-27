"""Team vocabulary of squadrules (drop-scope-size 01): DUTIES, resolve_duties, legacy_team, parse_team, ROLE_KEY, lint of keys."""
import itertools
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402

# Expected owners of today's S, M, L, copied from the BASE text (git show 2949573:templates/squad/process/sizes.md):
# SIZE-22 lines 269-282 (table rows, one per duty; the `Code check` S cell "Developer + Sonnet review subagent" is
# confirmed by the Manager, the `promote.md` L cell "Tech Lead, BA" gives the technical part to the Tech Lead,
# "Migration, contract change, risk flag, business doubt" is risk-owner and doubt-owner); SIZE-22a lines 291-295
# (with an Architect: Irreversible design choice = Architect for every size). SIZE-20 line 249 (qa-b no: QA whitebox
# alone checks the Developer's `## Behaviour`). Written out by hand, not derived from DUTIES.
#                  plan      notes   tech-ac    biz-ac   code       behaviour  handin     suite      promote    risk       doubt      choice
OLD = {
    "S": ("manager", "dev", "dev", "ticket", "manager", "manager", "manager", "dev", "dev", "manager", "manager", "manager"),
    "M": ("manager", "dev", "qa-white", "ticket", "qa-white", "qa-black", "qas", "qa-white", "qa-white", "manager", "manager", "manager"),
    "L": ("team-lead", "tech-lead", "tech-lead", "ba", "qa-white", "qa-black", "qas", "tech-lead", "tech-lead", "tech-lead", "ba", "tech-lead"),
}
OLD_FACTS = ("plan-owner", "design-notes", "tech-ac", "business-ac", "code-check", "behaviour-check", "handin-target",
             "suite-owner", "promote-owner", "risk-owner", "doubt-owner", "choice-owner")


def old_owners(size, qa_b="yes", design="no", architecture="no"):
    row = dict(zip(OLD_FACTS, OLD[size]))
    if qa_b == "no" and size in ("M", "L"):  # SIZE-20
        row["behaviour-check"] = "qa-white"
    if architecture == "yes":  # SIZE-22a
        row["choice-owner"] = "architect"
    return row


class Equivalence(unittest.TestCase):
    def check(self, size, qa_b="yes", design="no", architecture="no"):
        team = sr.legacy_team(size, qa_b, design, architecture)
        got = sr.resolve_duties(team)
        for fact, want in old_owners(size, qa_b, design, architecture).items():
            self.assertEqual(got[fact], want, f"{size} qa-b={qa_b} design={design} arch={architecture}: {fact}")

    def test_today_s_m_l(self):
        for size in "SML":
            with self.subTest(size=size):
                self.check(size)

    def test_qa_b_no(self):
        for size in "ML":
            with self.subTest(size=size):
                self.check(size, qa_b="no")

    def test_architecture_yes(self):
        for size in "SML":
            with self.subTest(size=size):
                self.check(size, architecture="yes")

    def test_design_yes(self):
        for size in "SML":
            with self.subTest(size=size):
                self.check(size, design="yes")

    def test_built_ui_check_follows_spec_rule_3(self):
        """spec rule 3: QA blackbox, else the Manager confirms the Developer's screenshots (new row, not in SIZE-22)."""
        self.assertEqual(sr.resolve_duties(["designer", "qa-white", "qa-black"])["ui-check"], "qa-black")
        self.assertEqual(sr.resolve_duties(["designer", "qa-white"])["ui-check"], "manager")
        self.assertEqual(sr.resolve_duties(["designer"])["ui-check"], "manager")

    def test_the_six_named_shapes(self):
        shapes = {"S": [], "M": ["qa-white", "qa-black"], "L": ["ba", "team-lead", "tech-lead", "qa-white", "qa-black"],
                  "Lnoqb": ["ba", "team-lead", "tech-lead", "qa-white"], "Mdesign": ["qa-white", "qa-black", "designer"],
                  "March": ["qa-white", "qa-black", "architect"]}
        self.assertEqual(sr.legacy_team("S"), shapes["S"])
        self.assertEqual(sr.legacy_team("M"), shapes["M"])
        self.assertEqual(sr.legacy_team("L"), shapes["L"])
        self.assertEqual(sr.legacy_team("L", "no"), shapes["Lnoqb"])
        self.assertEqual(sr.legacy_team("M", "yes", "yes"), shapes["Mdesign"])
        self.assertEqual(sr.legacy_team("M", "yes", "no", "yes"), shapes["March"])


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

    def test_resolve_is_pure_and_takes_any_iterable(self):
        before = dict(sr.DUTIES)
        a = sr.resolve_duties(frozenset({"ba"}))
        self.assertEqual(a, sr.resolve_duties(["ba"]))
        self.assertEqual(sr.DUTIES, before)

    def test_decided_team_has_no_missing_fact(self):
        new = set(sr.PRESENCE_KEY.values()) | set(sr.DUTIES)
        for team in ([], list(sr.TEAM_KEYS), ["qa-black"]):
            facts = sr.team_facts(team)
            self.assertEqual(set(facts), new)
            for key, value in facts.items():
                self.assertIn(value, sr.WHEN_KEYS[key])
        self.assertEqual(sr.team_facts(["designer"])["design"], "yes")
        self.assertEqual(sr.team_facts(["designer"])["architecture"], "no")
        self.assertEqual(sr.team_facts([])["qa-black"], "no")

    def test_new_when_keys_are_the_presence_keys_and_duties(self):
        for key in ("ba", "team-lead", "tech-lead", "qa-white", "qa-black"):
            self.assertEqual(sr.WHEN_KEYS[key], ("yes", "no"))
        for fact in sr.DUTIES:
            self.assertIn(fact, sr.WHEN_KEYS)
        self.assertEqual(sr.WHEN_KEYS["behaviour-check"], ("qa-black", "qa-white", "manager"))
        self.assertIn("qa-b", sr.WHEN_KEYS)  # stays until the cutover task
        self.assertIn("size", sr.WHEN_KEYS)

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


# Real lines from this machine's squads (the value after `size:` / `qa-b:`), paths under /home/chieule/workspace/.
# Blank `size:` is squad/templates/scope/scope.md:7 (the template line every new scope starts from).
# `size: M — signals ...` of svgdraw does not exist in any scope.md on this machine (only the `L —` line), so it is not used.
SAMPLES = {
    # squad/.claude/squads/plugin/scopes/squad-close/scope.md:7 (also _done/coachwait-closelocal/scope.md:11)
    "M-confirmed": "M (confirmed by PO 2026-10-23)",
    "L": "L",
    # plugin-bk261023 scopes/_done/refine-process/scope.md:7
    "refine": "M, custom pod (PO 2026-10-14): Tech Lead, BA, QA whitebox, Devs; no QA blackbox. Behaviour check: Dev saves evidence "
              "(dev-evidence.md, migration run on a copy of a real squad), QA whitebox checks it. Done = QA whitebox PASS (+ BA sign-off "
              "on the process.md rule audit). Signals: 4-5 tasks, one repo, no UI, changes the contract every squad reads",
    # plugin-bk261023 scopes/_done/extractor-role/scope.md:8
    "extractor": "M (PO confirmed 2026-10-17, no QA roles) - signals: research spike gates a build of ~4-5 tasks; new role every squad "
                 "sees (role instructions + process.md change need PO approval); one repo; no DB/API risk flag",
    # enhanced-markdown-vscode/.claude/squads/blueprint/scopes/_done/svgdraw/scope.md:7 (design: yes is line 9)
    "svgdraw": "L — confirmed by PO (E1 a). Signals: AI-authored SVG in webview = security flag; form is a business question; "
               "user-visible; touches skills/, syntaxes/, validate.mjs",
    # squad/.claude/squads/plugin/scopes/squad-close/scope.md:9
    "qab-no": "no  (task 03 only changes tests/fixtures; nothing a person using the product observes; PO confirmed 2026-10-23)",
}


class LegacyTeam(unittest.TestCase):
    def test_real_samples(self):
        self.assertEqual(sr.legacy_team(SAMPLES["M-confirmed"]), ["qa-white", "qa-black"])
        self.assertEqual(sr.legacy_team(SAMPLES["L"]), ["ba", "team-lead", "tech-lead", "qa-white", "qa-black"])
        self.assertEqual(sr.legacy_team(SAMPLES["svgdraw"], design="yes"), ["ba", "team-lead", "tech-lead", "qa-white", "qa-black", "designer"])
        # enhanced-markdown-vscode/.claude/squads/blueprint/scopes/grillui/scope.md:7-10: size: M, qa: full, qa-b: yes, design: yes
        self.assertEqual(sr.legacy_team("M", "yes", "yes"), ["qa-white", "qa-black", "designer"])

    def test_blank_size_is_undecided_even_with_flags(self):
        """Blank `size:` (squad/templates/scope/scope.md:7) with `qa-b: no  (task 03 ...)` (squad-close scope.md:9): the idle case."""
        self.assertIsNone(sr.legacy_team("", SAMPLES["qab-no"]))
        self.assertIsNone(sr.legacy_team("", "yes", "yes", "yes"))
        self.assertIsNone(sr.legacy_team(None))
        self.assertIsNone(sr.legacy_team("   "))

    def test_qa_b_no_with_commentary(self):
        self.assertEqual(sr.legacy_team("M", SAMPLES["qab-no"]), ["qa-white"])
        self.assertEqual(sr.legacy_team("L", SAMPLES["qab-no"]), ["ba", "team-lead", "tech-lead", "qa-white"])

    def test_commentary_that_contradicts_the_mapping_is_not_applied(self):
        """First token only: `custom pod`, `no QA roles` still map to plain M; the converter flags them (ticket 02)."""
        self.assertEqual(sr.legacy_team(SAMPLES["refine"]), ["qa-white", "qa-black"])
        self.assertEqual(sr.legacy_team(SAMPLES["extractor"]), ["qa-white", "qa-black"])

    def test_design_yes_with_qa_b_no_is_a_valid_team(self):
        self.assertEqual(sr.legacy_team("M", "no", "yes"), ["qa-white", "designer"])
        self.assertEqual(sr.legacy_team("S", "yes", "yes"), ["designer"])
        self.assertEqual(sr.legacy_team("S", "yes", "no", "yes"), ["architect"])

    def test_size_s_ignores_qa_b(self):
        self.assertEqual(sr.legacy_team("S", "yes"), [])
        self.assertEqual(sr.legacy_team("S", "no"), [])

    def test_first_token_vs_read_home_anywhere(self):
        """legacy_team takes the FIRST token (architecture section 7); base read_home takes `\\b[SML]\\b` anywhere."""
        text = "confirmed M by PO"
        self.assertIsNone(sr.legacy_team(text))
        with tempfile.TemporaryDirectory() as home:
            Path(home, "scope.md").write_text(f"# s\nsize: {text}\n", encoding="utf-8")
            self.assertEqual(sc.read_home(home)["facts"]["size"], "M")

    def test_bad_flag_value_raises(self):
        with self.assertRaises(ValueError):
            sr.legacy_team("M", "maybe")
        with self.assertRaises(ValueError):
            sr.legacy_team("M", "yes", "perhaps")

    def test_output_is_in_team_keys_order(self):
        for size, qb, d, a in itertools.product("SML", ("yes", "no"), ("yes", "no"), ("yes", "no")):
            team = sr.legacy_team(size, qb, d, a)
            self.assertEqual(team, [t for t in sr.TEAM_KEYS if t in team])

    def test_qa_none_line_does_not_reach_legacy_team(self):
        """`qa: none (PO ...)` (extractor-role) is not an input of legacy_team; the size sample alone maps."""
        self.assertEqual(sr.legacy_team(SAMPLES["extractor"], "yes", "no"), ["qa-white", "qa-black"])


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

    def test_old_language_still_lints_until_the_cutover(self):
        self.assertEqual(lint_rule("size = L and qa-b = yes"), [])
        self.assertEqual(lint_rule("size in M, L and qa-b = no"), [])
        self.assertEqual(lint_rule("size = M and architecture = yes"), [])

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


class ChangelogV9(unittest.TestCase):
    def test_empty_v9_block_exists_with_the_four_headings(self):
        text = (ROOT / "skills" / "squad-process-update" / "changelog.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("## v9"))
        head = text.split("## v8")[0]
        for h in ("added:", "changed:", "removed:", "retargeted:"):
            self.assertIn(h, head)


if __name__ == "__main__":
    unittest.main()
