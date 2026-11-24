"""Hooks find a resumed session (no SQUAD_* variables) in roster.md by its session id (ticket 11).
Fixtures are two real rosters of this squad: scope-roster.md (scope upstream-proposals) and goal-roster.md (goal process-fixes)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import winlaunch
from squadtest import BIN, GIT_ENV, clean_env

sys.path.insert(0, str(BIN))
import squadsession  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "session_lookup"
MGR, QAW, DEV, RETIRED = ("2b2bbc79-8708-45e3-8c15-b00c24fdb0df", "98789c41-dc76-459b-9edc-8ace94161d14",
                          "c7a0caa3-8754-4808-8445-adb3b988a526", "7eef7d82-874b-4029-bc3e-90cec4e6f528")
GOAL_MGR = "8993fe3f-7d89-4fa1-a5bc-a649ca59646f"
HOOKS = ("squad-log-message", "squad-usage-hook", "squad-lazy-hook", "squad-notify", "squad-path-guard",
         "squad-manager-guard", "squad-merge-record", "squad-away-hook")


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve() / "proj"
        self.squad = self.root / ".claude" / "squads" / "plugin"
        self.scope = self.squad / "scopes" / "upstream-proposals"
        self.goal = self.squad / "goals" / "process-fixes"
        for d in (self.scope / "iterations", self.goal):
            d.mkdir(parents=True)
        shutil.copy(FIX / "scope-roster.md", self.scope / "roster.md")
        shutil.copy(FIX / "goal-roster.md", self.goal / "roster.md")
        (self.scope / "scope.md").write_text("# Scope\n\ngoal: \n", encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.root)  # the process cwd is a lookup candidate: keep it out of the real project

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def resolve(self, sid, cwd=None, env=None):
        return squadsession.resolve(env or {}, {"session_id": sid, "cwd": str(cwd or self.root)})

    def hook(self, name, payload, env=None, cwd=None, script=None):
        return winlaunch.run_script(script or BIN / name, input=json.dumps(payload), text=True, encoding="utf-8",
                                    env=clean_env(**(env or {})), cwd=cwd or self.root, capture_output=True, timeout=20)


class ResolveTest(Project):
    def test_developer_row_from_a_worktree_cwd(self):
        wt = self.root / ".worktrees" / "plugin" / "upstream-proposals" / "plugin-dev-upstream-proposals-11"
        wt.mkdir(parents=True)
        self.assertEqual(self.resolve(DEV, cwd=wt), {
            "SQUAD_NAME": "plugin-dev-upstream-proposals-11", "SQUAD_ROLE": "dev", "SQUAD_SCOPE": "upstream-proposals",
            "SQUAD_DIR": str(self.squad), "SCOPE_DIR": str(self.scope)})

    def test_worktree_outside_the_project_finds_the_main_checkout_through_git(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, env={**os.environ, **GIT_ENV})
        subprocess.run(["git", "-C", str(self.root), "commit", "-q", "--allow-empty", "-m", "x"], check=True, env={**os.environ, **GIT_ENV})
        wt = Path(self.tmp.name).resolve() / "elsewhere"
        subprocess.run(["git", "-C", str(self.root), "worktree", "add", "-q", str(wt), "-b", "b"], check=True)
        self.assertEqual(self.resolve(QAW, cwd=wt)["SQUAD_ROLE"], "qa-whitebox")

    def test_goal_manager_row_gives_goal_dir_and_no_scope(self):
        self.assertEqual(self.resolve(GOAL_MGR), {"SQUAD_NAME": "plugin-mgr-process-fixes", "SQUAD_ROLE": "manager",
                                                  "SQUAD_DIR": str(self.squad), "GOAL_DIR": str(self.goal)})

    def test_scope_inside_a_goal_gets_both_folders(self):
        (self.scope / "scope.md").write_text("# Scope\n\ngoal: process-fixes\n", encoding="utf-8")
        r = self.resolve(MGR)
        self.assertEqual((r["SCOPE_DIR"], r["GOAL_DIR"]), (str(self.scope), str(self.goal)))

    def test_flat_roster(self):
        shutil.rmtree(self.scope)
        shutil.copy(FIX / "scope-roster.md", self.squad / "roster.md")
        r = self.resolve(MGR)
        self.assertEqual((r["SQUAD_NAME"], r["SQUAD_DIR"], "SCOPE_DIR" in r), ("plugin-mgr-upstream-proposals", str(self.squad), False))

    def test_done_roster_is_ignored(self):
        (self.squad / "scopes" / "_done").mkdir()
        shutil.move(str(self.scope), str(self.squad / "scopes" / "_done" / "x"))
        self.assertIsNone(self.resolve(MGR))

    def test_session_cell_that_only_contains_the_id_is_no_match(self):
        roster = self.scope / "roster.md"
        roster.write_text(roster.read_text(encoding="utf-8").replace(MGR, MGR + " (old)"), encoding="utf-8")
        self.assertIsNone(self.resolve(MGR))
        self.assertIsNone(self.resolve(MGR[:12]))

    def test_name_that_fails_the_pattern_is_no_match(self):
        roster = self.scope / "roster.md"
        roster.write_text(roster.read_text(encoding="utf-8").replace("plugin-mgr-upstream-proposals", "Bad Name;x"), encoding="utf-8")
        self.assertIsNone(self.resolve(MGR))

    def test_environment_wins(self):
        env = {"SQUAD_NAME": "someone", "SQUAD_DIR": str(self.squad)}
        self.assertIsNone(self.resolve(MGR, env=env))
        self.assertEqual(squadsession.fill(env, {"session_id": MGR, "cwd": str(self.root)}), env)


class HookTest(Project):
    def message(self, sid, **kw):
        return {"hook_event_name": "PostToolUse", "tool_name": "SendMessage", "session_id": sid, "cwd": str(self.root),
                "tool_input": {"to": "x", "message": "STATUS 11: ok"}, "tool_response": {"success": True, "msg_id": "m"}, **kw}

    def log(self):
        f = self.scope / "messages.jsonl"
        return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []

    def test_resumed_session_logs_as_its_roster_row(self):
        r = self.hook("squad-log-message", self.message(QAW))
        self.assertEqual(r.returncode, 0)
        [rec] = self.log()
        self.assertEqual(rec["from"], "plugin-qaw-upstream-proposals")

    def test_unknown_empty_or_unreadable_session_stays_silent(self):
        for sid in ("11111111-no-such-session", ""):
            with self.subTest(sid=sid):
                r = self.hook("squad-log-message", self.message(sid))
                self.assertEqual((r.returncode, r.stdout, r.stderr, self.log()), (0, "", "", []))
        (self.scope / "roster.md").unlink()
        (self.scope / "roster.md").mkdir()  # cannot be read as a file
        r = self.hook("squad-log-message", self.message(QAW))
        self.assertEqual((r.returncode, r.stdout, r.stderr, self.log()), (0, "", "", []))

    def test_environment_wins_over_the_roster(self):
        self.hook("squad-log-message", self.message(QAW), env={"SQUAD_NAME": "other", "SQUAD_DIR": str(self.squad), "SCOPE_DIR": str(self.scope)})
        self.assertEqual([r["from"] for r in self.log()], ["other"])

    def test_resumed_qa_is_stopped_by_the_path_guard_and_a_resumed_dev_is_not(self):
        write = {"session_id": QAW, "cwd": str(self.root), "tool_input": {"file_path": str(self.root / "x.md")}}
        r = self.hook("squad-path-guard", write)
        self.assertEqual(r.returncode, 2)
        self.assertIn("[FILE-11]", r.stderr)
        self.assertEqual(self.hook("squad-path-guard", {**write, "session_id": DEV}).returncode, 0)
        self.assertEqual(self.hook("squad-path-guard", {**write, "session_id": "unknown"}).returncode, 0)

    def test_resumed_manager_is_covered_by_the_manager_guard(self):
        ts = "2026-11-24T10:00:00Z"
        line = lambda i, ctx, tool=None: json.dumps({"type": "assistant", "timestamp": ts, "sessionId": "s", "message": {
            "id": i, "model": "claude-sonnet-5-5", "content": [{"type": "tool_use", "name": tool, "input": {}}] if tool else [],
            "usage": {"input_tokens": 2, "cache_read_input_tokens": ctx, "cache_creation_input_tokens": 0, "output_tokens": 9}}})
        tp = Path(self.tmp.name) / "t.jsonl"
        tp.write_text(line("a", 60_000, "Write") + "\n" + line("b", 400_000) + "\n", encoding="utf-8")
        p = {"session_id": MGR, "cwd": str(self.root), "transcript_path": str(tp), "tool_input": {"command": "squad-spawn x"}}
        r = self.hook("squad-manager-guard", p)
        self.assertIn("squad-respawn plugin-mgr-upstream-proposals", json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.hook("squad-manager-guard", {**p, "session_id": QAW}).stdout, "")  # not a Manager

    def test_every_squad_hook_of_hooks_json_calls_the_lookup(self):
        hooks = json.loads((BIN.parent / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        listed = {c.split("/bin/")[1].strip('"') for groups in hooks.values() for g in groups for h in g["hooks"]
                  for c in [h["command"]] if "/bin/squad-" in c}
        self.assertEqual(listed, set(HOOKS))
        for name in listed:
            text = (BIN / name).read_text(encoding="utf-8")
            self.assertTrue("squad-whoami" in text or "squadsession" in text, name)

    def test_a_session_with_the_variables_starts_no_squad_whoami(self):
        for name in ("squad-log-message", "squad-usage-hook", "squad-merge-record"):
            with self.subTest(hook=name):
                d = Path(self.tmp.name) / ("copy-" + name)
                d.mkdir()
                shutil.copy(BIN / name, d / name)
                stub = d / "squad-whoami"
                stub.write_text("#!/bin/sh\ntouch %s\n" % (d / "RAN"), encoding="utf-8", newline="\n")
                stub.chmod(0o755)
                env = {"SQUAD_NAME": "n", "SQUAD_DIR": str(self.squad), "SCOPE_DIR": str(self.scope), "SQUAD_ROLE": "dev"}
                msg = self.message(QAW)
                msg["tool_input"] = {"command": "git merge squad/x"}  # passes squad-merge-record's prefilter
                self.hook(name, msg, env=env, script=d / name)
                self.assertFalse((d / "RAN").exists())
                self.hook(name, msg, script=d / name)  # no variables: the stub is called
                self.assertTrue((d / "RAN").exists())


if __name__ == "__main__":
    unittest.main()
