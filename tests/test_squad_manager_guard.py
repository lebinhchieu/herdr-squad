"""squad-manager-guard: one context notice for the Manager on `squad-spawn` / `squad-inbox add` (COST-8)."""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
sys.path.insert(0, str(BIN))
_loader = importlib.machinery.SourceFileLoader("squad_manager_guard", str(BIN / "squad-manager-guard"))
_spec = importlib.util.spec_from_loader("squad_manager_guard", _loader)
guard = importlib.util.module_from_spec(_spec)
_loader.exec_module(guard)

NOW = datetime.now(timezone.utc)
ROLES = ("dev", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "token-coach")


def turn(ago_min, msg_id, ctx=1000, write=0):
    ts = (NOW - timedelta(minutes=ago_min)).isoformat().replace("+00:00", "Z")
    return {"type": "assistant", "timestamp": ts, "effort": "medium", "sessionId": "s",
            "message": {"id": msg_id, "model": "claude-sonnet-5-5",
                        "usage": {"input_tokens": 2, "cache_read_input_tokens": ctx - write,
                                  "cache_creation_input_tokens": write, "output_tokens": 100}}}


class GuardBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.scope = root / "squad" / "scopes" / "s"
        self.scope.mkdir(parents=True)
        self.transcript_path = root / "t.jsonl"
        self.log = self.scope / "usage-events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *lines, extra=()):
        self.transcript_path.write_text("".join(json.dumps(l) + "\n" for l in [*lines, *extra]), encoding="utf-8")

    def env(self, role="manager", **more):
        e = {"SQUAD_NAME": "mgr", "SQUAD_DIR": str(self.scope.parent.parent), "SCOPE_DIR": str(self.scope)}
        if role:
            e["SQUAD_ROLE"] = role
        e.update(more)
        return e

    def payload(self, command="squad-spawn dev-1 --role dev", session="sid-1", **more):
        return {"session_id": session, "transcript_path": str(self.transcript_path),
                "tool_input": {"command": command}, **more}

    def events(self):
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() else []


class DecisionTable(GuardBase):
    def test_over_threshold_gives_one_notice_naming_size_respawn_and_rule(self):
        self.write(turn(5, "a", 144_000))
        msg = guard.decide(self.env(), self.payload())
        self.assertEqual(msg, "context 144k (over 100k): after this step write your notes and run squad-respawn mgr [COST-8]")
        [ev] = self.events()
        self.assertEqual((ev["agent"], ev["role"], ev["session"], ev["rule"]), ("mgr", "manager", "sid-1", "manager-ctx"))
        self.assertIn("squad-respawn mgr", ev["action"])

    def test_a_second_call_in_the_same_session_gives_nothing(self):
        self.write(turn(5, "a", 144_000))
        self.assertTrue(guard.decide(self.env(), self.payload()))
        self.assertIsNone(guard.decide(self.env(), self.payload("squad-inbox add --kind read x")))
        self.assertEqual(len(self.events()), 1)

    def test_a_new_session_starts_clean(self):
        self.write(turn(5, "a", 144_000))
        self.assertTrue(guard.decide(self.env(), self.payload(session="old")))
        self.assertTrue(guard.decide(self.env(), self.payload(session="new")))

    def test_under_threshold_with_a_fresh_cache_gives_nothing(self):
        self.write(turn(10, "a", 40_000), turn(5, "b", 41_000))
        self.assertIsNone(guard.decide(self.env(), self.payload()))
        self.assertEqual(self.events(), [])

    def test_every_other_role_gets_nothing(self):
        self.write(turn(5, "a", 144_000))
        for role in ROLES + (None,):
            with self.subTest(role=role):
                self.assertIsNone(guard.decide(self.env(role), self.payload()))
        self.assertEqual(self.events(), [])

    def test_every_other_command_gets_nothing(self):
        self.write(turn(5, "a", 144_000))
        for cmd in ("ls", "git status", "squad-inbox list", "squad-inbox", "squad-spawner x", "echo squad-spawn a",
                    "squad-usage", "squad-respawn mgr", ""):
            with self.subTest(cmd=cmd):
                self.assertIsNone(guard.decide(self.env(), self.payload(cmd)))
        self.assertEqual(self.events(), [])

    def test_matching_commands(self):
        for cmd in ("squad-spawn a", "  squad-spawn a", "squad-inbox add --kind read", "squad-inbox   add x",
                    "/p/bin/squad-spawn a", "squad-spawn"):
            with self.subTest(cmd=cmd):
                self.assertTrue(guard.QUIET.match(cmd))

    def test_a_cache_expiry_since_the_last_turn_fires_once_under_100k(self):
        self.write(turn(200, "a", 30_000), turn(5, "b", 30_000, write=20_000))  # 195 min gap, big cache write
        msg = guard.decide(self.env(), self.payload())
        self.assertIn("cache expired", msg)
        self.assertIn("context 30k", msg)
        self.assertIsNone(guard.decide(self.env(), self.payload()))

    def test_an_idle_gap_not_yet_followed_by_a_turn_fires_once(self):
        self.write(turn(120, "a", 30_000))  # last turn 2h ago: the cache is gone now
        self.assertIn("cache expired", guard.decide(self.env(), self.payload()))
        self.assertIsNone(guard.decide(self.env(), self.payload()))
        self.assertEqual([e["rule"] for e in self.events()], ["manager-expiry-1"])

    def test_a_compaction_fires_once_and_a_second_one_fires_again(self):
        self.write(turn(5, "a", 30_000), extra=[{"type": "system", "subtype": "compact_boundary"}])
        self.assertIn("after a compaction", guard.decide(self.env(), self.payload()))
        self.assertIsNone(guard.decide(self.env(), self.payload()))
        self.write(turn(5, "a", 30_000), extra=[{"type": "system", "subtype": "compact_boundary"}] * 2)
        self.assertIn("after a compaction", guard.decide(self.env(), self.payload()))

    def test_over_100k_then_a_compaction_is_a_new_event(self):
        self.write(turn(5, "a", 144_000))
        self.assertTrue(guard.decide(self.env(), self.payload()))
        self.write(turn(5, "a", 20_000), turn(1, "b", 20_000), extra=[{"type": "system", "subtype": "compact_boundary"}])
        self.assertIn("after a compaction", guard.decide(self.env(), self.payload()))

    def test_goal_manager_logs_to_the_goal_folder(self):
        goal = Path(self.tmp.name) / "squad" / "goals" / "g"
        goal.mkdir(parents=True)
        self.write(turn(5, "a", 144_000))
        env = self.env()
        env.pop("SCOPE_DIR")
        env["GOAL_DIR"] = str(goal)
        self.assertTrue(guard.decide(env, self.payload()))
        self.assertTrue((goal / "usage-events.jsonl").exists())

    def test_tooling_problems_give_nothing(self):
        self.write(turn(5, "a", 144_000))
        for label, env, payload in (
            ("no session id", self.env(), {**self.payload(), "session_id": None}),
            ("no transcript", self.env(), {**self.payload(), "transcript_path": str(self.transcript_path) + ".gone"}),
            ("no SQUAD_NAME", {k: v for k, v in self.env().items() if k != "SQUAD_NAME"}, self.payload()),
            ("home missing", self.env(SCOPE_DIR=str(self.scope / "nope")), self.payload()),
            ("no tool_input", self.env(), {"session_id": "s"}),
        ):
            with self.subTest(label):
                self.assertIsNone(guard.decide(env, payload))

    def test_unwritable_log_stays_silent(self):
        self.write(turn(5, "a", 144_000))
        self.log.mkdir()  # a directory where the log file should be
        self.assertIsNone(guard.decide(self.env(), self.payload()))

    def test_unreadable_log_lines_do_not_break_the_check(self):
        self.write(turn(5, "a", 144_000))
        self.log.write_text("not json\n[1]\n{}\n", encoding="utf-8")
        self.assertTrue(guard.decide(self.env(), self.payload()))


class CliTest(GuardBase):
    def run_guard(self, env, payload, script=BIN / "squad-manager-guard", stdin=None):
        e = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        e.update(env)
        return subprocess.run([sys.executable, str(script)], input=json.dumps(payload) if stdin is None else stdin,
                               text=True, encoding="utf-8", env=e, capture_output=True, timeout=20)

    def test_notice_is_additional_context_json_on_stdout_and_exit_0(self):
        self.write(turn(5, "a", 144_000))
        r = self.run_guard(self.env(), self.payload())
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertIn("squad-respawn mgr", out["additionalContext"])
        self.assertNotIn("permissionDecision", out)  # never blocks
        self.assertEqual(r.stderr, "")

    def test_no_notice_means_empty_output(self):
        self.write(turn(5, "a", 144_000))
        for env, payload in ((self.env("tech-lead"), self.payload()), (self.env(), self.payload("ls"))):
            r = self.run_guard(env, payload)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_garbage_payloads_exit_0_silently(self):
        for stdin in ("not json", "", "[1]", "null"):
            with self.subTest(stdin=stdin):
                r = self.run_guard(self.env(), None, stdin=stdin)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_missing_squad_usage_exits_0_silently(self):
        self.write(turn(5, "a", 144_000))
        bin2 = Path(self.tmp.name) / "bin2"
        bin2.mkdir()
        for name in ("squad-manager-guard", "squadio.py", "squadtranscript.py"):
            shutil.copy(BIN / name, bin2 / name)  # everything but squad-usage
        r = self.run_guard(self.env(), self.payload(), script=bin2 / "squad-manager-guard")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.events(), [])

    def test_no_jq_dependency(self):
        self.write(turn(5, "a", 144_000))
        src = (BIN / "squad-manager-guard").read_text(encoding="utf-8")
        self.assertNotIn("jq", src.replace("no jq dependency", ""))
        r = self.run_guard({**self.env(), "PATH": "/nonexistent"}, self.payload())  # no jq on PATH: still works
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("additionalContext", r.stdout)

    def test_unreadable_transcript_exits_0_silently(self):
        self.transcript_path.write_bytes(b"\xff\xfe\x00 not a transcript\n")
        r = self.run_guard(self.env(), self.payload())
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_parallel_calls_give_one_notice_and_one_log_line(self):
        self.write(turn(5, "a", 144_000))
        e = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        e.update(self.env())
        for rnd in range(8):
            self.log.unlink(missing_ok=True)
            procs = [subprocess.Popen([sys.executable, str(BIN / "squad-manager-guard")], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, text=True, env=e) for _ in range(4)]
            outs = [p.communicate(json.dumps(self.payload()))[0] for p in procs]
            self.assertEqual(sum(1 for o in outs if "additionalContext" in o), 1, (rnd, outs))
            self.assertEqual(len(self.events()), 1, rnd)
            self.assertFalse(Path(str(self.log) + ".lock").exists())

    def test_a_stale_lock_is_taken_over(self):
        self.write(turn(5, "a", 144_000))
        lock = Path(str(self.log) + ".lock")
        lock.mkdir()
        old = time.time() - 60
        os.utime(lock, (old, old))
        self.assertTrue(guard.decide(self.env(), self.payload()))

    def test_stop_hook_still_exempts_the_manager(self):
        self.write(turn(5, "a", 144_000))
        stop = BIN / "squad-usage-hook"
        e = {**os.environ, **self.env(), "CLAUDE_CONFIG_DIR": str(Path(self.tmp.name) / "cfg")}
        r = subprocess.run([str(stop)], input=json.dumps({"session_id": "sid-1", "transcript_path": str(self.transcript_path)}),
                           text=True, env=e, capture_output=True, timeout=20)
        self.assertEqual((r.returncode, r.stderr), (0, ""))


if __name__ == "__main__":
    unittest.main()
