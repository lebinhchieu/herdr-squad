"""Ticket 17 (slice 1): S = Manager + Developers, M = + both QAs, L = every role. Rules in sizes, who, starting
and spawning. The whole-template orphan-duty checks land in ticket 31."""
import re
import sys
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
    "done is told to": {"S": ("LC-20a", "dev"), "M": ("LC-20a", "dev"), "L": ("LC-20b", "dev")},
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
    "REV-2b": "acts for QA whitebox when the Tech Lead owns risk; a `when:` holds one role or duty key, so the QA's presence is the role itself",
    "REV-3b": "acts for the QAs when no Tech Lead is on the team; same one-key limit",
    "REV-21b": "acts for QA whitebox when the ticket is the business AC; same one-key limit",
}


class DutyOwners(unittest.TestCase):
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


SLICE3 = ("cost", "messages", "files", "iterations", "notes", "goal", "closing", "safety", "core")
# not size-bound: the Token Coach is spawned by the Manager at any size (ITER-6a/6b); the Designer and the Architect are present at any size
# when design = yes / architecture = yes (rules for it carry that `when`, or are universal)
ANY_SIZE = {"token-coach", "designer", "architect"}
# slice-3 rules that may act on an absent role, with the reason
EXCEPTIONS3 = {
    "FILE-11": "drafts rule: acts on every role present; the absent roles are listed so it still reaches them on move up",
}


def slice3_ids():
    out = []
    for f in SLICE3:
        out += re.findall(r"(?m)^## ([A-Z]+-\d+[a-z]?) ", (ROOT / "templates" / "squad" / "process" / f"{f}.md").read_text(encoding="utf-8"))
    return out


class Slice3Owners(unittest.TestCase):
    def test_no_rule_of_the_slice_3_files_is_orphaned(self):
        """who-orphan = no present role acts on the rule at that size / qa-b value. Lists every one."""
        bad = []
        for rid in slice3_ids():
            if rid in EXCEPTIONS3:
                continue
            for line in run("who", rid).stdout.splitlines():
                m = re.match(r"([SM])(?: qa-b (yes|no))?: acts: (.*?); aware: ", line)
                if not m or m.group(3).strip() in ("-", "all"):
                    continue
                size, qab = m.group(1), m.group(2) or "yes"
                acting = {a.strip() for a in m.group(3).split(",")}
                if not acting & (present(size, qab) | ANY_SIZE):
                    bad.append(f"{rid} at {size} qa-b {qab}: acts only on {sorted(acting)}")
        self.maxDiff = None
        self.assertEqual(sorted(set(bad)), [])

    def test_rules_retargeted_in_30_act_on_the_right_roles(self):
        for rid, size, role in (("COST-6a", "M", "manager"), ("COST-10a", "M", "manager"), ("MSG-4a", "M", "manager"),
                                ("MSG-7a", "M", "manager"), ("MSG-17b", "S", "designer"), ("FILE-5a", "M", "manager"),
                                ("ITER-3b", "M", "manager"), ("GOAL-3c", "S", "manager"), ("GOAL-6d", "M", "manager"),
                                ("CLOSE-3c", "M", "manager"), ("FILE-8", "M", "manager")):
            with self.subTest(rule=rid, size=size):
                self.assertIn(role, acts(rid, size))
        for rid in ("COST-4a", "COST-4b", "COST-6b", "COST-10b", "COST-13b", "COST-14b", "MSG-4b", "MSG-5", "MSG-6", "MSG-8b",
                    "MSG-12", "MSG-13", "MSG-14", "MSG-15", "MSG-19", "ITER-3", "NOTE-3", "FILE-5c", "GOAL-3a", "GOAL-6a", "CLOSE-3a"):
            for size in "SM":
                with self.subTest(rule=rid, size=size):
                    self.assertFalse(set(acts(rid, size)) - {"manager"}, f"{rid} at {size} acts on {acts(rid, size)}")

    def test_composed_dev_and_qas_name_no_absent_role_at_s_and_m(self):
        for size in "SM":
            for role in ("dev", "qa-whitebox", "qa-blackbox"):
                if role != "dev" and size == "S":
                    continue
                for design, goal in (("no", "no"), ("yes", "yes")):
                    t = composed(role, size, design, goal)
                    with self.subTest(role=role, size=size, design=design, goal=goal):
                        for name in ("Tech Lead", "Team Lead", "the BA"):
                            self.assertNotIn(name, t, f"{role} at {size} names {name}")

    def test_files_table_owners_follow_the_sizes(self):
        t = composed("manager", "M")
        self.assertIn("Plan owner (Manager at S and M, Team Lead at L)", t)
        self.assertIn("Developer at S, QA whitebox at M, Tech Lead at L", t)
        self.assertNotIn("Tech Lead in S", t)

    def test_msg3_never_paste_in_composed_dev(self):
        for size in "SML":
            self.assertIn("never paste", composed("dev", size))


class Slice2Owners(unittest.TestCase):
    def test_no_rule_of_the_five_files_acts_on_an_absent_role(self):
        """Lists every orphan: a rule that matches a team (all 128 sets) on which none of its acting roles is present,
        minus the reasoned EXCEPTIONS."""
        import itertools
        sys.path.insert(0, str(ROOT / "bin"))
        import squadrules as sr
        import squadcompose as sc
        rules = sc.load_rules(str(ROOT), None)[0]
        mine = {r.id: r for r in rules if r.id.split("-")[0] in ("LC", "REV", "EVID")}  # the other slice-2 files migrate in their own tasks
        always = {"manager", "dev", "token-coach"}
        bad = []
        for n in range(len(sr.TEAM_KEYS) + 1):
            for team in itertools.combinations(sr.TEAM_KEYS, n):
                facts = sr.team_facts(list(team))
                present = always | {{"qa-white": "qa-whitebox", "qa-black": "qa-blackbox"}.get(t, t) for t in team}
                for rid, r in mine.items():
                    if rid in EXCEPTIONS or "all" in r.roles or not sr.matches(r.when, facts):
                        continue
                    if not set(r.roles) & present:
                        bad.append(f"{rid} on {', '.join(team) or 'none'}: acts only on {sorted(r.roles)}")
        self.assertEqual(sorted(set(bad)), [])

    def test_pointers_of_dev_rules_at_s_reach_a_present_role(self):
        """A [ID] pointer in a rule the S Developer acts on must name a rule someone present acts on at S."""
        bad = []
        for f in SLICE2:
            text = (ROOT / "templates" / "squad" / "process" / f"{f}.md").read_text(encoding="utf-8")
            for rid, body in re.findall(r"(?ms)^## ([A-Z]+-\d+[a-z]?) [^\n]*\n(.*?)(?=^## |\Z)", text):
                if "dev" not in acts(rid, "S"):
                    continue
                for target in set(re.findall(r"\[([A-Z]+-\d+[a-z]?)\]", body)):
                    if not set(acts(target, "S")) & PRESENT["S"]:
                        bad.append(f"{rid} -> {target}")
        self.assertEqual(sorted(bad), [])


class S_DeveloperReview(unittest.TestCase):
    def test_review_rule_reaches_composed_dev_at_s_only(self):
        s = composed("dev", "S")
        self.assertIn("## REV-22", s)
        body = s.split("## REV-22")[1].split(" ## ")[0]
        for needle in ("fresh-context review subagent", "`model: sonnet`", "`effort: high`", "`## Review`", "squad-evidence check"):
            self.assertIn(needle, body)
        self.assertNotIn("Opus", body)
        for size in "ML":
            self.assertNotIn("REV-22", composed("dev", size))
        self.assertEqual(acts("REV-22", "qa-white = no"), ("dev",))
        self.assertEqual(acts("REV-22", "qa-white = yes"), ())

    def test_s_dev_gets_the_suite_run_and_receipt_how_to(self):
        s = composed("dev", "S")
        body = s.split("## SUITE-2d")[1].split("\n## ")[0]
        for needle in ("pgrep -f", "never restart", "receipt"):
            self.assertIn(needle, body)
        for size in "ML":
            self.assertNotIn("## SUITE-2d", composed("dev", size))

    def test_manager_confirms_behaviour_and_review_at_s(self):
        t = composed("manager", "S")
        self.assertIn("`## Behaviour` and `## Review` ([REV-22])", t)
        self.assertIn("## EVID-3a", t)

    @unittest.skip("5 KiB trim is ticket 11")
    def test_dev_rules_stay_within_5_kib(self):
        from test_dev_rules_size import COMBOS, LIMIT, compose
        for size, design, goal in COMBOS:
            self.assertLessEqual(len(compose("dev", size, design, goal)), LIMIT, (size, design, goal))


class RespawnReadable(unittest.TestCase):
    def test_l_business_ac_owner_with_and_without_qa_blackbox(self):
        # qa-b yes: SIZE-5b; qa-b no: REV-21 (the BA alone). Either way the BA owns it at L.
        self.assertIn("ba", acts("SIZE-5b", "business-ac = ba"))
        self.assertIn("ba", acts("REV-21", "business-ac = ba"))
        self.assertEqual(acts("REV-21", "business-ac = ticket"), ())

class SizeRules(unittest.TestCase):
    def test_m_has_no_ba_team_lead_or_tech_lead_text(self):
        m = composed("manager", "M")
        for name in ("The Team Lead owns the plan", "Tech Lead tells the Manager"):
            self.assertNotIn(name, m)
        self.assertEqual(who("START-2d")["M"][0], ())


# ---- ticket 31: whole-template checks -------------------------------------------------------------------------
ALL_FILES = sorted((ROOT / "templates" / "squad" / "process").glob("*.md"))
# rules that act on no present role at S or M, or name an absent role as actor; by ID, with the reason
# (tech-ac.md follow-up list: only SIZE-17a-e, LC-23/25/26, move-up rules and the six role start cards)
ORPHAN_ALLOWED = {
    **{f"SIZE-17{c}": "join on move up: acts on the role that arrives when the scope moves up" for c in "abcde"},
    **{rid: "role start card; role absent at this size, rule never composed" for rid in
       ("START-8", "START-11", "START-13", "START-14", "START-15", "START-16")},
}
# composed manager text (outside tables and the index) that names an absent role
ABSENT_NAME_ALLOWED = {}   # none: SIZE-18 is `when: size = L`, SPAWN-4 says "the plan" (DECISION 31)
# duty -> sizes need an owner row in OWNERS
REQUIRED_DUTIES = ("plan and Developer spawning", "technical AC", "business AC", "code check", "behaviour check", "full suite",
                   "promote.md", "migration, contract change", "irreversible choice", "hand-in")


def all_ids():
    out = []
    for f in ALL_FILES:
        if f.name != "_removed.md":
            out += re.findall(r"(?m)^## ([A-Z]+-\d+[a-z]?) ", f.read_text(encoding="utf-8"))
    return out


class WholeTemplate(unittest.TestCase):
    def test_allow_list_is_only_what_the_follow_up_list_names(self):
        for rid, why in ORPHAN_ALLOWED.items():
            self.assertTrue(why)
            self.assertTrue(rid.startswith("SIZE-17") or rid.startswith("START-"), rid)
        self.assertEqual(sorted(k for k in ORPHAN_ALLOWED if k.startswith("START-")),
                         ["START-11", "START-13", "START-14", "START-15", "START-16", "START-8"])

    def test_allowed_orphans_really_are_orphans(self):
        """A stale allow-list entry hides nothing: each still acts on no present role at some size."""
        for rid in ORPHAN_ALLOWED:
            hit = False
            for size, (acting, _) in who(rid).items():
                if size in "SM" and acting and not set(acting) & (PRESENT[size] | ANY_SIZE):
                    hit = True
            self.assertTrue(hit, f"{rid} is no longer an orphan: drop it from ORPHAN_ALLOWED")

    def test_dev_and_qas_name_no_absent_role_at_s_and_m(self):
        for size in "SM":
            for role in ("dev", "qa-whitebox", "qa-blackbox"):
                if size == "S" and role != "dev":
                    continue
                for design, goal in (("no", "no"), ("yes", "yes")):
                    t = composed(role, size, design, goal).split("## Index of other rules")[0]
                    for name in ("Tech Lead", "Team Lead", "the BA"):
                        with self.subTest(role=role, size=size, name=name):
                            self.assertNotIn(name, t)

    def test_every_duty_has_an_owner_per_size(self):
        pairs = {"plan and Developer spawning": "plan and Developer spawning", "technical AC": "technical AC",
                 "business AC": "business AC", "code check": "code check", "behaviour check": "behaviour check",
                 "full suite": "full suite", "promote.md": "promote.md", "hand-in": "hand-in"}
        for duty in pairs:
            self.assertIn(duty, OWNERS)
            for size in "SML":
                self.assertIn(size, OWNERS[duty], f"{duty} has no owner at {size}")

    def test_the_orphan_check_catches_an_orphan(self):
        """Mutation: a rule acting only on an absent role is reported by the same parser."""
        line = "S: acts: tech-lead; aware: -"
        m = re.match(r"([SM])(?: qa-b (yes|no))?: acts: (.*?); aware: ", line)
        acting = {a.strip() for a in m.group(3).split(",")}
        self.assertFalse(acting & (present("S", "yes") | ANY_SIZE))


BASE = "2e81e5e"


def rules_at(rev=None):
    """{rule id: text} of every process rule file, at a git revision or in the working tree."""
    import subprocess
    out = {}
    for f in ALL_FILES:
        if f.name == "_removed.md":
            continue  # tombstones are not rules; a removed ID must be absent from `new`
        if rev:
            r = subprocess.run(["git", "show", f"{rev}:templates/squad/process/{f.name}"], cwd=ROOT, capture_output=True, encoding="utf-8")
            text = r.stdout if r.returncode == 0 else ""
        else:
            text = f.read_text(encoding="utf-8")
        for part in re.split(r"(?m)^(?=## [A-Z]+-\d+[a-z]? )", text):
            m = re.match(r"## ([A-Z]+-\d+[a-z]?) ", part)
            if m:
                out[m.group(1)] = part.strip()
    return out


class Changelog(unittest.TestCase):
    def test_every_changed_added_or_removed_rule_id_is_in_the_v7_entry(self):
        import subprocess
        if subprocess.run(["git", "cat-file", "-e", BASE], cwd=ROOT, capture_output=True).returncode:
            self.skipTest(f"base {BASE} not in this clone")
        old, new = rules_at(BASE), rules_at()
        diff = {i for i in set(old) | set(new) if old.get(i) != new.get(i)}
        text = (ROOT / "skills" / "squad-process-update" / "changelog.md").read_text(encoding="utf-8")
        entry = re.split(r"(?m)^## v6\b", text)[0]
        listed = {m.group(1): m.group(2) for m in re.finditer(r"(?m)^- ([A-Z]+-\d+[a-z]?): (.+)$", entry)}
        # the v7 and later blocks (v8 holds the Architect rules) together are the entry since the base
        sections = {s: "\n".join(part.split("\n\n")[0] for part in entry.split(f"\n{s}:\n")[1:]) for s in ("added", "changed", "removed", "retargeted")}
        # IDs in the diff sit in added/removed/retargeted with a reason
        self.assertEqual(sorted(diff - set(listed)), [], "rule IDs changed since the base but missing from the v7 entry")
        for rid in diff:
            self.assertGreater(len(listed[rid]), 10, f"{rid} has no reason")
        for rid in set(old) - set(new):
            self.assertIn(f"- {rid}:", sections["removed"])
        for rid in set(new) - set(old):
            self.assertIn(f"- {rid}:", sections["added"])
        for rid in diff & set(old) & set(new):
            self.assertTrue(f"- {rid}:" in sections["retargeted"] or f"- {rid}:" in sections["changed"] or f", {rid}:" in sections["changed"],
                            f"{rid} is in neither retargeted nor changed")

    def test_no_opus_review_subagent_in_the_rule_files(self):
        pat = re.compile(r"Opus review|review subagent.{0,40}Opus|Opus.{0,20}review subagent")
        for f in sorted((ROOT / "templates" / "squad" / "process").rglob("*")):
            if f.is_file():
                self.assertIsNone(pat.search(f.read_text(encoding="utf-8")), str(f))
        text = (ROOT / "skills" / "squad-process-update" / "changelog.md").read_text(encoding="utf-8")
        for line in re.split(r"(?m)^## v6\b", text)[0].splitlines():
            self.assertIsNone(pat.search(line), line)

    def test_the_owner_rules_changed_after_17_are_listed(self):
        text = (ROOT / "skills" / "squad-process-update" / "changelog.md").read_text(encoding="utf-8")
        for rid in ("SPAWN-4", "SIZE-18", "LC-7c", "REV-22", "SUITE-2d"):
            self.assertIn(f"- {rid}:", text)


# ---- drop-scope-size 05 (design 04a): sizes.md and teams.md in the team language ----------------------------------
import itertools  # noqa: E402
from pathlib import Path  # noqa: E402
import sys  # noqa: E402

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

    def test_done_text_by_the_four_shapes(self):
        both = composed("manager", team="qa-white, qa-black")
        self.assertIn("Done = every checker on the team has passed the task: QA whitebox PASS and QA blackbox PASS", both)
        self.assertIn("One PASS is never enough", both)
        for other in ("## TEAM-1", "## TEAM-2", "## TEAM-3"):
            self.assertNotIn(other, both)
        w = composed("manager", team="qa-white")
        self.assertIn("Done = every checker on the team has passed the task: QA whitebox PASS", w)
        self.assertNotIn("QA blackbox PASS", w)
        self.assertNotIn("One PASS is never enough", w)
        b = composed("manager", team="qa-black")
        self.assertIn("QA blackbox PASS, and the Developer's `## Review` confirmed", b)
        self.assertNotIn("QA whitebox PASS", b)
        n = composed("manager", team="")
        self.assertIn("Done = the Developer's checks, `evidence.md` and `## Review` exist, and the code-check owner", n)
        self.assertIn("No QA is on the team: confirm `evidence.md` `## Behaviour`", n)
        self.assertNotIn("PASS and QA", n)

    def test_who_checks_behaviour_by_shape(self):
        self.assertIn("QA whitebox PASS", composed("manager", team="qa-white"))
        self.assertIn("you check the Developer's `## Behaviour`", composed("qa-whitebox", team="qa-white"))
        self.assertNotIn("you check the Developer's `## Behaviour`", composed("qa-whitebox", team="qa-white, qa-black"))
        self.assertIn("QA blackbox checks the behaviour of every task", composed("qa-blackbox", team="qa-white, qa-black"))
        self.assertIn("QA blackbox checks the behaviour of every task", composed("qa-blackbox", team="qa-black"))
        self.assertIn("The BA owns the business AC and writes them alone", composed("ba", team="ba"))
        self.assertIn("writes them with QA blackbox", composed("ba", team="ba, qa-black"))

    def test_architecture_ac_rules_follow_the_tech_ac_owner(self):
        for team, rid, role in (("tech-lead, qa-white, architect", "SIZE-23d", "tech-lead"), ("qa-white, architect", "SIZE-23c", "qa-whitebox")):
            self.assertIn(f"## {rid}", composed(role, team=team))
        self.assertNotIn("## SIZE-23d", composed("qa-whitebox", team="qa-white, architect"))
        self.assertNotIn("## SIZE-23c", composed("qa-whitebox", team="qa-white"))

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

    def test_tombstones_of_this_task_carry_why_and_a_live_replacement(self):
        rules, tombs, _ = sr.load_rules(PDIR, str(ROOT))
        ids = {r.id for r in rules}
        mine = [t for t in tombs if t.version == "v9"]
        self.assertGreaterEqual(len(mine), 10)
        for t in mine:
            self.assertGreater(len(t.why), 10, t.id)
            self.assertTrue(t.replaced_by and set(t.replaced_by) <= ids, t.id)
            self.assertNotIn(t.id, ids)

    def test_qa_b_is_gone_from_the_when_of_both_files(self):
        for name in MY_FILES:
            for line in Path(PDIR, name).read_text(encoding="utf-8").splitlines():
                if line.startswith("when:"):
                    self.assertNotRegex(line, r"\bqa-b\b|\bsize\b", line)


if __name__ == "__main__":
    unittest.main()
