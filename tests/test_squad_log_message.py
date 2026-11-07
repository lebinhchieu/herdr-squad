"""Seam B: the SendMessage hook. Payload on stdin in, line in messages.jsonl out."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import winlaunch

from squadtest import BIN

SCRIPT = BIN / "squad-log-message"


def payload(message="HANDIN SET-01: branch squad/dev-1, commit abc123", to="qa-w-settings",
            tool="SendMessage", success=True, msg_id="m-1", **input_overrides):
    tool_input = {"to": to, "summary": "s", "message": message, "type": "message",
                  "recipient": to, "recipient_kind": "name", "content": message[:20] + "…"}
    tool_input.update(input_overrides)
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "session_id": "sess",
            "tool_input": tool_input,
            "tool_response": {"success": success, "msg_id": msg_id}}


class LogMessageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = Path(self.tmp.name) / "squad"
        (self.squad / "iterations").mkdir(parents=True)
        self.log = self.squad / "messages.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, data, squad_name="dev-settings-1", raw=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        if squad_name is not None:
            env.update(SQUAD_NAME=squad_name, SQUAD_DIR=str(self.squad))
        stdin = raw if raw is not None else json.dumps(data)
        return winlaunch.run_script(SCRIPT, input=stdin, text=True, encoding="utf-8", env=env,
                              capture_output=True, timeout=10)

    def records(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def run_hook_in(self, home_env, data=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad), **home_env)
        return winlaunch.run_script(SCRIPT, input=json.dumps(data or payload()), text=True, encoding="utf-8", env=env,
                              capture_output=True, timeout=10)

    def test_scope_agent_logs_into_its_scope_folder_with_that_scopes_iteration(self):
        scope = self.squad / "scopes" / "sc1"
        (scope / "iterations").mkdir(parents=True)
        (scope / "iterations" / "3.md").write_text("x", encoding="utf-8")
        (self.squad / "iterations" / "9.md").write_text("x", encoding="utf-8")
        self.assertEqual(self.run_hook_in({"SCOPE_DIR": str(scope)}).returncode, 0)
        [rec] = [json.loads(l) for l in (scope / "messages.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rec["iteration"], 3)
        self.assertFalse(self.log.exists())

    def test_goal_manager_logs_into_the_goal_folder(self):
        goal = self.squad / "goals" / "g1"
        goal.mkdir(parents=True)
        self.run_hook_in({"GOAL_DIR": str(goal)})
        self.assertTrue((goal / "messages.jsonl").exists())
        self.assertFalse(self.log.exists())

    def test_scope_dir_wins_over_goal_dir(self):
        scope, goal = self.squad / "scopes" / "sc1", self.squad / "goals" / "g1"
        scope.mkdir(parents=True)
        goal.mkdir(parents=True)
        self.run_hook_in({"SCOPE_DIR": str(scope), "GOAL_DIR": str(goal)})
        self.assertTrue((scope / "messages.jsonl").exists())
        self.assertFalse((goal / "messages.jsonl").exists())

    def test_typed_message_is_logged_with_type_task_and_sender(self):
        (self.squad / "iterations" / "1.md").write_text("x", encoding="utf-8")
        (self.squad / "iterations" / "2.md").write_text("x", encoding="utf-8")
        (self.squad / "iterations" / "10.md").write_text("x", encoding="utf-8")
        r = self.run_hook(payload())
        self.assertEqual(r.returncode, 0, r.stderr)
        [rec] = self.records()
        self.assertEqual(rec["from"], "dev-settings-1")
        self.assertEqual(rec["to"], "qa-w-settings")
        self.assertEqual(rec["type"], "HANDIN")
        self.assertEqual(rec["task"], "SET-01")
        self.assertEqual(rec["msg_id"], "m-1")
        self.assertEqual(rec["text"], "HANDIN SET-01: branch squad/dev-1, commit abc123")
        self.assertEqual(rec["iteration"], 10)
        self.assertRegex(rec["ts"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d")

    def test_status_with_colon_finds_task_later_in_text(self):
        self.run_hook(payload("STATUS: building SET-01, 60%, no blockers", to="manager"))
        [rec] = self.records()
        self.assertEqual((rec["type"], rec["task"]), ("STATUS", "SET-01"))

    def test_untyped_message_has_null_type_and_task(self):
        self.run_hook(payload("hello there, quick question"))
        [rec] = self.records()
        self.assertIsNone(rec["type"])
        self.assertIsNone(rec["task"])

    def test_typed_message_without_task(self):
        self.run_hook(payload("ANSWER: yes, see requirements note in project.md#reqs"))
        [rec] = self.records()
        self.assertEqual((rec["type"], rec["task"]), ("ANSWER", None))

    def test_type_must_be_the_leading_word(self):
        self.run_hook(payload("I will HANDIN SET-01 soon"))
        self.assertIsNone(self.records()[0]["type"])

    def test_recipient_used_when_to_missing(self):
        p = payload()
        del p["tool_input"]["to"]
        self.run_hook(p)
        self.assertEqual(self.records()[0]["to"], "qa-w-settings")

    def test_full_message_not_truncated_content(self):
        long = "DECISION SET-02: " + "x" * 300
        self.run_hook(payload(long))
        self.assertEqual(self.records()[0]["text"], long)

    def test_no_iterations_gives_null_iteration(self):
        self.run_hook(payload())
        self.assertIsNone(self.records()[0]["iteration"])

    def test_messages_append(self):
        self.run_hook(payload(msg_id="a"))
        self.run_hook(payload("PASS SET-01", to="dev-settings-1", msg_id="b"),
                      squad_name="qa-w-settings")
        self.assertEqual([r["msg_id"] for r in self.records()], ["a", "b"])

    def test_outside_a_squad_nothing_is_written(self):
        r = self.run_hook(payload(), squad_name=None)
        self.assertEqual(r.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_failed_send_is_not_logged(self):
        self.run_hook(payload(success=False))
        self.assertEqual(self.records(), [])

    def test_other_tools_are_ignored(self):
        self.run_hook(payload(tool="ToolSearch"))
        self.assertEqual(self.records(), [])

    def test_bad_input_never_fails_the_agent(self):
        r = self.run_hook(None, raw="not json{")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.records(), [])


    def qa_roster(self, scope, rows="| qa-w | qa-whitebox | sc1 |  | live | s |\n"):
        """A scope roster: with a QA row the task-state hook does not run the evidence check (design D9)."""
        head = "| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n"
        (scope / "roster.md").write_text(head + rows, encoding="utf-8")

    # ---- 3rd return notice: Team Lead iff `team-lead` is on the team, else Manager (AC 12) ----
    def third_fail_notice(self, scope_md):
        scope = self.squad / "scopes" / "sc1"
        scope.mkdir(parents=True, exist_ok=True)
        (scope / "scope.md").write_text(scope_md, encoding="utf-8", newline="")
        self.qa_roster(scope)
        lines = [payload("HANDIN 07: branch b, commit aaa1111", msg_id="h1"), payload("FAIL 07: a", msg_id="f1"),
                 payload("HANDIN 07: branch b, commit bbb2222", msg_id="h2"), payload("FAIL 07: b", msg_id="f2"),
                 payload("HANDIN 07: branch b, commit ccc3333", msg_id="h3")]
        for d in lines:
            self.run_hook_in({"SCOPE_DIR": str(scope)}, d)
        r = self.run_hook_in({"SCOPE_DIR": str(scope)}, payload("FAIL 07: c", msg_id="f3"))
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def test_third_return_goes_to_team_lead_when_on_the_team(self):
        out = self.third_fail_notice("team: ba, team-lead, tech-lead, qa-white\n")
        self.assertIn("to Team Lead [LC-7b]", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_third_return_goes_to_manager_for_none_undecided_error_and_size(self):
        for text in ("team: none\n", "team:\n", "team: ba, nobody\n", "size: L\n", "team: team-lead; touch X\n"):
            with self.subTest(text=text):
                self.setUp()
                out = self.third_fail_notice(text)
                self.assertIn("to Manager [LC-7c]", json.loads(out)["hookSpecificOutput"]["additionalContext"])
                self.assertFalse((self.squad / "scopes" / "sc1" / "X").exists())
                self.tearDown()

    def test_the_notice_is_stdout_json_on_the_third_failing_sha_only(self):
        """AC 12 observability: stdout `hookSpecificOutput.additionalContext`; nothing for 2 returns or 3 FAILs on one sha."""
        scope = self.squad / "scopes" / "sc1"
        scope.mkdir(parents=True, exist_ok=True)
        (scope / "scope.md").write_text("team: team-lead\n", encoding="utf-8")
        self.qa_roster(scope)
        seq = [("HANDIN 07: branch b, commit aaa1111", False), ("FAIL 07: a", False), ("FAIL 07: a again", False),
               ("FAIL 07: a thrice", False), ("HANDIN 07: branch b, commit bbb2222", False), ("FAIL 07: b", False),
               ("HANDIN 07: branch b, commit ccc3333", False), ("FAIL 07: c", True)]
        for i, (text, notice) in enumerate(seq):
            r = self.run_hook_in({"SCOPE_DIR": str(scope)}, payload(text, msg_id=f"m{i}"))
            self.assertEqual("has 3 returns" in r.stdout, notice, (text, r.stdout))  # a task-state warning (W3) may share stdout
            if notice:
                ctx = json.loads(r.stdout)["hookSpecificOutput"]
                self.assertEqual(ctx["hookEventName"], "PostToolUse")
                self.assertIn("task 07 has 3 returns", ctx["additionalContext"])

    def test_a_stale_lock_dir_does_not_wedge_the_append(self):  # ticket 06: no flock, lock left by a killed writer
        lock = Path(str(self.log) + ".lock")
        lock.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad))
        env = winlaunch.no_flock_env(env, self.tmp.name)
        for n in (1, 2):
            r = winlaunch.run_script(SCRIPT, input=json.dumps(payload(msg_id=f"m{n}")), text=True, encoding="utf-8",
                                     env=env, capture_output=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(self.records()), n)
            self.assertFalse(lock.exists())

    # ---- task state (ticket 02): the hook hands each record to squad-task ----
    def task_hook(self, text, sender="dev-1", msg_id="m", env_extra=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_NAME=sender, SQUAD_DIR=str(self.sd), SCOPE_DIR=str(self.sc), **(env_extra or {}))
        r = winlaunch.run_script(SCRIPT, input=json.dumps(payload(text, msg_id=msg_id)), text=True, encoding="utf-8",
                                 env=env, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)  # T1: always exit 0
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout.strip() else ""
        return ctx

    def task_events(self):
        f = self.sd / "task-events" / "sc1.jsonl"
        return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []

    def project(self, rows):
        """<project>/.claude/squads/sq/scopes/sc1 with the roster `rows`; the Developer worktree is <project>/.worktrees/sq/sc1/dev-1."""
        self.proj = Path(self.tmp.name) / "proj"
        self.sd = self.proj / ".claude" / "squads" / "sq"
        self.sc = self.sd / "scopes" / "sc1"
        self.sc.mkdir(parents=True)
        self.qa_roster(self.sc, rows)

    def test_qa_team_records_handin_pass_fail_blocked_and_warns_by_context(self):  # AC3, AC5, T5
        self.project("| dev-1 | dev | sc1 |  | live | s |\n| qa-w | qa-whitebox | sc1 |  | live | s |\n")
        ctx = self.task_hook("HANDIN 02: branch squad/sq/sc1/dev-1, commit abc1234", msg_id="h")
        self.assertIn("W3", ctx)  # no claim on record
        self.assertEqual([e["ev"] for e in self.task_events()], ["handin"])  # QA on the roster: no evidence check, no pass
        self.assertEqual(self.task_hook("PASS 02: ok", sender="qa-w", msg_id="p"), "")
        self.assertIn("W4", self.task_hook("PASS 02: ok", sender="mgr", msg_id="p2"))  # not a checker: no event
        self.task_hook("BLOCKED 02: waiting on 01", msg_id="b")
        evs = self.task_events()
        self.assertEqual([(e["ev"], e["by"]) for e in evs], [("handin", "dev-1"), ("pass", "qa-w"), ("blocked", "dev-1")])
        self.assertEqual(evs[1]["slot"], "qa-w")
        self.assertTrue(evs[0]["warn"][0].startswith("W3"))  # saved in the event (D4)

    def test_pass_with_no_sha_and_ask_and_evidence_sha_handin_write_what_they_should(self):  # T5
        self.project("| qa-w | qa-whitebox | sc1 |  | live | s |\n")
        self.task_hook("HANDIN 02: branch b, commit abc1234", msg_id="h")
        self.task_hook("ASK 02: which file?", msg_id="a")
        self.task_hook("HANDIN 02: evidence sha def5678", msg_id="e")
        self.task_hook("PASS 02: idle, no sha named", sender="qa-w", msg_id="p")
        self.assertEqual([e["ev"] for e in self.task_events()], ["handin", "pass"])
        self.assertIsNone(self.task_events()[1]["sha"])
        # real messages from the repo's own scopes (REV-4): a HANDIN `..sha` and a FAIL naming a sha, from non-roster senders
        self.task_hook("HANDIN 03: diff check 90dbd7c..148a5f9. One line in bin/squad-watchdog (read of /proc/version gets encoding).",
                       sender="plugin-dev-watchdog-2", msg_id="r1")
        self.task_hook("FAIL 06: one finding, AC4 evidence. The screenshots were made at 1b59666; 210876f changed palette.",
                       sender="plugin-mgr-process-audit", msg_id="r2")
        evs = self.task_events()
        self.assertEqual([(e["ev"], e["task"], e["sha"]) for e in evs[-2:]], [("handin", "03", "148a5f9"), ("fail", "06", "1b59666")])

    def test_the_third_return_notice_and_the_task_warning_share_one_context(self):
        self.project("| qa-w | qa-whitebox | sc1 |  | live | s |\n")
        (self.sc / "scope.md").write_text("team: team-lead\n", encoding="utf-8")
        for i, sha in enumerate(("aaa1111", "bbb2222", "ccc3333")):
            self.task_hook(f"HANDIN 07: branch b, commit {sha}", msg_id=f"h{i}")
            if i < 2:
                self.task_hook(f"FAIL 07: bad {sha}", sender="qa-w", msg_id=f"f{i}")
        ctx = self.task_hook("FAIL 07: bad ccc3333", sender="qa-w", msg_id="f2")
        self.assertIn("task 07 has 3 returns", ctx)

    def test_no_qa_team_valid_evidence_passes_and_a_missing_image_is_w9(self):  # T19, AC4
        self.project("| dev-1 | dev | sc1 |  | live | s |\n")
        wt = self.proj / ".worktrees" / "sq" / "sc1" / "dev-1"
        folder = wt / ".scratch" / "sc1" / "issues" / "02-x"
        (folder / "img").mkdir(parents=True)
        (folder.parent / "02-x.md").write_text("# 02\n", encoding="utf-8")
        git = lambda *a: subprocess.run(["git", "-C", str(wt), *a], capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q")
        git("config", "user.email", "t@t")
        git("config", "user.name", "t")

        def commit(body, image):
            if image:
                (folder / "img" / "a.png").write_bytes(b"png")
            (folder / "evidence.md").write_text(body, encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "c")
            return git("rev-parse", "HEAD")

        bad = commit("## Behaviour\n![a](img/gone.png)\n", False)
        ctx = self.task_hook(f"HANDIN 02: branch squad/sq/sc1/dev-1, commit {bad}", msg_id="h1")
        self.assertIn("W9 evidence check failed", ctx)
        self.assertIn("gone.png", ctx)  # the check ran and named the image, not the "not checked" fallback
        self.assertEqual([e["ev"] for e in self.task_events()], ["handin"])
        good = commit("## Behaviour\n![a](img/a.png)\n", True)
        self.task_hook(f"HANDIN 02: branch squad/sq/sc1/dev-1, commit {good}", msg_id="h2")
        last = self.task_events()[-1]
        self.assertEqual((last["ev"], last["slot"], last["by"]), ("pass", "evidence", "hook"))

    def test_a_store_that_cannot_be_written_still_exits_0_and_a_goal_manager_is_skipped(self):  # T1
        self.project("| qa-w | qa-whitebox | sc1 |  | live | s |\n")
        (self.sd / "task-events").write_text("a file, not a folder", encoding="utf-8")
        self.task_hook("HANDIN 02: branch b, commit abc1234")
        self.assertEqual(len((self.sc / "messages.jsonl").read_text(encoding="utf-8").splitlines()), 1)  # still logged
        goal = self.sd / "goals" / "g1"
        goal.mkdir(parents=True)
        (self.sd / "task-events").unlink()
        self.run_hook_in({"GOAL_DIR": str(goal)}, payload("HANDIN 02: branch b, commit abc1234"))
        self.assertFalse((self.sd / "task-events").exists())


if __name__ == "__main__":
    unittest.main()
