"""squad-merge-record: a Manager `git merge squad/...` records `merged` in the task-event store (design.md s5.3)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from squadtest import BIN

sys.path.insert(0, str(BIN))
sys.dont_write_bytecode = True
import squadledger  # noqa: E402
import squadtask  # noqa: E402

HOOK = BIN / "squad-merge-record"
BRANCH = "squad/plugin/s1/dev"
ROSTER = """| Agent | Role | Scope | Owns | Status | Session |
| --- | --- | --- | --- | --- | --- |
| qaw | qa-whitebox | s1 | x | live | c |
| dev | dev | s1 |  | live | f |
"""


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


class MergeRecord(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo, self.sd = root / "repo", root / "squad"  # T23: a temp store, never the real one
        self.home = self.sd / "scopes" / "s1"
        self.home.mkdir(parents=True)
        (self.home / "scope.md").write_text("x\n", encoding="utf-8")
        (self.home / "roster.md").write_text(ROSTER, encoding="utf-8")
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "base")
        git(self.repo, "checkout", "-q", "-b", BRANCH)
        (self.repo / "f").write_text("x", encoding="utf-8")
        git(self.repo, "add", "f")
        git(self.repo, "commit", "-q", "-m", "work")
        git(self.repo, "checkout", "-q", "main")
        squadtask.record(self.home, "06", "claim", by="dev", branch=BRANCH)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, cmd="git merge --no-ff " + BRANCH, role="manager", resp=None, merge=True):
        if merge:
            git(self.repo, "merge", "-q", "--no-ff", "-m", "m", BRANCH)
        env = {**os.environ, "SQUAD_ROLE": role, "SQUAD_NAME": "mgr", "SQUAD_DIR": str(self.sd)}
        env.pop("SCOPE_DIR", None)
        payload = {"tool_name": "Bash", "cwd": str(self.repo), "tool_input": {"command": cmd},
                   "tool_response": resp or {"stdout": "Merge made", "stderr": ""}}
        r = subprocess.run([str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)  # T1
        return r.stdout

    def events(self):
        return squadtask.read_events(self.sd, "s1")

    def merged(self):
        return [e for e in self.events() if e["ev"] == "merged"]

    def test_manager_merge_records_merged_with_w7_when_not_passed(self):  # AC6 record side, W7
        out = self.run_hook()
        (e,) = self.merged()
        self.assertEqual((e["branch"], e["by"], e["role"], e["task"]), (BRANCH, "mgr", "manager", "06"))
        self.assertEqual(e["sha"], git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(e["warn"], ["W7 merged before it passed"])  # saved in the event (D4)
        self.assertIn("W7 merged before it passed", json.loads(out)["hookSpecificOutput"]["additionalContext"])
        self.assertTrue(squadtask.fold(self.events())[squadledger.key("06")]["merged_ts"])

    def test_passed_ticket_merges_without_warning_and_once(self):
        squadtask.record(self.home, "06", "handin", by="dev", sha="abc1234", branch=BRANCH)
        squadtask.record(self.home, "06", "pass", by="qaw", slot="qaw", sha="abc1234")
        self.assertEqual(self.run_hook(), "")
        self.assertEqual(self.merged()[0]["warn"], [])
        self.run_hook(merge=False)  # a second run does not double-record
        self.assertEqual(len(self.merged()), 1)

    def test_nothing_recorded_for_other_roles_commands_or_a_branch_not_in_head(self):
        self.run_hook(role="dev")  # not the Manager
        self.run_hook(cmd="git log squad/x", merge=False)  # not a merge
        self.assertEqual(self.merged(), [])
        git(self.repo, "reset", "-q", "--hard", "HEAD~1")  # the merge did not land (conflict, abort, --no-commit)
        self.run_hook(merge=False)
        self.assertEqual(self.merged(), [])
        self.run_hook(cmd="git merge squad/plugin/other/dev", merge=False)  # a branch no ticket has
        self.assertEqual(self.merged(), [])
