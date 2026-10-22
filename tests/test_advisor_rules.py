"""Ticket 18: advisor rules (LC-24..26), COST-11 step-up, settings overlay can turn the advisor off."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rulesview import ROLES, acts, composed, run

ROOT = Path(__file__).resolve().parent.parent


def rule(role, rid, size="M"):
    return composed(role, size).split(f"## {rid} ")[1].split(" ## ")[0]


class AdvisorRulesTest(unittest.TestCase):
    def test_who_shows_acting_roles(self):
        for size in "SML":
            self.assertEqual(acts("LC-24", size), ("dev",))
            self.assertEqual(set(acts("LC-25", size)), set(ROLES_ACT))
            self.assertEqual(acts("LC-26", size), ("manager", "tech-lead"))

    def test_each_rule_asks_for_a_three_line_note(self):
        for rid, role in (("LC-24", "dev"), ("LC-25", "dev"), ("LC-26", "tech-lead")):
            r = rule(role, rid)
            self.assertIn("3-line note", r)
            self.assertIn("question, advice, what was done", r)
        self.assertIn("3rd `FAIL`", rule("dev", "LC-24"))
        self.assertIn("2 failed attempts", rule("dev", "LC-25"))
        self.assertIn("unanswered for 2 rounds", rule("dev", "LC-25"))
        self.assertIn("irreversible", rule("manager", "LC-26"))

    def test_step_up_replaced(self):
        r = rule("manager", "COST-11")
        self.assertNotIn("notch of model", r)
        self.assertIn("advisor first", r)
        self.assertIn("only by respawn", r)

    def test_third_return_notice_names_the_advisor(self):
        src = (ROOT / "bin" / "squad-log-message").read_text(encoding="utf-8")
        self.assertIn("consult the advisor before the next HANDIN and note it in the task file [LC-24]", src)

    def test_overlay_can_turn_the_advisor_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd = Path(tmp) / "settings"
            sd.mkdir()
            (sd / "dev.local.json").write_text(json.dumps({"advisorModel": None}), encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT / "bin" / "squadsettings.py"), "effective", "--role", "dev",
                                "--squad-dir", tmp, "--template-root", str(ROOT)],
                               capture_output=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIsNone(json.loads(r.stdout).get("advisorModel", "absent-or-null"))
            (sd / "dev.local.json").write_text("{}", encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT / "bin" / "squadsettings.py"), "effective", "--role", "dev",
                                "--squad-dir", tmp, "--template-root", str(ROOT)],
                               capture_output=True, encoding="utf-8")
            self.assertEqual(json.loads(r.stdout)["advisorModel"], "opus")

    def test_lint_passes(self):
        r = run("lint")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


ROLES_ACT = [r for r in ROLES if r != "token-coach"]

if __name__ == "__main__":
    unittest.main()
