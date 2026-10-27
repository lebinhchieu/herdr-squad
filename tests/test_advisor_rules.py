"""Ticket 18: advisor rules (LC-25, LC-26), COST-11 step-up, settings overlay can turn the advisor off."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rulesview import ROLES, acts, composed, run

ROOT = Path(__file__).resolve().parent.parent
ALL = {r for r in ROLES if r != "token-coach"}


def rule(role, rid, size="M"):
    return composed(role, size).split(f"## {rid} ")[1].split(" ## ")[0]


def effective(tmp):
    return subprocess.run([sys.executable, str(ROOT / "bin" / "squadsettings.py"), "effective", "--role", "dev",
                           "--squad-dir", tmp, "--template-root", str(ROOT)], capture_output=True, encoding="utf-8")


class AdvisorRulesTest(unittest.TestCase):
    def test_who_shows_acting_roles(self):
        for size in "SML":
            self.assertEqual(set(acts("LC-25", size)), ALL)
            self.assertEqual(acts("LC-26", size), ("manager", "tech-lead"))

    def test_triggers_and_note(self):
        r = rule("dev", "LC-25")
        for needle in ("2 failed tries at one error", "2 unanswered `BLOCKED`", "3rd `FAIL`",
                       "3 lines: question, advice", "question, advice, what was done", "Advisor off: say so"):
            self.assertIn(needle, r)
        r = rule("tech-lead", "LC-26")
        self.assertIn("irreversible design choice", r)
        self.assertIn("[LC-25] note", r)
        self.assertNotIn("LC-24", composed("dev", "M"))

    def test_step_up_replaced(self):
        r = rule("manager", "COST-11")
        self.assertNotIn("notch of model", r)
        self.assertIn("advisor first", r)
        self.assertIn("only by respawn", r)

    def test_third_return_notice_cites_a_real_rule(self):
        src = (ROOT / "bin" / "squad-log-message").read_text(encoding="utf-8")
        self.assertIn("consult the advisor before the next HANDIN; note it in the task file [LC-25]", src)
        r = run("rule", "LC-25")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("## LC-25 "))

    def test_overlay_can_turn_the_advisor_off(self):
        # "" turns it off; null makes Claude Code refuse the whole settings file (probed 2026-10-22).
        with tempfile.TemporaryDirectory() as tmp:
            sd = Path(tmp) / "settings"
            sd.mkdir()
            (sd / "dev.local.json").write_text(json.dumps({"advisorModel": ""}), encoding="utf-8")
            r = effective(tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["advisorModel"], "")
            (sd / "dev.local.json").write_text("{}", encoding="utf-8")
            self.assertEqual(json.loads(effective(tmp).stdout)["advisorModel"], "opus")

    def test_lint_passes(self):
        r = run("lint")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
