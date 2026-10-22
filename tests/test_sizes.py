"""Ticket 17 (slice 1): S = Manager + Developers, M = + both QAs, L = every role. Rules in sizes, who, starting
and spawning. The whole-template orphan-duty checks land in ticket 31."""
import re
import unittest

from rulesview import ROOT, acts, composed, run, who

PRESENT = {"S": {"manager", "dev"}, "M": {"manager", "dev", "qa-whitebox", "qa-blackbox"},
           "L": {"manager", "dev", "qa-whitebox", "qa-blackbox", "ba", "team-lead", "tech-lead"}}
ONLY_L = ("ba", "team-lead", "tech-lead")
# duty -> {size: (rule id, role that acts on it)}
OWNERS = {
    "plan and Developer spawning": {"S": ("SIZE-6a", "manager"), "M": ("SIZE-6a", "manager"), "L": ("SIZE-6b", "team-lead")},
    "Developer spawning (cap)": {"S": ("START-2a", "manager"), "M": ("START-2a", "manager"), "L": ("START-2b", "team-lead")},
    "Developer briefing (design notes, AC)": {"S": ("SIZE-6c", "manager"), "M": ("SIZE-6d", "manager")},
    "technical AC": {"S": ("SIZE-6c", "manager"), "M": ("SIZE-23b", "qa-whitebox"), "L": ("REV-7", "tech-lead")},
    "business AC": {"S": ("SIZE-5a", "manager"), "M": ("SIZE-5c", "qa-blackbox"), "L": ("SIZE-5b", "ba")},
    "code check": {"S": ("SIZE-7a", "manager"), "M": ("SIZE-7b", "qa-whitebox"), "L": ("SIZE-7b", "qa-whitebox")},
    "behaviour check": {"S": ("SIZE-8a", "manager"), "M": ("SIZE-8b", "qa-blackbox"), "L": ("SIZE-8b", "qa-blackbox")},
    "disputes": {"S": ("WHO-8a", "manager"), "M": ("WHO-8a", "manager"), "L": ("WHO-8c", "team-lead")},
    "health checks": {"S": ("SPAWN-10a", "manager"), "M": ("SPAWN-10a", "manager"), "L": ("SPAWN-10b", "manager")},
    "promotion": {"S": ("WHO-2b", "manager"), "M": ("WHO-2b", "manager"), "L": ("WHO-2c", "tech-lead")},
    # slice 2 (ticket 29)
    "hand-in": {"S": ("REV-13a", "dev"), "M": ("REV-13b", "dev"), "L": ("REV-13b", "dev")},
    "hand-in confirmation": {"S": ("REV-1", "manager"), "M": ("REV-9", "qa-blackbox"), "L": ("REV-9", "qa-blackbox")},
    "done is told to": {"S": ("LC-20a", "dev"), "M": ("LC-20c", "dev"), "L": ("LC-20b", "dev")},
    "full suite": {"S": ("SUITE-2d", "dev"), "M": ("SUITE-1b", "qa-whitebox"), "L": ("SUITE-1", "tech-lead")},
    "promote.md": {"S": ("PROMO-3b", "manager"), "M": ("SIZE-24b", "qa-whitebox"), "L": ("PROMO-2", "tech-lead")},
    "evidence commit check": {"S": ("REV-1", "manager"), "M": ("EVID-2e", "manager"), "L": ("EVID-2c", "tech-lead")},
    "three returns": {"S": ("LC-7a", "manager"), "M": ("LC-7c", "manager"), "L": ("LC-7b", "team-lead")},
}
SLICE2 = ("review", "evidence", "suites", "promotion", "lifecycle")
# rules of slice 2 that still act on a role absent at S or M, with the reason
EXCEPTIONS = {
    "LC-25": "advisor when stuck acts on every role (ticket 18, pinned by test_advisor_rules); the absent roles read it only if they exist",
    "LC-26": "irreversible-choice advisor rule acts on manager, tech-lead (ticket 18, pinned by test_advisor_rules)",
    "LC-23": "the Designer is present at any size when design = yes",
}


class DutyOwners(unittest.TestCase):
    def test_named_owner_acts_at_its_size(self):
        for duty, by_size in OWNERS.items():
            for size, (rid, role) in by_size.items():
                with self.subTest(duty=duty, size=size):
                    self.assertIn(role, acts(rid, size))
                    self.assertIn(role, PRESENT[size], "owner is absent at this size")

    def test_rules_of_this_slice_never_act_on_an_absent_role(self):
        ids = ("SIZE-1", "SIZE-3", "SIZE-4", "SIZE-5a", "SIZE-5b", "SIZE-5c", "SIZE-6a", "SIZE-6b", "SIZE-6c", "SIZE-6d",
               "SIZE-7a", "SIZE-7b", "SIZE-8a", "SIZE-8b", "SIZE-10a", "SIZE-10b", "SIZE-11a", "SIZE-11b",
               "SIZE-13", "SIZE-14", "SIZE-15", "SIZE-16", "SIZE-21a", "SIZE-21b", "SIZE-23b",
               "WHO-1a", "WHO-1b", "WHO-2", "WHO-2d", "WHO-2b", "WHO-2c", "WHO-3a", "WHO-3b", "WHO-8a", "WHO-8b", "WHO-8c",
               "START-2a", "START-2b", "START-2c", "START-2d",
               "SPAWN-2a", "SPAWN-2b", "SPAWN-2c", "SPAWN-5a", "SPAWN-5b", "SPAWN-8a", "SPAWN-8b", "SPAWN-9", "SPAWN-10a", "SPAWN-10b")
        for rid in ids:
            for size in "SML":
                with self.subTest(rule=rid, size=size):
                    absent = set(acts(rid, size)) - PRESENT[size]
                    self.assertFalse(absent, f"{rid} acts on {absent} at {size}")

    def test_l_only_roles_act_nowhere_else_on_slice_rules(self):
        for rid in ("SIZE-6b", "SIZE-5b", "SIZE-11b", "START-2b", "START-2c", "START-2d", "WHO-1b", "WHO-2", "WHO-8c", "SPAWN-5b", "SPAWN-9", "SPAWN-10b"):
            for size in "SM":
                with self.subTest(rule=rid, size=size):
                    self.assertEqual(acts(rid, size), ())

    def test_manager_variant_of_every_team_lead_duty_at_s_and_m(self):
        for rid in ("SIZE-6a", "START-2a", "WHO-1a", "WHO-3a", "WHO-8a", "SPAWN-5a", "SPAWN-8a", "SPAWN-10a"):
            for size in "SM":
                with self.subTest(rule=rid, size=size):
                    self.assertIn("manager", acts(rid, size))
            self.assertNotIn("manager", acts(rid, "L") if rid in ("SPAWN-5a", "SPAWN-8a") else ("x",))


def slice2_ids():
    out = []
    for f in SLICE2:
        out += re.findall(r"(?m)^## ([A-Z]+-\d+[a-z]?) ", (ROOT / "templates" / "squad" / "process" / f"{f}.md").read_text(encoding="utf-8"))
    return out


def present(size, qab):
    roles = set(PRESENT[size])
    if qab == "no":
        roles.discard("qa-blackbox")
    return roles


class Slice2Owners(unittest.TestCase):
    def test_no_rule_of_the_five_files_acts_on_an_absent_role(self):
        """Lists every orphan: a rule that acts on a role absent at S or M, minus the reasoned EXCEPTIONS."""
        bad = []
        for rid in slice2_ids():
            if rid in EXCEPTIONS:
                continue
            out = run("who", rid).stdout
            for size in "SM":
                for qab in ("yes", "no"):
                    for line in out.splitlines():
                        m = re.match(rf"{size} qa-b {qab}: acts: (.*?); aware: ", line)
                        if m and m.group(1).strip() != "-":
                            absent = [a.strip() for a in m.group(1).split(",") if a.strip() not in present(size, qab)]
                            if absent:
                                bad.append(f"{rid} at {size} qa-b {qab}: {absent}")
        self.assertEqual(sorted(set(bad)), [])

    def test_the_old_orphan_list_is_fixed(self):
        for rid, size in (("REV-1", "S"), ("REV-5a", "S"), ("PROMO-3b", "S"), ("SUITE-3", "S"), ("SUITE-4", "S"), ("SUITE-5", "S"),
                          ("LC-22b", "S"), ("EVID-3a", "S"), ("EVID-5", "S"), ("PROMO-3a", "S"), ("PROMO-3a", "M")):
            with self.subTest(rule=rid, size=size):
                self.assertFalse(set(acts(rid, size)) - PRESENT[size], (rid, size))
        self.assertEqual(acts("REV-1", "S"), ("manager",))
        self.assertEqual(acts("REV-5a", "S"), ("dev",))
        self.assertEqual(acts("EVID-3a", "S"), ("manager",))
        self.assertEqual(acts("EVID-5", "S"), ("dev",))
        for rid in ("SUITE-3", "SUITE-4", "SUITE-5", "LC-22b", "PROMO-3a"):
            self.assertEqual(acts(rid, "S"), ())
            self.assertEqual(acts(rid, "M"), ())

    def test_move_up_exceptions_are_the_listed_ids(self):
        self.assertEqual(sorted(EXCEPTIONS), ["LC-23", "LC-25", "LC-26"])

    def test_hand_in_goes_to_the_manager_at_s_and_the_qas_at_m_and_l(self):
        s, m, l = composed("dev", "S"), composed("dev", "M"), composed("dev", "L")
        self.assertIn("to the Manager.", s.split("## REV-13a")[1].split("##")[0])
        self.assertIn("to QA whitebox and QA blackbox", m)
        self.assertIn("to QA whitebox and QA blackbox", l)
        self.assertIn("Tell the Manager and wait", m)
        self.assertIn("Tell the Manager and wait", s)
        self.assertIn("Tell the Team Lead and wait", l)
        for text in (s, m):
            self.assertNotIn("Tech Lead", text.split("## REV-13a")[1].split("## EVID")[0] if "## REV-13a" in text else "")

    def test_rev_21_has_no_ba_at_m(self):
        self.assertNotIn("ba", acts("REV-21", "M") + acts("REV-21", "S"))
        self.assertEqual(acts("REV-21b", "M"), ("qa-whitebox",))
        self.assertIn("ba", acts("REV-21", "L"))

    def test_rev_2_migration_step_is_l_only(self):
        self.assertNotIn("Tech Lead", composed("qa-whitebox", "M").split("## REV-2 ")[1].split(" ## ")[0])
        self.assertNotIn("## REV-2b", composed("qa-whitebox", "M"))
        self.assertIn("## REV-2b", composed("qa-whitebox", "L"))

    def test_claude_md_running_tests_names_the_size_owner(self):
        text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("S the Developer, M QA whitebox, L the Tech Lead", text)


class S_DeveloperReview(unittest.TestCase):
    def test_review_rule_reaches_composed_dev_at_s_only(self):
        s = composed("dev", "S")
        self.assertIn("## REV-22", s)
        for needle in ("fresh-context Opus review subagent", "`## Review`", "squad-evidence check"):
            self.assertIn(needle, s.split("## REV-22")[1].split(" ## ")[0])
        for size in "ML":
            self.assertNotIn("REV-22", composed("dev", size))
        self.assertEqual(acts("REV-22", "S"), ("dev",))
        self.assertEqual(acts("REV-22", "M"), ())

    def test_manager_confirms_behaviour_and_review_at_s(self):
        t = composed("manager", "S")
        self.assertIn("`## Behaviour` and `## Review` ([REV-22])", t)
        self.assertIn("## EVID-3a", t)

    def test_dev_rules_stay_within_5_kib(self):
        from test_dev_rules_size import COMBOS, LIMIT, compose
        for size, design, goal in COMBOS:
            self.assertLessEqual(len(compose("dev", size, design, goal)), LIMIT, (size, design, goal))


class RespawnReadable(unittest.TestCase):
    def test_l_business_ac_owner_with_and_without_qa_blackbox(self):
        # qa-b yes: SIZE-5b; qa-b no: REV-21 (the BA alone). Either way the BA owns it at L.
        self.assertIn("ba", acts("SIZE-5b", "L"))
        self.assertIn("ba", acts("REV-21", "L"))
        self.assertEqual(acts("REV-21", "S"), ())

    def test_duties_line_is_written_into_the_task_file(self):
        # a respawned Developer reads the task file, not the first prompt; the dev rules are at their size cap
        sm, mm = composed("manager", "S"), composed("manager", "M")
        for text, need in ((sm, ("start each task file with `Duties:`", "technical AC are yours", "`promote.md`", "BLOCKED <task>", "user-visible change")),
                           (mm, ("start each task file with `Duties:`", "technical AC are QA whitebox's", "BLOCKED <task>"))):
            for n in need:
                self.assertIn(n, text)
        self.assertNotIn("Duties:", composed("dev", "S"))
        self.assertNotIn("user-visible change or business doubt", mm.split("SIZE-6d")[1].split("##")[0])


class SizeRules(unittest.TestCase):
    def test_size_table(self):
        m = composed("manager", "S")
        self.assertIn("| **S** Quick fix | Manager, Developers |", m)
        self.assertIn("| **M** Feature | + QA whitebox, QA blackbox |", m)
        self.assertIn("| **L** Full pod | Every role: + BA, Team Lead, Tech Lead |", m)

    def test_every_risk_flag_forces_l(self):
        for size in "SM":
            t = composed("manager", size)
            self.assertIn("Every risk flag forces L", t)
            self.assertNotIn("force at least M", t)
        self.assertIn("DB migration or data change", composed("manager", "S"))

    def test_business_doubt_moves_s_and_m_to_l(self):
        self.assertIn("A business doubt moves the scope to L", composed("manager", "S"))
        self.assertIn("A business doubt moves the scope to L", composed("manager", "M"))
        self.assertIn("`BLOCKED <task>` ([SIZE-14])", composed("manager", "S"))
        self.assertIn("a business doubt or risk flag moves it to L", composed("manager", "S"))

    def test_manager_plans_and_spawns_in_s_and_m_not_l(self):
        for size in "SM":
            m = composed("manager", size)
            self.assertIn("## SIZE-6a Plan owner, S and M", m)
            self.assertIn("## SPAWN-5a", m)
        self.assertNotIn("## SIZE-6a", composed("manager", "L"))
        self.assertIn("## SIZE-6b", composed("team-lead", "L"))

    def test_developers_write_design_notes_in_the_task_file(self):
        for size in "SM":
            self.assertIn("put design notes in the task file", composed("manager", size))

    def test_s_dev_rules_name_the_review_and_duty_table_has_every_duty(self):
        t = composed("manager", "S")
        for row in ("Full suite | Developer | QA whitebox | Tech Lead", "`promote.md` | Developer | QA whitebox |",
                    "Code check | Developer + Opus review subagent", "Technical AC | Developer | QA whitebox with the Developer",
                    "Migration, contract change, risk flag, business doubt | Manager moves to L"):
            self.assertIn(row, t)

    def test_m_has_no_ba_team_lead_or_tech_lead_text(self):
        m = composed("manager", "M")
        for name in ("The Team Lead owns the plan", "Tech Lead tells the Manager"):
            self.assertNotIn(name, m)
        self.assertEqual(who("START-2d")["M"][0], ())


if __name__ == "__main__":
    unittest.main()
