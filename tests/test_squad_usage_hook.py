"""Stop hook: payload on stdin in, exit 2 + stderr message and a line in usage-events.jsonl out."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import winlaunch

from squadtest import BIN

SCRIPT = BIN / "squad-usage-hook"
NOW = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def line(ctx_read, tool=None, mid="m"):
    return {"type": "assistant", "timestamp": NOW, "effort": "medium",
            "message": {"id": mid, "model": "claude-sonnet-5-5",
                        "content": [{"type": "tool_use", "name": tool, "input": {}}] if tool else [],
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
        # first action at 60k, so the respawn line is 110k
        rows = [line(60_000, "Write", "first"), line(ctx)]
        (self.proj / f"{sid}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    def run_hook(self, sid="sid-1", role="dev", squad_session=True, **payload):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env["CLAUDE_CONFIG_DIR"] = str(Path(self.tmp.name) / "cfg")
        if squad_session:
            env.update(SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad), SQUAD_ROLE=role)
        data = {"hook_event_name": "Stop", "session_id": sid, **payload}
        return winlaunch.run_script(SCRIPT, input=json.dumps(data), text=True, encoding="utf-8", env=env,
                              capture_output=True, timeout=10)

    def test_fixture_over_the_line_gives_fresh_message_and_event(self):
        self.transcript("sid-1", 130_000)
        r = self.run_hook()
        self.assertEqual(r.returncode, 2)
        self.assertIn("'fresh'", r.stderr)
        self.assertIn("respawn line", r.stderr)
        self.assertNotIn("120k", r.stderr)
        self.assertIn("tell your plan owner (the Manager) and stop ([COST-5a], no squad-respawn)", r.stderr)
        self.assertIn("mid-ticket, run once: squad-respawn dev-1", r.stderr)
        [ev] = [json.loads(l) for l in self.events.read_text(encoding="utf-8").splitlines()]
        self.assertEqual((ev["agent"], ev["role"], ev["session"], ev["rule"]), ("dev-1", "dev", "sid-1", "fresh"))
        self.assertIn("tell your plan owner (the Manager) and stop ([COST-5a], no squad-respawn)", ev["action"])
        self.assertIn("mid-ticket, run once: squad-respawn dev-1", ev["action"])
        self.assertNotEqual(ev["action"], "write roles/dev-1.notes.md, then run: squad-respawn dev-1")

    def test_event_goes_to_the_scope_folder_when_the_agent_has_one(self):
        scope = Path(self.tmp.name) / "squad" / "scopes" / "sc1"
        scope.mkdir(parents=True)
        self.transcript("sid-1", 130_000)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "cfg"), SQUAD_NAME="dev-1", SQUAD_ROLE="dev",
                   SQUAD_DIR=str(self.squad), SCOPE_DIR=str(scope))
        r = winlaunch.run_script(SCRIPT, input=json.dumps({"hook_event_name": "Stop", "session_id": "sid-1"}),
                           text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 2)
        self.assertTrue((scope / "usage-events.jsonl").exists())
        self.assertFalse(self.events.exists())

    def hook_text_with_scope_md(self, scope_md):
        scope = self.squad / "scopes" / "sc1"
        shutil.rmtree(scope, ignore_errors=True)  # a fresh scope each call: no scope.md, no fired-rule log
        scope.mkdir(parents=True)
        if scope_md is not None:
            (scope / "scope.md").write_text(scope_md, encoding="utf-8")
        self.transcript("sid-1", 130_000)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "cfg"), SQUAD_NAME="dev-1", SQUAD_ROLE="dev",
                   SQUAD_DIR=str(self.squad), SCOPE_DIR=str(scope))
        r = winlaunch.run_script(SCRIPT, input=json.dumps({"hook_event_name": "Stop", "session_id": "sid-1"}),
                                 text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 2, r.stderr)
        return r.stderr

    def test_developer_text_names_the_plan_owner_from_scope_md(self):  # task 18 AC2
        text = self.hook_text_with_scope_md("# Scope: x\nteam: ba, team-lead, qa-white (a note)\n")
        self.assertIn("tell your plan owner (the Team Lead) and stop ([COST-5], no squad-respawn)", text)
        self.assertNotIn("tell the Team Lead", text)
        # `team-lead` only inside the trailing note does not count; no team line and no scope.md: the Manager
        for scope_md in ("team: qa-white, qa-black (Manager plans, no team-lead)\n", "# Scope\n", None):
            self.assertIn("tell your plan owner (the Manager) and stop ([COST-5a], no squad-respawn)", self.hook_text_with_scope_md(scope_md))

    def test_other_roles_text_is_unchanged(self):  # task 18 AC3
        self.transcript("sid-1", 130_000)
        r = self.run_hook(role="qa-whitebox")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr, "Cost rule 'fresh' fired: your context is past your respawn line "
                         "(your context at first action + 50k, at most 180k) or was compacted. Finish the step you are on, "
                         "then write roles/dev-1.notes.md, then run: squad-respawn dev-1\n")

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
        p.write_text(json.dumps(line(190_000)) + "\n", encoding="utf-8")  # no first action: only the 180k cap
        self.assertEqual(self.run_hook(sid="unlisted", transcript_path=str(p)).returncode, 2)

    def test_garbage_stdin_exits_zero(self):
        env = dict(os.environ, SQUAD_NAME="a", SQUAD_DIR=str(self.squad), SQUAD_ROLE="dev")
        r = winlaunch.run_script(SCRIPT, input="not json", text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0)

    def test_a_stale_lock_dir_does_not_wedge_the_event_append(self):  # ticket 06: no flock, lock left by a killed writer
        lock = Path(str(self.events) + ".lock")
        lock.mkdir()
        self.transcript("sid-1", 130_000)
        self.transcript("sid-2", 130_000)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "cfg"), SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad),
                   SQUAD_ROLE="dev")
        env = winlaunch.no_flock_env(env, self.tmp.name)
        for n in (1, 2):
            data = {"hook_event_name": "Stop", "session_id": f"sid-{n}"}
            r = winlaunch.run_script(SCRIPT, input=json.dumps(data), text=True, encoding="utf-8", env=env,
                                     capture_output=True, timeout=120)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), n)
            self.assertFalse(lock.exists())


if __name__ == "__main__":
    unittest.main()
