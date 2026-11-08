"""Ticket 22: the composed Developer rules fit 5 KiB at every size x design x goal, keep every duty, and
anything left out stays one `squad-process rule <ID>` away."""
import re
import sys
import tempfile
import unittest
from itertools import product
from pathlib import Path

from squadtest import BIN

sys.path.insert(0, str(BIN))
from rulesview import ROOT, ROLES, run, shape_team, who

LIMIT = 5120
NOW = "2026-10-22T10:00:00Z"
KEYS = ("ba", "team-lead", "tech-lead", "qa-white", "qa-black", "designer", "architect")
TEAMS = [tuple(k for i, k in enumerate(KEYS) if m >> i & 1) for m in range(128)]
COMBOS = [("S", "no", "no"), ("M", "yes", "no"), ("L", "yes", "yes")]  # one per size; design yes at M and L covers LC-19b and LC-19


def compose(role, size, design="no", goal="no", architecture="no", name="role-cards-upgrade", agent="plugin-dev-role-cards-upgrade-12"):
    """The raw composed bytes for a pinned fixture home with live-length names; no --plugin-root, time injected."""
    import squadcompose
    pin = (squadcompose.running_version(), "0123456789abcdef0123456789abcdef01234567")
    team = shape_team(size, "yes", design, architecture)  # the converter's mapping of the old shape
    return compose_team(role, team, goal=goal, name=name, agent=agent)


def compose_team(role, team, goal="no", qa="full", name="role-cards-upgrade", agent="plugin-dev-role-cards-upgrade-12"):
    """Raw composed bytes for a `team:` home (no scaffold) with live-length names; pinned plugin line, time injected."""
    import squadcompose
    pin = (squadcompose.running_version(), "0123456789abcdef0123456789abcdef01234567")
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / name
        home.mkdir(parents=True)
        (home / "scope.md").write_text(f"goal:{' g1' if goal == 'yes' else ''}\nteam: {', '.join(team) or 'none'}\nqa: {qa}\nplugin: {pin[0]} {pin[1]}\n",
                                       encoding="utf-8", newline="\n")
        return squadcompose.compose(role, str(home), str(ROOT), None, agent, NOW, pin).encode("utf-8")


def section(text, rule_id):
    """Body of one rule in a composed file, '' when the rule is not there."""
    m = re.search(rf"(?m)^## {re.escape(rule_id)} [^\n]*\n(.*?)(?=^## |\Z)", text, re.S)
    return m.group(1) if m else ""


class DevRulesSize(unittest.TestCase):
    def sweep(self):
        for team in TEAMS:
            for goal, qa in product(("yes", "no"), ("full", "light")):
                yield team, goal, qa, len(compose_team("dev", team, goal, qa))

    def test_every_team_set_fits_5_kib(self):
        for team, goal, qa, n in self.sweep():
            self.assertLessEqual(n, LIMIT, f"dev, team {team}, goal {goal}, qa {qa} is {n} B")

    def test_must_keep_duties_by_rule_id(self):
        for size, design, goal in COMBOS:
            t = compose("dev", size, design, goal).decode()
            tag = f"{size}/{design}/{goal}"
            owner = {"S": "Manager", "M": "Manager", "L": "Team Lead"}[size]
            ask_owner = "Team Lead" if size == "L" else "Manager"  # MSG-11a/b move with ticket 30
            checks = {
                "CORE-1": "returned",
                "CORE-2": "`HANDIN`",
                "CORE-6": "squad-process rule <ID>",
                "LC-3a": "On `FAIL`: fix every finding",
                "START-6": "$SQUAD_DIR",
                "START-10": "git branch --show-current",
                "MSG-3": "`NN` alone",
                "LC-18": "squad-label",
                {"S": "LC-20a", "M": "LC-20b", "L": "LC-20b"}[size]: "Tell the Manager" if size == "S" else "Tell the plan owner",
                "REV-13a" if size == "S" else "REV-13b": "HANDIN <task>: the branch of your worktree (`git branch --show-current`), commit <sha>, how to run it",
                "REV-14a": "After a PASS, a later commit goes to",
                {"S": "REV-22", "M": "EVID-2d", "L": "EVID-2b"}[size]: "squad-evidence check",
                "COST-5" if size == "L" else "COST-5a": "no `squad-respawn`",
                "SAFE-1a": "Never push, rebase",
                "SAFE-3": "by PID",
                "SAFE-4": "files your role owns",
                "SAFE-11": "mktemp -d",
                {"S": "SUITE-2d", "M": "SUITE-2c", "L": "SUITE-2a"}[size]: "the test files you touched",
                "MSG-4b" if size == "L" else "MSG-4a": ask_owner,
                "MSG-11b" if size == "L" else "MSG-11a": f"to the {ask_owner}",
            }
            if design == "yes":
                checks["LC-19b" if size in "SM" else "LC-19"] = "Status: final"
            for rid, needle in checks.items():
                with self.subTest(combo=tag, rule=rid):
                    self.assertIn(needle, section(t, rid))
            self.assertIn("## LC-18 ", t)

    def test_lost_rules_are_one_command_away(self):
        for rid in ("GOAL-6b", "PROMO-5", "REV-15", "NOTE-1", "MSG-5", "MSG-9", "COST-2", "SAFE-2", "SAFE-5", "REV-4", "LC-6", "SUITE-4", "REV-5a", "EVID-5"):
            with self.subTest(rule=rid):
                r = run("rule", rid)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.startswith(f"## {rid} "), r.stdout)
                for size, (acting, aware) in who(rid).items():
                    self.assertNotIn("dev", acting + aware, f"{rid} at {size}")

    def test_on_demand_rules_attach_to_no_role(self):
        for rid in ("REV-5a", "EVID-5"):
            w = who(rid)
            self.assertTrue(w)
            for key, (acting, aware) in w.items():
                self.assertEqual((acting, aware), ((), ()), f"{rid} at {key}")
            for team in ((), ("tech-lead",), ("team-lead", "designer"), ("qa-white", "qa-black", "designer", "architect")):
                for role in ROLES:
                    self.assertNotIn(f"## {rid} ", compose_team(role, team).decode(), f"{role} {team}")

    def test_manager_composed_bytes_did_not_grow_vs_90be196(self):
        # (team, goal) -> bytes of the composed Manager rules at 90be196 plus ticket 06's parked-question rule (+265 B, +253 B with goal+architect) and the respawn-line rules of fix 2 (+118 to +132 B) and task 11 worktree reuse in SPAWN-5a (+291 B) and task 12 suite policy in SUITE-1b (+156 B) and task 13 GOAL-6b ask (+59 B) and task-claim-gates 05 passed/merged text and LC-27 (+678 to +742 B) and wd2-away 03 away rule ITER-17 (+951 B), fixture home with live-length names
        base = {((), "yes"): 56195, ((), "no"): 52906, (("tech-lead",), "yes"): 55106, (("team-lead", "designer"), "no"): 51120,
                (("qa-white", "qa-black", "designer", "architect"), "yes"): 59301,
                (("ba", "team-lead", "tech-lead", "qa-white", "qa-black", "designer", "architect"), "no"): 52204}
        for (team, goal), n in base.items():
            with self.subTest(team=team, goal=goal):
                self.assertLessEqual(len(compose_team("manager", team, goal)), n)

    def test_moved_rules_are_cited_from_the_rule_that_keeps_them(self):
        for kept, moved in (("REV-22", "REV-5a"), ("LC-19", "EVID-5")):
            with self.subTest(moved=moved):
                self.assertIn(f"[{moved}]", section(compose_team("dev", ("tech-lead", "designer"), "no").decode(), kept))

    def test_core6_reaches_every_role_and_names_rule_and_who(self):
        for role in ROLES:
            with self.subTest(role=role):
                body = section(compose(role, "M").decode(), "CORE-6")
                self.assertIn("squad-process rule <ID>", body)
                self.assertIn("squad-process who <ID>", body)

    def test_scratch_rule_reaches_dev_and_both_qas_only(self):
        have = {r for r in ROLES if "mktemp -d" in compose(r, "M").decode() and "rm -rf /tmp/tmp." in compose(r, "M").decode()}
        self.assertEqual(have, {"dev", "qa-whitebox", "qa-blackbox"})
        self.assertLessEqual(len(section(compose("dev", "M").decode(), "SAFE-11").split()), 45)
        for r in ("dev", "qa-whitebox", "qa-blackbox"):
            self.assertIn("`cd` out before `rm`", section(compose(r, "M").decode(), "SAFE-11"))

    def test_core_file_stays_within_40_lines(self):
        self.assertLessEqual(len((ROOT / "templates/squad/process/core.md").read_text().rstrip("\n").split("\n")), 40)


if __name__ == "__main__":
    unittest.main()
