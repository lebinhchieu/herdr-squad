"""bin/squad-lazy-hook: first prompt of a lazily respawned session (warmcache 02).
Input shape: the common hook field `session_id`, as in tests/fixtures/squad-notify/subagent-stop.json (a real capture)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "bin" / "squad-lazy-hook"
SID = "7d38e90b-9c3f-4a23-84c1-cd946ae0f1aa"


class LazyHookTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.home = Path(self._t.name).resolve()
        (self.home / "roles").mkdir()
        self.marker = self.home / "roles" / "dev-1.lazy"

    def run_hook(self, sid):
        env = {k: v for k, v in os.environ.items() if k not in ("SCOPE_DIR", "GOAL_DIR", "SQUAD_DIR")}
        env.update(SCOPE_DIR=str(self.home), SQUAD_NAME="dev-1")
        stdin = json.dumps({"session_id": sid, "hook_event_name": "UserPromptSubmit", "prompt": "hi"})
        r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_matching_session_gets_text_and_marker_goes(self):
        self.marker.write_text(SID + "\n")
        out = json.loads(self.run_hook(SID))["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "UserPromptSubmit")
        self.assertIn(str(self.home / "roles" / "dev-1.notes.md"), out["additionalContext"])
        self.assertIn(str(self.home / "roles" / "dev-1.rules.md"), out["additionalContext"])
        self.assertIn("read no other process file", out["additionalContext"])
        self.assertFalse(self.marker.exists())

    def test_other_session_or_no_marker_is_silent_and_keeps_marker(self):
        self.assertEqual(self.run_hook(SID), "")
        self.marker.write_text(SID + "\n")
        self.assertEqual(self.run_hook("old-session"), "")
        self.assertEqual(self.marker.read_text(), SID + "\n")

    def test_second_prompt_is_silent(self):
        self.marker.write_text(SID + "\n")
        self.assertNotEqual(self.run_hook(SID), "")
        self.assertEqual(self.run_hook(SID), "")


if __name__ == "__main__":
    unittest.main()
