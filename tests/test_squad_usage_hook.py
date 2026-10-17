"""Stop hook: payload on stdin in, exit 2 + stderr message and a line in usage-events.jsonl out."""
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-usage-hook"
NOW = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def line(ctx_read):
    return {"type": "assistant", "timestamp": NOW, "effort": "medium",
            "message": {"id": "m", "model": "claude-sonnet-5-5",
                        "usage": {"input_tokens": 2, "cache_read_input_tokens": ctx_read,
                                  "cache_creation_input_tokens": 0, "output_tokens": 10}}}


class HookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.squad = root / "squad"
        self.squad.mkdir()
        self.events = self.squad / "usage-events.jsonl"
        self.proj = root / "cfg" / "projects" / "-cwd"
        self.proj.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def transcript(self, sid, ctx):
        (self.proj / f"{sid}.jsonl").write_text(json.dumps(line(ctx)) + "\n", encoding="utf-8")

    def run_hook(self, sid="sid-1", role="dev", squad_session=True, **payload):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env["CLAUDE_CONFIG_DIR"] = str(Path(self.tmp.name) / "cfg")
        if squad_session:
            env.update(SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad), SQUAD_ROLE=role)
        data = {"hook_event_name": "Stop", "session_id": sid, **payload}
        return subprocess.run([str(SCRIPT)], input=json.dumps(data), text=True, encoding="utf-8", env=env,
                              capture_output=True, timeout=10)

    def test_fixture_over_120k_gives_fresh_message_and_event(self):
        self.transcript("sid-1", 130_000)
        r = self.run_hook()
        self.assertEqual(r.returncode, 2)
        self.assertIn("'fresh'", r.stderr)
        self.assertIn("squad-respawn dev-1", r.stderr)
        [ev] = [json.loads(l) for l in self.events.read_text(encoding="utf-8").splitlines()]
        self.assertEqual((ev["agent"], ev["role"], ev["session"], ev["rule"]), ("dev-1", "dev", "sid-1", "fresh"))
        self.assertIn("squad-respawn dev-1", ev["action"])

    def test_event_goes_to_the_scope_folder_when_the_agent_has_one(self):
        scope = Path(self.tmp.name) / "squad" / "scopes" / "sc1"
        scope.mkdir(parents=True)
        self.transcript("sid-1", 130_000)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "cfg"), SQUAD_NAME="dev-1", SQUAD_ROLE="dev",
                   SQUAD_DIR=str(self.squad), SCOPE_DIR=str(scope))
        r = subprocess.run([str(SCRIPT)], input=json.dumps({"hook_event_name": "Stop", "session_id": "sid-1"}),
                           text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 2)
        self.assertTrue((scope / "usage-events.jsonl").exists())
        self.assertFalse(self.events.exists())

    def test_under_threshold_is_silent(self):
        self.transcript("sid-1", 50_000)
        r = self.run_hook()
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertFalse(self.events.exists())

    def test_non_squad_session_is_ignored(self):
        self.transcript("sid-1", 130_000)
        r = self.run_hook(squad_session=False)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertFalse(self.events.exists())

    def test_manager_is_exempt(self):
        self.transcript("sid-1", 130_000)
        self.assertEqual(self.run_hook(role="manager").returncode, 0)

    def test_rule_fires_once_per_session(self):
        self.transcript("sid-1", 130_000)
        self.assertEqual(self.run_hook().returncode, 2)
        self.assertEqual(self.run_hook().returncode, 0)
        self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), 1)

    def test_stop_hook_active_is_not_re_fired(self):
        self.transcript("sid-1", 130_000)
        self.assertEqual(self.run_hook(stop_hook_active=True).returncode, 0)
        self.assertFalse(self.events.exists())

    def test_uses_transcript_path_from_payload(self):
        p = Path(self.tmp.name) / "elsewhere.jsonl"
        p.write_text(json.dumps(line(130_000)) + "\n", encoding="utf-8")
        self.assertEqual(self.run_hook(sid="unlisted", transcript_path=str(p)).returncode, 2)

    def test_garbage_stdin_exits_zero(self):
        env = dict(os.environ, SQUAD_NAME="a", SQUAD_DIR=str(self.squad), SQUAD_ROLE="dev")
        r = subprocess.run([str(SCRIPT)], input="not json", text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
