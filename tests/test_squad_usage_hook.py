"""Stop and PostToolUse hook: payload on stdin in; Stop: exit 2 + stderr message, PostToolUse: JSON context, exit 0; a line in usage-events.jsonl out."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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


class HookBase(unittest.TestCase):
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

    def transcript(self, sid, ctx, pad=0):
        # the respawn line is a fixed 600k; pad = bytes of a non-assistant row (the file's size)
        rows = [line(60_000, "Write", "first"), line(ctx)]
        if pad:
            rows.append({"type": "user", "message": {"content": "x" * pad}})
        (self.proj / f"{sid}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    def run_hook(self, sid="sid-1", role="dev", squad_session=True, **payload):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env["CLAUDE_CONFIG_DIR"] = str(Path(self.tmp.name) / "cfg")
        if squad_session:
            env.update(SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad), SQUAD_ROLE=role)
        data = {"hook_event_name": "Stop", "session_id": sid, **payload}
        return winlaunch.run_script(SCRIPT, input=json.dumps(data), text=True, encoding="utf-8", env=env,
                              capture_output=True, timeout=10)


class HookTest(HookBase):
    def test_fixture_over_the_line_gives_fresh_message_and_event(self):
        self.transcript("sid-1", 630_000)
        r = self.run_hook()
        self.assertEqual(r.returncode, 2)
        self.assertIn("'fresh'", r.stderr)
        self.assertIn("respawn line", r.stderr)
        self.assertNotIn("120k", r.stderr)
        self.assertIn("tell your plan owner (the Team Lead) and stop ([COST-5], no squad-respawn)", r.stderr)
        self.assertIn("mid-ticket, run once: squad-respawn dev-1", r.stderr)
        [ev] = [json.loads(l) for l in self.events.read_text(encoding="utf-8").splitlines()]
        self.assertEqual((ev["agent"], ev["role"], ev["session"], ev["rule"]), ("dev-1", "dev", "sid-1", "fresh"))
        self.assertEqual((ev["line"], ev["turns"]), (600_000, 2))   # the fixed line; two main-thread turns
        self.assertGreater(ev["ctx"], 630_000 - 1)                  # last context, from the same summarize as the row
        self.assertIn("tell your plan owner (the Team Lead) and stop ([COST-5], no squad-respawn)", ev["action"])
        self.assertIn("mid-ticket, run once: squad-respawn dev-1", ev["action"])
        self.assertNotEqual(ev["action"], "write roles/dev-1.notes.md, then run: squad-respawn dev-1")

    def test_event_goes_to_the_scope_folder_when_the_agent_has_one(self):
        scope = Path(self.tmp.name) / "squad" / "scopes" / "sc1"
        scope.mkdir(parents=True)
        self.transcript("sid-1", 630_000)
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
        self.transcript("sid-1", 630_000)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "cfg"), SQUAD_NAME="dev-1", SQUAD_ROLE="dev",
                   SQUAD_DIR=str(self.squad), SCOPE_DIR=str(scope))
        r = winlaunch.run_script(SCRIPT, input=json.dumps({"hook_event_name": "Stop", "session_id": "sid-1"}),
                                 text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 2, r.stderr)
        return r.stderr

    def test_developer_text_is_the_same_for_every_scope_md_shape(self):  # ticket 04 AC5
        want = "tell your plan owner (the Team Lead) and stop ([COST-5], no squad-respawn)"
        texts = [self.hook_text_with_scope_md(s) for s in
                 ("# Scope: x\nteam: ba, team-lead, qa-white (a note)\n", "team: qa-white, qa-black\n", None)]
        for text in texts:
            self.assertIn(want, text)
        self.assertEqual(len(set(texts)), 1)

    def test_other_roles_text_is_unchanged(self):  # task 18 AC3
        self.transcript("sid-1", 630_000)
        r = self.run_hook(role="qa-whitebox")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr, "Cost rule 'fresh' fired: your context is past your respawn line "
                         "(600k) or was compacted. Finish the step you are on, "
                         "then write roles/dev-1.notes.md, then run: squad-respawn dev-1\n")

    def test_under_threshold_is_silent(self):
        self.transcript("sid-1", 50_000)
        r = self.run_hook()
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertFalse(self.events.exists())

    def test_non_squad_session_is_ignored(self):
        self.transcript("sid-1", 630_000)
        r = self.run_hook(squad_session=False)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertFalse(self.events.exists())

    def test_manager_is_exempt(self):
        self.transcript("sid-1", 630_000)
        self.assertEqual(self.run_hook(role="manager").returncode, 0)

    def test_rule_fires_once_per_session(self):
        self.transcript("sid-1", 630_000)
        self.assertEqual(self.run_hook().returncode, 2)
        self.assertEqual(self.run_hook().returncode, 0)
        self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), 1)

    def test_the_dedupe_skips_corrupt_blank_and_non_object_lines(self):  # task 20 AC1, AC2
        def ev(session):
            return json.dumps({"agent": "dev-1", "session": session, "rule": "fresh"})
        mess = ['{"session": "sid-1", "rul', "", ev("sid-1"), "5", "[]", "null", '"x"']
        self.events.write_text("\n".join(mess) + "\n", encoding="utf-8")
        self.transcript("sid-1", 630_000)
        self.assertEqual(self.run_hook().returncode, 0)  # the valid event of this session still stops it
        self.assertEqual(self.events.read_text(encoding="utf-8").splitlines(), mess)
        # control: the same mess, the valid event is for another session: the hook fires and appends one line
        self.events.write_text("\n".join(m if m != ev("sid-1") else ev("other") for m in mess) + "\n", encoding="utf-8")
        before = len(self.events.read_text(encoding="utf-8").splitlines())
        self.assertEqual(self.run_hook().returncode, 2)
        self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), before + 1)

    def test_stop_hook_active_is_not_re_fired(self):
        self.transcript("sid-1", 630_000)
        self.assertEqual(self.run_hook(stop_hook_active=True).returncode, 0)
        self.assertFalse(self.events.exists())

    def test_uses_transcript_path_from_payload(self):
        p = Path(self.tmp.name) / "elsewhere.jsonl"
        p.write_text(json.dumps(line(610_000)) + "\n", encoding="utf-8")  # over the fixed line
        self.assertEqual(self.run_hook(sid="unlisted", transcript_path=str(p)).returncode, 2)

    def test_garbage_stdin_exits_zero(self):
        env = dict(os.environ, SQUAD_NAME="a", SQUAD_DIR=str(self.squad), SQUAD_ROLE="dev")
        r = winlaunch.run_script(SCRIPT, input="not json", text=True, encoding="utf-8", env=env, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0)

    def test_a_stale_lock_dir_does_not_wedge_the_event_append(self):  # ticket 06: no flock, lock left by a killed writer
        lock = Path(str(self.events) + ".lock")
        lock.mkdir()
        self.transcript("sid-1", 630_000)
        self.transcript("sid-2", 630_000)
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


class PostToolUseTest(HookBase):
    """Ticket 09: the same check at a tool boundary, throttled by transcript growth (stamp roles/<agent>.usage-check)."""
    def post(self, sid="sid-1", **kw):
        return self.run_hook(sid=sid, hook_event_name="PostToolUse", tool_name="Bash",
                                  transcript_path=str(self.proj / f"{sid}.jsonl"), **kw)

    @property
    def stamp_file(self):
        return self.squad / "roles" / "dev-1.usage-check"

    def stamp(self):
        return json.loads(self.stamp_file.read_text(encoding="utf-8"))

    def test_fresh_notice_is_context_json_exit_0_once_per_session(self):  # AC2
        self.transcript("sid-1", 630_000)
        r = self.post()
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PostToolUse")
        self.assertIn("Cost rule 'fresh' fired", out["additionalContext"])
        self.assertIn("mid-ticket, run once: squad-respawn dev-1", out["additionalContext"])
        self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), 1)
        self.stamp_file.unlink()  # no stamp: the check runs again, the dedupe keeps it quiet
        r = self.post()
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), 1)

    def test_growth_under_the_step_skips_the_check_and_keeps_the_stamp(self):  # AC3
        self.transcript("sid-1", 630_000, pad=100_000)
        size = (self.proj / "sid-1.jsonl").stat().st_size
        self.stamp_file.parent.mkdir()
        old = {"ts": "2026-01-01T00:00:00.000Z", "session": "sid-1", "size": size - 65_535, "ctx": 5, "line": 6}
        self.stamp_file.write_text(json.dumps(old) + "\n", encoding="utf-8")
        r = self.post()
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.stamp(), old)
        self.assertFalse(self.events.exists())
        old["size"] = size - 65_536  # control: the step is reached, the check runs and the stamp moves
        self.stamp_file.write_text(json.dumps(old) + "\n", encoding="utf-8")
        self.assertIn("fresh", self.post().stdout)
        self.assertEqual(self.stamp()["size"], size)

    def test_a_stamp_of_another_session_does_not_throttle(self):
        self.transcript("sid-1", 630_000)
        self.stamp_file.parent.mkdir()
        size = (self.proj / "sid-1.jsonl").stat().st_size
        self.stamp_file.write_text(json.dumps({"ts": "t", "session": "old", "size": size}) + "\n", encoding="utf-8")
        self.assertIn("fresh", self.post().stdout)

    def test_manager_unknown_session_and_missing_transcript_are_silent(self):  # AC4
        self.transcript("sid-1", 630_000)
        for r in (self.post(role="manager"), self.post(sid="nope"), self.post(squad_session=False)):
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        gone = self.run_hook(hook_event_name="PostToolUse", transcript_path=str(self.proj / "gone.jsonl"))
        self.assertEqual((gone.returncode, gone.stdout, gone.stderr), (0, "", ""))
        self.assertFalse(self.events.exists())

    def test_stamp_holds_ts_session_size_ctx_line_after_post_and_after_stop(self):  # AC5
        self.transcript("sid-1", 50_000)
        size = (self.proj / "sid-1.jsonl").stat().st_size
        self.assertEqual(self.post().stdout, "")
        s = self.stamp()
        self.assertEqual((s["session"], s["size"], s["line"]), ("sid-1", size, 600_000))
        self.assertGreater(s["ctx"], 49_999)
        self.assertRegex(s["ts"], r"^\d{4}-\d\d-\d\dT")
        self.stamp_file.unlink()
        r = self.run_hook(transcript_path=str(self.proj / "sid-1.jsonl"))  # Stop, no rule fires
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertEqual(self.stamp()["size"], size)
        self.assertEqual(self.stamp()["line"], 600_000)

    def test_parallel_calls_of_one_session_record_and_notify_once(self):  # review: dedupe under the append lock
        self.transcript("sid-1", 630_000)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "cfg"), SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad), SQUAD_ROLE="dev")
        data = json.dumps({"hook_event_name": "PostToolUse", "session_id": "sid-1",
                           "transcript_path": str(self.proj / "sid-1.jsonl")})
        def call(_):
            return winlaunch.run_script(SCRIPT, input=data, text=True, encoding="utf-8", env=env,
                                        capture_output=True, timeout=30).stdout
        with ThreadPoolExecutor(6) as pool:
            outs = list(pool.map(call, range(6)))
        self.assertEqual(len([o for o in outs if o]), 1)
        self.assertEqual(len(self.events.read_text(encoding="utf-8").splitlines()), 1)

    def test_stop_stays_exit_2_with_stderr(self):  # AC6 beside the 13 inherited tests
        self.transcript("sid-1", 630_000)
        r = self.run_hook()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("'fresh'", r.stderr)


if __name__ == "__main__":
    unittest.main()
