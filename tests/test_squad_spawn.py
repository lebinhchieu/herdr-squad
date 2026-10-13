"""squad-spawn --dry-run: role defaults and session id."""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-spawn"
TABLE = {"manager": ("opus", "medium"), "tech-lead": ("sonnet", "high"), "ba": ("sonnet", "high"),
         "team-lead": ("sonnet", "medium"), "dev": ("sonnet", "medium"),
         "qa-whitebox": ("sonnet", "high"), "qa-blackbox": ("sonnet", "high"),
         "token-coach": ("sonnet", "medium")}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
if [[ "$1 $2" == "agent get" ]]; then
  [[ " ${LIVE:-} " == *" $3 "* ]] && { echo '{"result":{"agent":{"tab_id":"t0"}}}'; exit 0; }
  echo '{"error":{"code":"agent_not_found"}}'; exit 1
fi
[[ $1 == tab ]] && echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


class SpawnDryRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = Path(self.tmp.name) / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, *args):
        r = subprocess.run([str(SCRIPT), role, "x", "--dry-run", *args], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_role_defaults_match_the_table(self):
        for role, (model, effort) in TABLE.items():
            with self.subTest(role=role):
                self.assertRegex(self.spawn(role), rf"--model {model} --effort {effort}\b")

    def test_flags_override_role_defaults(self):
        self.assertRegex(self.spawn("dev", "--model", "opus", "--effort", "high"), r"--model opus --effort high\b")

    def test_dry_run_passes_a_session_id_and_plans_the_roster_write(self):
        out = self.spawn("dev")
        self.assertRegex(out, rf"--session-id {UUID}\b")
        self.assertRegex(out, rf"--set-session x {UUID}")

    def test_spawn_records_the_same_session_id_in_roster(self):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(log))
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n| manager | Manager | all | x | live |\n")
        r = subprocess.run([str(SCRIPT), "dev", "dev-1", "--scope", "s"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        passed = re.search(rf"--session-id ({UUID})", log.read_text()).group(1)
        self.assertIn(f"| dev-1 | dev | s |  | live | {passed} |", (self.squad / "roster.md").read_text())
        self.assertIn(passed, r.stdout)


    def _fake_herdr(self, live):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        self.log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.log), LIVE=live)
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n")

    def test_refuses_a_name_that_is_already_live_in_another_squad(self):
        self._fake_herdr(live="bill-ba-invoices")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already live", r.stderr)
        self.assertNotIn("tab create", self.log.read_text())

    def test_spawns_when_the_name_is_free(self):
        self._fake_herdr(live="other-name")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_every_role_has_settings_that_parse(self):
        settings = SCRIPT.parent.parent / "templates" / "squad" / "settings"
        for role in TABLE:
            with self.subTest(role=role):
                self.assertIn("permissions", json.loads((settings / f"{role}.json").read_text()))


def scoped_squad(root, goal_of_sc2="g1"):
    """A squad in the per-scope layout: scopes/sc1 (lone), scopes/sc2 (in goal g1), goals/g1."""
    squad = Path(root) / ".claude" / "squads" / "t"
    header = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
    for d, goal in (("scopes/sc1", ""), ("scopes/sc2", goal_of_sc2), ("goals/g1", None)):
        (squad / d).mkdir(parents=True)
        (squad / d / "roster.md").write_text(header)
        if goal is not None:
            (squad / d / "scope.md").write_text(f"# Scope\n\ngoal: {goal}\ntouches:\n")
    (squad / "process.md").write_text("x")
    return squad


class SpawnScopedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def run_spawn(self, role, name, *args):
        return subprocess.run([str(SCRIPT), role, name, "--dry-run", *args], env=self.env,
                              text=True, capture_output=True, timeout=10)

    def test_lone_scope_agent_gets_scope_dir_and_no_goal_dir(self):
        r = self.run_spawn("tech-lead", "t-tech-sc1", "--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--env SCOPE_DIR={self.squad}/scopes/sc1", r.stdout)
        self.assertIn("--env SQUAD_SCOPE=sc1", r.stdout)
        self.assertNotIn("GOAL_DIR", r.stdout)
        self.assertIn(f"--squad-dir {self.squad}/scopes/sc1 --set-session t-tech-sc1", r.stdout)

    def test_scope_in_a_goal_also_gets_goal_dir(self):
        r = self.run_spawn("tech-lead", "t-tech-sc2", "--scope", "sc2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--env SCOPE_DIR={self.squad}/scopes/sc2", r.stdout)
        self.assertIn(f"--env GOAL_DIR={self.squad}/goals/g1", r.stdout)

    def test_goal_manager_gets_goal_dir_and_no_scope_dir(self):
        r = self.run_spawn("manager", "t-mgr-g1", "--goal", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--env GOAL_DIR={self.squad}/goals/g1", r.stdout)
        self.assertNotIn("SCOPE_DIR", r.stdout)
        self.assertIn(f"--squad-dir {self.squad}/goals/g1 --set-session t-mgr-g1", r.stdout)

    def test_developer_worktree_and_branch_are_grouped_by_scope(self):
        repo = self.root / "code"
        repo.mkdir()
        r = self.run_spawn("dev", "t-dev-sc1-1", "--scope", "sc1", "--repo", str(repo))
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-1"
        self.assertIn(f"worktree add {wt} -b squad/t/sc1/t-dev-sc1-1", r.stdout)
        self.assertIn(f"--cwd {wt}", r.stdout)

    def test_base_makes_the_new_branch_start_from_a_passed_branch_or_commit(self):
        repo = self.root / "code"
        repo.mkdir()
        r = self.run_spawn("dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(repo), "--base", "squad/t/sc1/t-dev-sc1-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-2"
        self.assertIn(f"worktree add {wt} -b squad/t/sc1/t-dev-sc1-2 squad/t/sc1/t-dev-sc1-1", r.stdout)

    def test_real_spawn_with_base_branches_from_the_passed_commit_not_from_head(self):
        repo = self.root / "code"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True,
                                      env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}).stdout.strip()
        g("init", "-q", "-b", "main")
        g("commit", "-q", "--allow-empty", "-m", "init")
        g("branch", "passed")
        g("checkout", "-q", "passed")
        g("commit", "-q", "--allow-empty", "-m", "passed work")
        g("checkout", "-q", "main")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        r = subprocess.run([str(SCRIPT), "dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(repo), "--base", "passed"],
                           env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-2"
        self.assertEqual(g("-C", str(wt), "rev-parse", "HEAD"), g("rev-parse", "passed"))
        self.assertNotEqual(g("rev-parse", "main"), g("rev-parse", "passed"))

    def test_base_needs_repo(self):
        self.assertNotEqual(self.run_spawn("dev", "t-dev-sc1-2", "--scope", "sc1", "--base", "main").returncode, 0)

    def test_worktree_flag_reuses_an_existing_worktree_wherever_it_is(self):
        old = self.root / ".worktrees" / "dev-board-1"
        old.mkdir(parents=True)
        r = self.run_spawn("dev", "t-dev-sc1-1", "--scope", "sc1", "--worktree", str(old))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--cwd {old}", r.stdout)
        self.assertNotIn("worktree add", r.stdout)

    def test_worktree_flag_must_exist(self):
        r = self.run_spawn("dev", "t-dev-sc1-1", "--scope", "sc1", "--worktree", str(self.root / "nope"))
        self.assertNotEqual(r.returncode, 0)

    def test_scope_or_goal_is_required(self):
        r = self.run_spawn("dev", "t-dev-x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--scope or --goal", r.stderr)

    def test_unknown_scope_or_goal_is_refused(self):
        self.assertNotEqual(self.run_spawn("dev", "t-dev-x", "--scope", "nope").returncode, 0)
        self.assertNotEqual(self.run_spawn("manager", "t-mgr-x", "--goal", "nope").returncode, 0)

    def test_scope_and_goal_together_are_refused(self):
        self.assertNotEqual(self.run_spawn("manager", "t-mgr-x", "--scope", "sc1", "--goal", "g1").returncode, 0)

    def test_a_goal_manager_has_no_worktree(self):
        r = self.run_spawn("manager", "t-mgr-g1", "--goal", "g1", "--repo", str(self.root))
        self.assertNotEqual(r.returncode, 0)

    def test_real_spawn_writes_the_roster_row_in_the_scope_folder(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        r = subprocess.run([str(SCRIPT), "tech-lead", "t-tech-sc1", "--scope", "sc1"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| t-tech-sc1 | tech-lead | sc1 |", (self.squad / "scopes" / "sc1" / "roster.md").read_text())
        self.assertNotIn("t-tech-sc1", (self.squad / "scopes" / "sc2" / "roster.md").read_text())


if __name__ == "__main__":
    unittest.main()
