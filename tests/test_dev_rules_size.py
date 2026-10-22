"""Ticket 22: the composed Developer rules fit 5 KiB at every size x design x goal, keep every duty, and
anything left out stays one `squad-process rule <ID>` away."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
from rulesview import ROOT, ROLES, run, who

LIMIT = 5120
NOW = "2026-10-22T10:00:00Z"
COMBOS = list(product("SML", ("yes", "no"), ("yes", "no")))


def compose(role, size, design="no", goal="no", name="role-cards-upgrade", agent="plugin-dev-role-cards-upgrade-12"):
    """The raw composed bytes for a pinned fixture home with live-length names; no --plugin-root, time injected."""
    import squadcompose
    pin = f"plugin: {squadcompose.running_version()} 0123456789abcdef0123456789abcdef01234567\n"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / name
        home.mkdir(parents=True)
        (home / "scope.md").write_text(f"goal:{' g1' if goal == 'yes' else ''}\nsize: {size}\nqa: full\ndesign: {design}\n{pin}",
                                       encoding="utf-8", newline="\n")
        out = Path(tmp) / "rules.md"
        r = subprocess.run([sys.executable, str(ROOT / "bin" / "squad-process"), "compose", role, "--home", str(home),
                            "--out", str(out), "--now", NOW, "--agent", agent], capture_output=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr
        return out.read_bytes()


def section(text, rule_id):
    """Body of one rule in a composed file, '' when the rule is not there."""
    m = re.search(rf"(?m)^## {re.escape(rule_id)} [^\n]*\n(.*?)(?=^## |\Z)", text, re.S)
    return m.group(1) if m else ""


class DevRulesSize(unittest.TestCase):
    def test_every_combination_fits_5_kib(self):
        for size, design, goal in COMBOS:
            with self.subTest(size=size, design=design, goal=goal):
                n = len(compose("dev", size, design, goal))
                self.assertLessEqual(n, LIMIT, f"dev at {size}/design {design}/goal {goal} is {n} B")

    def test_must_keep_duties_by_rule_id(self):
        for size, design, goal in COMBOS:
            t = compose("dev", size, design, goal).decode()
            tag = f"{size}/{design}/{goal}"
            owner = "Tech Lead" if size == "S" else "Team Lead"
            checks = {
                "CORE-1": "returned",
                "CORE-2": "`HANDIN`",
                "CORE-6": "squad-process rule <ID>",
                "LC-3a": "On `FAIL`: fix every finding",
                "START-6": "$SQUAD_DIR",
                "START-10": "git branch --show-current",
                "MSG-3": "`NN` alone",
                "LC-18": "squad-label",
                "LC-20a" if size == "S" else "LC-20b": f"Tell the {owner}",
                "REV-13a" if size == "S" else "REV-13b": "HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it",
                "REV-14a" if size == "S" else "REV-14b": "After a PASS, a later commit goes to",
                "EVID-2b": "squad-evidence check",
                "COST-5": "no `squad-respawn`",
                "SAFE-1a": "Never push, rebase",
                "SAFE-3": "by PID",
                "SAFE-4": "files your role owns",
                "SAFE-11": "mktemp -d",
                "SUITE-2a": "only the test files you touched",
                "MSG-4a" if size == "S" else "MSG-4b": "Manager" if size == "S" else "Team Lead",
                "MSG-11a" if size == "S" else "MSG-11b": f"to the {owner}",
            }
            if design == "yes":
                checks["LC-19"] = "Status: final"
            for rid, needle in checks.items():
                with self.subTest(combo=tag, rule=rid):
                    self.assertIn(needle, section(t, rid))
            self.assertIn("## LC-18 ", t)

    def test_lost_rules_are_one_command_away(self):
        for rid in ("GOAL-6b", "PROMO-5", "REV-15", "MSG-5", "MSG-9", "COST-2", "SAFE-2", "SAFE-5", "REV-4", "LC-6"):
            with self.subTest(rule=rid):
                r = run("rule", rid)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.startswith(f"## {rid} "), r.stdout)
                for size, (acting, aware) in who(rid).items():
                    self.assertNotIn("dev", acting + aware, f"{rid} at {size}")

    def test_core6_reaches_every_role_and_names_rule_and_who(self):
        for role in ROLES:
            with self.subTest(role=role):
                body = section(compose(role, "M").decode(), "CORE-6")
                self.assertIn("squad-process rule <ID>", body)
                self.assertIn("squad-process who <ID>", body)

    def test_scratch_rule_reaches_dev_and_both_qas_only(self):
        have = {r for r in ROLES if "mktemp -d" in compose(r, "M").decode() and "${VAR:?}" in compose(r, "M").decode()}
        self.assertEqual(have, {"dev", "qa-whitebox", "qa-blackbox"})
        self.assertLessEqual(len(section(compose("dev", "M").decode(), "SAFE-11").split()), 45)

    def test_core_file_stays_within_40_lines(self):
        self.assertLessEqual(len((ROOT / "templates/squad/process/core.md").read_text().rstrip("\n").split("\n")), 40)


if __name__ == "__main__":
    unittest.main()
