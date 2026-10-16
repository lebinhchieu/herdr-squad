"""squad-spawn --dry-run: role defaults and session id."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-spawn"
BIN_DIR = SCRIPT.parent
TABLE = {"manager": ("opus", "medium"), "tech-lead": ("sonnet", "high"), "ba": ("sonnet", "high"),
         "team-lead": ("sonnet", "medium"), "dev": ("sonnet", "medium"),
         "qa-whitebox": ("sonnet", "high"), "qa-blackbox": ("sonnet", "high"),
         "token-coach": ("sonnet", "medium"), "designer": ("sonnet", "high")}
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

    def test_new_tab_is_created_in_the_callers_workspace(self):
        self._fake_herdr(live="")
        self.env.update(HERDR_WORKSPACE_ID="wK")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        tab_create = next(l for l in self.log.read_text().splitlines() if l.startswith("tab create"))
        self.assertIn("--workspace wK", tab_create)

    def _real_spawn(self, *args, name="dev-1"):
        self._fake_herdr(live="")
        return subprocess.run([str(SCRIPT), "dev", name, "--scope", "s", *args], env=self.env,
                              text=True, capture_output=True, timeout=10)

    def _respawn_dry(self, name="dev-1"):
        r = subprocess.run([str(SCRIPT.parent / "squad-respawn"), name, "--dry-run"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        return r

    def test_an_effort_override_is_recorded_and_replayed_by_respawn(self):
        self.assertEqual(self._real_spawn("--effort", "low").returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(), "effort=low\n")
        r = self._respawn_dry()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"squad-spawn dev dev-1 .*--effort low ")
        self.assertNotIn("--model", r.stdout)  # the role's default model is left to squad-spawn

    def test_both_overrides_are_recorded(self):
        self.assertEqual(self._real_spawn("--model", "haiku", "--effort", "low").returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(), "model=haiku\neffort=low\n")
        self.assertRegex(self._respawn_dry().stdout, r"--model haiku --effort low ")

    def test_no_override_writes_no_file_and_respawn_passes_none(self):
        self.assertEqual(self._real_spawn().returncode, 0)
        self.assertFalse((self.squad / "roles" / "dev-1.overrides").exists())
        out = self._respawn_dry().stdout
        self.assertNotIn("--model", out)
        self.assertNotIn("--effort", out)

    def test_a_spawn_without_overrides_removes_a_stale_file(self):
        self.assertEqual(self._real_spawn("--effort", "low").returncode, 0)
        self.assertTrue((self.squad / "roles" / "dev-1.overrides").exists())
        Path(self.tmp.name, "herdr.log").unlink()
        self.assertEqual(self._real_spawn().returncode, 0)
        self.assertFalse((self.squad / "roles" / "dev-1.overrides").exists())

    def test_a_bad_override_value_is_refused_by_spawn_and_by_respawn(self):
        r = self._real_spawn("--model", "x; touch pwned")
        self.assertEqual(r.returncode, 2)
        self.assertIn("bad --model/--effort value", r.stderr)
        self.assertFalse((self.squad / "roles").exists())
        self.assertEqual(self._real_spawn().returncode, 0)
        (self.squad / "roles").mkdir(exist_ok=True)
        (self.squad / "roles" / "dev-1.overrides").write_text("effort=low\nfuture=ignored $(x)\nmodel=a b\n")
        r = self._respawn_dry()
        self.assertEqual(r.returncode, 1)
        self.assertIn("bad model value", r.stderr)
        (self.squad / "roles" / "dev-1.overrides").write_text("future=ignored $(x)\neffort=low\n")
        self.assertRegex(self._respawn_dry().stdout, r"--effort low ")

    def test_a_value_starting_with_a_dash_is_refused_everywhere(self):
        for bad in ("--dangerously-skip-permissions", "-x"):
            for flag in ("--model", "--effort"):
                with self.subTest(bad=bad, flag=flag):
                    r = self._real_spawn(flag, bad)
                    self.assertEqual(r.returncode, 2)
                    self.assertIn("bad --model/--effort value", r.stderr)
        self.assertEqual(self._real_spawn().returncode, 0)
        roles = self.squad / "roles"
        roles.mkdir(exist_ok=True)
        for line in ("model=--dangerously-skip-permissions", "effort=-x"):
            with self.subTest(line=line):
                (roles / "dev-1.overrides").write_text(line + "\n")
                self.env["LIVE"] = "dev-1"
                self.log.write_text("")
                r = self._respawn_dry()
                self.assertEqual(r.returncode, 1)
                self.assertIn("refusing", r.stderr)
                r = subprocess.run([str(SCRIPT.parent / "squad-respawn"), "dev-1"], env=self.env,
                                   text=True, capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 1)
                self.assertNotIn("agent rename", self.log.read_text())
                self.assertNotIn("pane close", self.log.read_text())

    def test_a_failed_agent_start_leaves_the_old_overrides_file(self):
        self.assertEqual(self._real_spawn("--effort", "low").returncode, 0)
        herdr = Path(self.tmp.name) / "bin" / "herdr"
        herdr.write_text(FAKE_HERDR.replace("exit 0\n", '[[ "$1 $2" == "agent start" ]] && exit 1\nexit 0\n'))
        r = subprocess.run([str(SCRIPT), "dev", "dev-1", "--scope", "s", "--effort", "high"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(), "effort=low\n")

    def test_a_flat_squad_manager_keeps_its_model_across_a_respawn(self):
        self._fake_herdr(live="")
        r = subprocess.run([str(SCRIPT), "manager", "m-1", "--model", "sonnet"], env=self.env,
                           text=True, capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.squad / "roles" / "m-1.overrides").read_text(), "model=sonnet\n")
        r = self._respawn_dry("m-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"squad-spawn manager m-1 .*--model sonnet ")

    def test_dry_run_records_nothing(self):
        self.spawn("dev", "--effort", "low")
        self.assertFalse((self.squad / "roles").exists())

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


LABEL_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get") [[ " ${LIVE:-} " == *" $3 "* ]] && { echo '{"result":{"agent":{"tab_id":"t-'$3'"}}}'; exit 0; }
               echo '{"error":{"code":"agent_not_found"}}'; exit 1 ;;
  "agent list") jq -nc --arg l "${LIVE:-}" '{result:{agents:($l|split(" ")|map(select(.!=""))|map({name:.}))}}' ;;
  "tab create") echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t-new"}}}' ;;
esac
exit 0
"""


class SpawnLabelTest(unittest.TestCase):
    """The tab label is "<emoji> <Role>[ n][ · title]"; the address name stays as it is."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(LABEL_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{bin_dir}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, name, *args, scope="sc1"):
        where = ("--goal", scope) if role == "manager" and scope.startswith("g") else ("--scope", scope)
        r = subprocess.run([str(SCRIPT), role, name, *where, *args], env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def calls(self, prefix):
        return [l for l in self.log.read_text().splitlines() if l.startswith(prefix)]

    def test_title_goes_after_the_role_and_the_env_keeps_the_address_name(self):
        self.spawn("tech-lead", "t-tech-sc1", "--title", "plan")
        (create,) = self.calls("tab create")
        self.assertIn("--label 🤖 Tech Lead · plan --no-focus", create)
        self.assertIn("--env SQUAD_NAME=t-tech-sc1", create)
        self.assertNotIn("t-tech-sc1 ·", create)

    def test_refused_spawn_of_a_live_name_keeps_its_stored_label(self):
        self.spawn("tech-lead", "t-tech-sc1", "--title", "plan")
        store = self.squad / "scopes" / "sc1" / "labels" / "t-tech-sc1.json"
        before = store.read_text()
        self.env["LIVE"] = "t-tech-sc1"
        calls = self.log.read_text()
        for extra in (["--title", "OTHER"], []):
            r = subprocess.run([str(SCRIPT), "tech-lead", "t-tech-sc1", "--scope", "sc1", *extra],
                               env=self.env, text=True, capture_output=True, timeout=20)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("already live", r.stderr)
            self.assertEqual(store.read_text(), before)
        self.assertEqual(self.calls("tab rename"), [])
        self.assertNotIn("tab create", self.log.read_text()[len(calls):])

    def test_no_title_means_no_separator_and_a_manager_has_the_crab(self):
        self.spawn("manager", "t-mgr-sc1")
        self.assertIn("--label 🦀 Manager --no-focus", self.calls("tab create")[0])
        self.assertNotIn(" · ", self.calls("tab create")[0])

    def test_a_goal_manager_stores_its_label_in_the_goal_folder(self):
        self.spawn("manager", "t-mgr-g1", scope="g1")
        self.assertTrue((self.squad / "goals" / "g1" / "labels" / "t-mgr-g1.json").is_file())

    def test_a_second_live_dev_renames_the_first_and_gets_number_two(self):
        self.spawn("dev", "t-dev-sc1-1")
        self.env["LIVE"] = "t-dev-sc1-1"
        self.spawn("dev", "t-dev-sc1-2")
        self.assertIn("tab rename t-t-dev-sc1-1 🤖 Dev 1", self.log.read_text())
        self.assertIn("--label 🤖 Dev 2 --no-focus", self.calls("tab create")[1])

    def test_the_label_never_holds_the_squad_or_scope_name(self):
        self.spawn("qa-whitebox", "t-qaw-sc1")
        self.assertNotIn("sc1", self.calls("tab create")[0].split("--env")[0])

    def test_a_title_with_spaces_quotes_or_a_substitution_is_data(self):
        self.spawn("ba", "t-ba-sc1", "--title", "it's $(touch pwned) `x`")
        self.assertIn("--label 🤖 BA · it's $(touch pwned) `x` --no-focus", self.calls("tab create")[0])
        self.assertFalse((self.root / "pwned").exists())

    def test_a_failing_squad_label_still_starts_the_agent_with_the_name_and_a_warning(self):
        stub = self.root / "plugin"
        (stub / "bin").mkdir(parents=True)
        for f in ("squad-spawn", "squad-usage", "squadlabel.py"):  # copies: squad-spawn finds its plugin via the real path
            shutil.copy(BIN_DIR / f, stub / "bin" / f)
        os.symlink(BIN_DIR.parent / "agents", stub / "agents")
        os.symlink(BIN_DIR.parent / "templates", stub / "templates")
        (stub / "bin" / "squad-label").write_text("#!/bin/sh\nexit 1\n")
        (stub / "bin" / "squad-label").chmod(0o755)
        r = subprocess.run([str(stub / "bin" / "squad-spawn"), "ba", "t-ba-sc1", "--scope", "sc1"], env=self.env,
                           text=True, capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning", r.stderr)
        self.assertIn("--label t-ba-sc1 --no-focus", self.calls("tab create")[0])

    def test_dry_run_prints_the_label_and_writes_no_store_file(self):
        r = subprocess.run([str(SCRIPT), "dev", "t-dev-sc1-1", "--scope", "sc1", "--title", "x", "--dry-run"],
                           env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--label 🤖 Dev · x --no-focus", r.stdout)
        self.assertFalse((self.squad / "scopes" / "sc1" / "labels").exists())


def toy_plugin(root, version):
    """A copy of the plugin whose template process.md is `version` (None: no version line)."""
    plugin = Path(root) / "plugin"
    shutil.rmtree(plugin, ignore_errors=True)
    shutil.copytree(BIN_DIR, plugin / "bin", ignore=shutil.ignore_patterns("__pycache__"))
    os.symlink(BIN_DIR.parent / "agents", plugin / "agents")
    shutil.copytree(BIN_DIR.parent / "templates", plugin / "templates")
    (plugin / "templates" / "squad" / "process.md").write_text(
        "# T\n" + (f"\nprocess-version: {version}\n" if version else ""))
    return plugin


class SpawnProcessUpdateTest(unittest.TestCase):
    """The Manager's first prompt carries the process-update sentence; nobody else's does; nothing blocks."""
    setUp, tearDown, calls = SpawnLabelTest.setUp, SpawnLabelTest.tearDown, SpawnLabelTest.calls

    def spawn_from(self, plugin_version, squad_text, role="manager", name="t-mgr-sc1", *args):
        plugin = toy_plugin(self.root, plugin_version)
        (self.squad / "process.md").write_text(squad_text)
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), role, name, "--scope", "sc1", *args], env=self.env,
                           text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return (self.calls("agent prompt") or [""])[0]

    def test_behind_manager_gets_the_sentence_after_its_own_prompt(self):
        p = self.spawn_from(2, "process-version: 1\n", "manager", "t-mgr-sc1", "--prompt", "Start of run.")
        self.assertTrue(p.startswith("agent prompt t-mgr-sc1 Start of run. Process update: "), p)
        for s in ("version 1", "is 2", "migrate the process", "Tell the PO in your first message", "Do not migrate unless the PO says so"):
            self.assertIn(s, p)

    def test_empty_prompt_becomes_the_sentence(self):
        p = self.spawn_from(2, "# T\n")
        self.assertTrue(p.startswith("agent prompt t-mgr-sc1 Process update: "), p)
        self.assertIn("treated as version 1", p)

    def test_other_roles_get_nothing(self):
        p = self.spawn_from(2, "process-version: 1\n", "dev", "t-dev-sc1-1", "--prompt", "Do RP-1.")
        self.assertEqual(p, "agent prompt t-dev-sc1-1 Do RP-1.")

    def test_current_manager_prompt_is_unchanged_and_without_prompt_none_is_sent(self):
        self.assertEqual(self.spawn_from(2, "process-version: 2\n", "manager", "t-mgr-sc1", "--prompt", "Go."),
                         "agent prompt t-mgr-sc1 Go.")
        self.log.unlink()
        self.assertEqual(self.spawn_from(2, "process-version: 2\n", "manager", "t-mgr-sc2"), "")

    def test_a_failing_check_or_a_template_without_the_line_never_stops_the_spawn(self):
        self.assertEqual(self.spawn_from(None, "process-version: 1\n", "manager", "t-mgr-sc1", "--prompt", "Go."),
                         "agent prompt t-mgr-sc1 Go.")
        self.log.unlink()
        plugin = self.root / "plugin"
        (plugin / "bin" / "squad-process").write_text("#!/bin/sh\nexit 1\n")
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), "manager", "t-mgr-sc1", "--scope", "sc1", "--prompt", "Go."],
                           env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls("agent prompt")[0], "agent prompt t-mgr-sc1 Go.")

    def test_dry_run_is_unchanged(self):
        plugin = toy_plugin(self.root, 2)
        (self.squad / "process.md").write_text("process-version: 1\n")
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), "manager", "t-mgr-sc1", "--scope", "sc1", "--dry-run"],
                           env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Process update", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()


class SpawnDesignerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = scoped_squad(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, *args):
        return subprocess.run([str(SCRIPT), "designer", "d-sc1", "--scope", "sc1", *args], env=self.env,
                              text=True, capture_output=True, timeout=10)

    def test_design_yes_spawns_a_sonnet_high_designer_with_its_own_settings(self):
        (self.squad / "scopes/sc1/scope.md").write_text("# Scope\n\ndesign: Yes\n")
        r = self.spawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--agent squad:designer", r.stdout)
        self.assertRegex(r.stdout, r"--model sonnet --effort high\b")
        self.assertRegex(r.stdout, r"--settings \S*settings/designer\.json")

    def test_without_design_yes_it_refuses_and_starts_nothing(self):
        scope_md = self.squad / "scopes/sc1/scope.md"
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(FAKE_HERDR)
        (bin_dir / "herdr").chmod(0o755)
        log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(log))
        for body in ("# Scope\n\ndesign: no\n", "# Scope\n\ntouches:\n", None):
            for extra in (("--dry-run",), ()):
                with self.subTest(body=body, extra=extra):
                    scope_md.unlink(missing_ok=True)
                    if body is not None:
                        scope_md.write_text(body)
                    r = self.spawn(*extra)
                    self.assertEqual(r.returncode, 1)
                    self.assertIn("scope sc1 has no 'design: yes' in scope.md; only the PO turns the designer on", r.stderr)
                    self.assertFalse(log.exists())
