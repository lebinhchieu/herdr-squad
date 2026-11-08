"""bin/squad-away-hook: "I am away" / "I am back" in a Manager session (wd2-away 02)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "bin" / "squad-away-hook"


def run(home, prompt, role="manager", var="SCOPE_DIR", stdin=None):
    env = {k: v for k, v in os.environ.items() if k not in ("SCOPE_DIR", "GOAL_DIR", "SQUAD_ROLE")}
    env["SQUAD_ROLE"] = role
    if home is not None:
        env[var] = str(home)
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin if stdin is not None else json.dumps({"prompt": prompt}),
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout


class AwayHookTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.home = Path(self._t.name)
        self.addCleanup(self._t.cleanup)

    def sleep_file(self):
        p = self.home / "watchdog.sleep"
        return p.read_text() if p.exists() else ""

    def test_manager_away_then_back(self):
        out = json.loads(run(self.home, "  I am away for the night"))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("Away mode is ON", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual((self.home / "away").read_text(), "on\n")
        self.assertIn("\non\n", self.sleep_file())
        out = json.loads(run(self.home, "i'm BACK!"))
        self.assertIn("ONE inbox read item", out["hookSpecificOutput"]["additionalContext"])
        self.assertFalse((self.home / "away").exists())
        self.assertIn("\noff\n", self.sleep_file())

    def test_goal_manager_uses_goal_dir(self):
        run(self.home, "I'm away", var="GOAL_DIR")
        self.assertTrue((self.home / "away").exists())

    def test_nothing_for_other_sessions_or_prompts(self):
        for role, prompt, home in [("dev", "I am away", self.home), ("manager", "ok, I am away", self.home),
                                   ("manager", "I am awayish", self.home), ("manager", "I am back", None)]:
            self.assertEqual(run(home, prompt, role=role), "", (role, prompt))
        self.assertEqual(run(self.home, "", stdin="not json"), "")
        self.assertEqual(os.listdir(self.home), [])

    def test_failing_switch_does_not_block(self):
        gone = self.home / "gone"
        gone.mkdir()
        (gone / "watchdog.sleep").mkdir()  # set_sleep cannot write a file here
        out = json.loads(run(gone, "I am away"))
        self.assertIn("FAILED", out["hookSpecificOutput"]["additionalContext"])
        self.assertTrue((gone / "away").exists())  # away file is written whatever the switch says


if __name__ == "__main__":
    unittest.main()
