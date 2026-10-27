"""Seam B: the SendMessage hook. Payload on stdin in, line in messages.jsonl out."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-log-message"


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
        return subprocess.run([str(SCRIPT)], input=stdin, text=True, encoding="utf-8", env=env,
                              capture_output=True, timeout=10)

    def records(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def run_hook_in(self, home_env, data=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_NAME="dev-1", SQUAD_DIR=str(self.squad), **home_env)
        return subprocess.run([str(SCRIPT)], input=json.dumps(data or payload()), text=True, encoding="utf-8", env=env,
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

    def test_bare_number_ids_after_the_type(self):
        for text, want in (("HANDIN 03: commit abc123", "03"), ("HANDIN SET-13: x", "SET-13"), ("FAIL 3: x", "3"),
                           ("PASS 12", "12"), ("STATUS: building SET-01", "SET-01"), ("hello 03", None)):
            self.run_hook(payload(text))
        self.assertEqual([r["task"] for r in self.records()], ["03", "SET-13", "3", "12", "SET-01", None])

    def test_first_task_id_wins(self):
        self.run_hook(payload("BLOCKED SET-01: AC-033 contradicts spec §4"))
        self.assertEqual(self.records()[0]["task"], "SET-01")

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


    # ---- 3rd return notice: Team Lead iff `team-lead` is on the team, else Manager (AC 12) ----
    def third_fail_notice(self, scope_md):
        scope = self.squad / "scopes" / "sc1"
        scope.mkdir(parents=True, exist_ok=True)
        (scope / "scope.md").write_text(scope_md, encoding="utf-8", newline="")
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

    def test_third_return_goes_to_manager_without_team_lead(self):
        out = self.third_fail_notice("team: qa-white, qa-black\n")
        self.assertIn("to Manager [LC-7c]", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_third_return_goes_to_manager_for_none_undecided_error_and_size(self):
        for text in ("team: none\n", "team:\n", "team: ba, nobody\n", "size: L\n", "team: team-lead; touch X\n"):
            with self.subTest(text=text):
                self.setUp()
                out = self.third_fail_notice(text)
                self.assertIn("to Manager [LC-7c]", json.loads(out)["hookSpecificOutput"]["additionalContext"])
                self.assertFalse((self.squad / "scopes" / "sc1" / "X").exists())
                self.tearDown()

    def test_third_return_notice_text_has_no_size_word(self):
        out = self.third_fail_notice("team: team-lead\n")
        self.assertNotRegex(out.lower(), r"\bsize\b")


if __name__ == "__main__":
    unittest.main()
