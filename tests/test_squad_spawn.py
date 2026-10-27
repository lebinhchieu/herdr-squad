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
SETTINGS = SCRIPT.parent.parent / "templates" / "squad" / "settings"
TABLE = {p.stem: (json.loads(p.read_text(encoding="utf-8"))["model"], json.loads(p.read_text(encoding="utf-8"))["effortLevel"])
         for p in sorted(SETTINGS.glob("*.json"))}
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
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, *args):
        r = subprocess.run([str(SCRIPT), role, "x", "--dry-run", *args], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_role_defaults_match_the_table(self):
        for role, (model, effort) in TABLE.items():
            with self.subTest(role=role):
                self.assertRegex(self.spawn(role), rf"--model {model} --effort {effort}\b")

    def test_warns_once_on_stderr_when_a_non_manager_role_has_no_prompt(self):
        for role in ("dev", "token-coach", "qa-whitebox"):
            with self.subTest(role=role):
                r = subprocess.run([str(SCRIPT), role, "x", "--dry-run"], env=self.env, text=True, capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stderr.count("without --prompt"), 1, r.stderr)
                self.assertNotIn("without --prompt", r.stdout)

    def test_no_warning_for_a_manager_or_when_prompt_is_given(self):
        for role, args in (("manager", []), ("dev", ["--prompt", "go"]), ("token-coach", ["--prompt", "go"])):
            with self.subTest(role=role, args=args):
                r = subprocess.run([str(SCRIPT), role, "x", "--dry-run", *args], env=self.env, text=True, capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("without --prompt", r.stderr)

    def test_flags_override_role_defaults(self):
        self.assertRegex(self.spawn("dev", "--model", "opus", "--effort", "high"), r"--model opus --effort high\b")

    def _squad_settings(self, role, data):
        (self.squad / "settings").mkdir(exist_ok=True)
        (self.squad / "settings" / f"{role}.json").write_text(json.dumps(data), encoding="utf-8")

    def _spawn_any(self, *args):
        return subprocess.run([str(SCRIPT), "dev", "x", "--dry-run", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=10)

    def test_the_table_covers_every_role(self):
        self.assertEqual(len(TABLE), 10)
        self.assertEqual(TABLE["architect"], ("sonnet", "high"))

    def test_squad_settings_override_the_template(self):
        self._squad_settings("dev", {"model": "haiku", "effortLevel": "low"})
        self.assertRegex(self.spawn("dev"), r"--model haiku --effort low\b")

    def test_flag_beats_squad_and_template(self):
        self._squad_settings("dev", {"model": "haiku", "effortLevel": "low"})
        self.assertRegex(self.spawn("dev", "--model", "opus", "--effort", "max"), r"--model opus --effort max\b")

    def test_squad_file_lacking_a_key_falls_back_to_the_template_silently(self):
        self._squad_settings("dev", {"permissions": {}, "model": "haiku"})
        r = self._spawn_any("--prompt", "go")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, rf"--model haiku --effort {TABLE['dev'][1]}\b")
        # only the old-layout warning (ticket 08), no missing-key warning
        self.assertEqual(r.stderr.count("warning:"), 1)
        self.assertIn("full settings file", r.stderr)

    def test_a_key_in_neither_file_warns_and_passes_no_flag(self):
        tpl = Path(self.tmp.name) / "plugin"
        shutil.copytree(SCRIPT.parent.parent, tpl, ignore=shutil.ignore_patterns(".git", ".worktrees", ".scratch", "tests"))
        (tpl / "templates/squad/settings/dev.json").write_text('{"model": "sonnet"}', encoding="utf-8")
        r = subprocess.run([str(tpl / "bin/squad-spawn"), "dev", "x", "--dry-run"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning: no effortLevel for dev in", r.stderr)
        self.assertIn("runs on Claude Code's default", r.stderr)
        self.assertIn("--model sonnet", r.stdout)
        self.assertNotIn("--effort", r.stdout)

    def test_a_bad_settings_value_is_refused(self):
        for bad in ({"model": ["x"]}, {"model": "--x"}, {"effortLevel": "a; touch pwned"}, {"effortLevel": 3}):
            with self.subTest(bad=bad):
                self._squad_settings("dev", bad)
                r = self._spawn_any()
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertNotIn("would run: herdr agent start", r.stdout)

    def test_an_unparsable_settings_file_is_refused(self):
        (self.squad / "settings").mkdir()
        (self.squad / "settings" / "dev.json").write_text("{not json", encoding="utf-8")
        r = self._spawn_any()
        self.assertEqual(r.returncode, 2)
        self.assertIn("cannot read", r.stderr)

    def test_dry_run_passes_a_session_id_and_plans_the_roster_write(self):
        out = self.spawn("dev")
        self.assertRegex(out, rf"--session-id {UUID}\b")
        self.assertRegex(out, rf"--set-session x {UUID}")

    def test_spawn_records_the_same_session_id_in_roster(self):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (bin_dir / "herdr").chmod(0o755)
        log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(log))
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n| manager | Manager | all | x | live |\n", encoding="utf-8")
        r = subprocess.run([str(SCRIPT), "dev", "dev-1", "--scope", "s"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        passed = re.search(rf"--session-id ({UUID})", log.read_text(encoding="utf-8")).group(1)
        self.assertIn(f"| dev-1 | dev | s |  | live | {passed} |", (self.squad / "roster.md").read_text(encoding="utf-8"))
        self.assertIn(passed, r.stdout)


    def _fake_herdr(self, live):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (bin_dir / "herdr").chmod(0o755)
        self.log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.log), LIVE=live)
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n", encoding="utf-8")

    def test_refuses_a_name_that_is_already_live_in_another_squad(self):
        self._fake_herdr(live="bill-ba-invoices")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already live", r.stderr)
        self.assertNotIn("tab create", self.log.read_text(encoding="utf-8"))

    def test_spawns_when_the_name_is_free(self):
        self._fake_herdr(live="other-name")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_new_tab_is_created_in_the_callers_workspace(self):
        self._fake_herdr(live="")
        self.env.update(HERDR_WORKSPACE_ID="wK")
        r = subprocess.run([str(SCRIPT), "ba", "bill-ba-invoices"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        tab_create = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create"))
        self.assertIn("--workspace wK", tab_create)

    def _real_spawn(self, *args, name="dev-1"):
        self._fake_herdr(live="")
        return subprocess.run([str(SCRIPT), "dev", name, "--scope", "s", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=10)

    def _respawn_dry(self, name="dev-1"):
        r = subprocess.run([str(SCRIPT.parent / "squad-respawn"), name, "--dry-run"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        return r

    # --- ticket 24: a legacy squad (process.md, no process.local.md) gets the running plugin's rules attached
    def test_legacy_dry_run_has_the_rules_flag_and_no_plugin_dir_and_one_warning(self):
        r = self.spawn("dev", "--scope", "s", "--prompt", "Task 1.")
        rules = self.squad / "roles" / "x.rules.md"
        self.assertIn(f"--append-system-prompt-file {rules}", r)
        self.assertNotIn("--plugin-dir", r)
        self.assertFalse(rules.exists())  # dry run writes nothing

    def test_legacy_dry_run_prints_the_warning_once(self):
        r = self._spawn_any("--scope", "s")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr.count("legacy squad: plugin rules attached, local process.md edits not applied; "
                                        "run squad-process adopt --dry-run"), 1)

    def test_legacy_real_spawn_writes_the_composed_rules_and_attaches_them(self):
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        rules = self.squad / "roles" / "dev-1.rules.md"
        self.assertTrue(rules.read_text(encoding="utf-8").startswith("# Your process rules"))
        start = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent start"))
        self.assertIn(f"--append-system-prompt-file {rules}", start)
        self.assertNotIn("--plugin-dir", start)
        self.assertEqual(r.stderr.count("legacy squad: plugin rules attached"), 1)
        tab = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create"))
        self.assertNotIn("SQUAD_PLUGIN_DIR", tab)

    def test_legacy_first_prompt_says_the_rules_are_attached(self):
        self.assertEqual(self._real_spawn().returncode, 0)
        # Without --prompt nothing is sent in legacy mode; with one, the sentence follows it.
        self.log.write_text("", encoding="utf-8")
        (self.squad / "roster.md").write_text("| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n", encoding="utf-8")
        r = subprocess.run([str(SCRIPT), "dev", "dev-2", "--scope", "s", "--prompt", "Task 1."], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        prompt = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent prompt"))
        self.assertIn("Task 1. Your process rules are attached to this session", prompt)

    def test_a_squad_folder_with_neither_file_still_exits_1(self):
        (self.squad / "process.md").unlink()
        r = self._spawn_any("--scope", "s")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no squad folder", r.stderr)

    def test_legacy_compose_failure_exits_2_and_leaves_nothing_behind(self):
        plugin = Path(self.tmp.name) / "plugin"
        root = SCRIPT.parent.parent
        for d in ("bin", "templates", ".claude-plugin"):
            shutil.copytree(root / d, plugin / d, ignore=shutil.ignore_patterns("__pycache__"))
        broken = sorted((plugin / "templates" / "squad" / "process").glob("[a-z]*.md"))[0]
        broken.write_text("not a rule file\n\n## no id\n", encoding="utf-8")
        self._fake_herdr(live="")
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), "dev", "dev-1", "--scope", "s"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse((self.squad / "roles" / "dev-1.rules.md").exists())
        self.assertFalse(self.log.exists() and "agent start" in self.log.read_text(encoding="utf-8"))
        self.assertNotIn("tab create", self.log.read_text(encoding="utf-8") if self.log.exists() else "")

    def test_an_effort_override_is_recorded_and_replayed_by_respawn(self):
        self.assertEqual(self._real_spawn("--effort", "low").returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(encoding="utf-8"), "effort=low\n")
        r = self._respawn_dry()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"squad-spawn dev dev-1 .*--effort low ")
        self.assertNotIn("--model", r.stdout)  # the role's default model is left to squad-spawn

    def test_both_overrides_are_recorded(self):
        self.assertEqual(self._real_spawn("--model", "haiku", "--effort", "low").returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(encoding="utf-8"), "model=haiku\neffort=low\n")
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
        (self.squad / "roles" / "dev-1.overrides").write_text("effort=low\nfuture=ignored $(x)\nmodel=a b\n", encoding="utf-8")
        r = self._respawn_dry()
        self.assertEqual(r.returncode, 1)
        self.assertIn("bad model value", r.stderr)
        (self.squad / "roles" / "dev-1.overrides").write_text("future=ignored $(x)\neffort=low\n", encoding="utf-8")
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
                (roles / "dev-1.overrides").write_text(line + "\n", encoding="utf-8")
                self.env["LIVE"] = "dev-1"
                self.log.write_text("", encoding="utf-8")
                r = self._respawn_dry()
                self.assertEqual(r.returncode, 1)
                self.assertIn("refusing", r.stderr)
                r = subprocess.run([str(SCRIPT.parent / "squad-respawn"), "dev-1"], env=self.env,
                                   text=True, encoding="utf-8", capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 1)
                self.assertNotIn("agent rename", self.log.read_text(encoding="utf-8"))
                self.assertNotIn("pane close", self.log.read_text(encoding="utf-8"))

    def test_a_failed_agent_start_leaves_the_old_overrides_file(self):
        self.assertEqual(self._real_spawn("--effort", "low").returncode, 0)
        herdr = Path(self.tmp.name) / "bin" / "herdr"
        herdr.write_text(FAKE_HERDR.replace("exit 0\n", '[[ "$1 $2" == "agent start" ]] && exit 1\nexit 0\n'), encoding="utf-8")
        r = subprocess.run([str(SCRIPT), "dev", "dev-1", "--scope", "s", "--effort", "high"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(encoding="utf-8"), "effort=low\n")

    def test_a_flat_squad_manager_keeps_its_model_across_a_respawn(self):
        self._fake_herdr(live="")
        r = subprocess.run([str(SCRIPT), "manager", "m-1", "--model", "sonnet"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.squad / "roles" / "m-1.overrides").read_text(encoding="utf-8"), "model=sonnet\n")
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
                self.assertIn("permissions", json.loads((settings / f"{role}.json").read_text(encoding="utf-8")))


ALL_ROLES_TEAM = "ba, team-lead, tech-lead, qa-white, qa-black, designer, architect"


def scoped_squad(root, goal_of_sc2="g1", team=ALL_ROLES_TEAM):
    """A squad in the per-scope layout: scopes/sc1 (lone), scopes/sc2 (in goal g1), goals/g1. Both scopes have
    `team:` (every role on it unless `team` says otherwise)."""
    squad = Path(root) / ".claude" / "squads" / "t"
    header = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
    for d, goal in (("scopes/sc1", ""), ("scopes/sc2", goal_of_sc2), ("goals/g1", None)):
        (squad / d).mkdir(parents=True)
        (squad / d / "roster.md").write_text(header, encoding="utf-8")
        if goal is not None:
            (squad / d / "scope.md").write_text(f"# Scope\n\ngoal: {goal}\ntouches:\nteam: {team}\n", encoding="utf-8")
    (squad / "process.md").write_text("x", encoding="utf-8")
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
                              text=True, encoding="utf-8", capture_output=True, timeout=10)

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
        g = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8",
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
        (bin_dir / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (bin_dir / "herdr").chmod(0o755)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        r = subprocess.run([str(SCRIPT), "dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(repo), "--base", "passed"],
                           env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-2"
        self.assertEqual(g("-C", str(wt), "rev-parse", "HEAD"), g("rev-parse", "passed"))
        self.assertNotEqual(g("rev-parse", "main"), g("rev-parse", "passed"))

    def test_base_with_an_existing_worktree_folder_is_refused(self):
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-2"
        wt.mkdir(parents=True)
        r = self.run_spawn("dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(self.root / "not-a-git-repo"), "--base", "main")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn(str(wt), r.stderr)
        self.assertIn("--base", r.stderr)
        self.assertNotIn("worktree add", r.stdout)
        self.assertNotIn("herdr", r.stdout)

    def test_base_with_worktree_flag_is_refused(self):
        old = self.root / ".worktrees" / "dev-board-1"
        old.mkdir(parents=True)
        r = self.run_spawn("dev", "t-dev-sc1-1", "--scope", "sc1", "--worktree", str(old), "--base", "main", "--repo", str(self.root))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn(str(old), r.stderr)
        self.assertIn("--base", r.stderr)
        self.assertNotIn("herdr", r.stdout)

    def test_existing_worktree_folder_without_base_is_reused(self):
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-2"
        wt.mkdir(parents=True)
        r = self.run_spawn("dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--cwd {wt}", r.stdout)

    def test_real_second_spawn_with_another_base_is_refused_and_keeps_the_commit(self):
        repo = self.root / "code"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8",
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
        (bin_dir / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (bin_dir / "herdr").chmod(0o755)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        run = lambda base: subprocess.run([str(SCRIPT), "dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(repo), "--base", base],
                                          env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(run("passed").returncode, 0)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-2"
        r = run("main")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(g("-C", str(wt), "rev-parse", "HEAD"), g("rev-parse", "passed"))

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
        (bin_dir / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (bin_dir / "herdr").chmod(0o755)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        r = subprocess.run([str(SCRIPT), "tech-lead", "t-tech-sc1", "--scope", "sc1"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| t-tech-sc1 | tech-lead | sc1 |", (self.squad / "scopes" / "sc1" / "roster.md").read_text(encoding="utf-8"))
        self.assertNotIn("t-tech-sc1", (self.squad / "scopes" / "sc2" / "roster.md").read_text(encoding="utf-8"))


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
        (bin_dir / "herdr").write_text(LABEL_HERDR, encoding="utf-8")
        (bin_dir / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{bin_dir}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, name, *args, scope="sc1"):
        where = ("--goal", scope) if role == "manager" and scope.startswith("g") else ("--scope", scope)
        r = subprocess.run([str(SCRIPT), role, name, *where, *args], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def calls(self, prefix):
        return [l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith(prefix)]

    def test_title_goes_after_the_role_and_the_env_keeps_the_address_name(self):
        self.spawn("tech-lead", "t-tech-sc1", "--title", "plan")
        (create,) = self.calls("tab create")
        self.assertIn("--label 🤖 Tech Lead · plan --no-focus", create)
        self.assertIn("--env SQUAD_NAME=t-tech-sc1", create)
        self.assertNotIn("t-tech-sc1 ·", create)

    def test_refused_spawn_of_a_live_name_keeps_its_stored_label(self):
        self.spawn("tech-lead", "t-tech-sc1", "--title", "plan")
        store = self.squad / "scopes" / "sc1" / "labels" / "t-tech-sc1.json"
        before = store.read_text(encoding="utf-8")
        self.env["LIVE"] = "t-tech-sc1"
        calls = self.log.read_text(encoding="utf-8")
        for extra in (["--title", "OTHER"], []):
            r = subprocess.run([str(SCRIPT), "tech-lead", "t-tech-sc1", "--scope", "sc1", *extra],
                               env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("already live", r.stderr)
            self.assertEqual(store.read_text(encoding="utf-8"), before)
        self.assertEqual(self.calls("tab rename"), [])
        self.assertNotIn("tab create", self.log.read_text(encoding="utf-8")[len(calls):])

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
        self.env["LC_ALL"] = "C.UTF-8"  # emoji argv to `herdr tab rename` needs a UTF-8 fs encoding (always so on Windows)
        self.spawn("dev", "t-dev-sc1-2")
        self.assertIn("tab rename t-t-dev-sc1-1 🤖 Dev 1", self.log.read_text(encoding="utf-8"))
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
        shutil.copytree(BIN_DIR, stub / "bin", ignore=shutil.ignore_patterns("__pycache__"))  # copies: squad-spawn finds its plugin via the real path
        os.symlink(BIN_DIR.parent / "agents", stub / "agents")
        os.symlink(BIN_DIR.parent / "templates", stub / "templates")
        (stub / "bin" / "squad-label").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stub / "bin" / "squad-label").chmod(0o755)
        r = subprocess.run([str(stub / "bin" / "squad-spawn"), "ba", "t-ba-sc1", "--scope", "sc1"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning", r.stderr)
        self.assertIn("--label t-ba-sc1 --no-focus", self.calls("tab create")[0])

    def test_dry_run_prints_the_label_and_writes_no_store_file(self):
        r = subprocess.run([str(SCRIPT), "dev", "t-dev-sc1-1", "--scope", "sc1", "--title", "x", "--dry-run"],
                           env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
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
        "# T\n" + (f"\nprocess-version: {version}\n" if version else ""), encoding="utf-8")
    return plugin


class SpawnProcessUpdateTest(unittest.TestCase):
    """The Manager's first prompt carries the process-update sentence; nobody else's does; nothing blocks."""
    setUp, tearDown, calls = SpawnLabelTest.setUp, SpawnLabelTest.tearDown, SpawnLabelTest.calls

    def spawn_from(self, plugin_version, squad_text, role="manager", name="t-mgr-sc1", *args):
        plugin = toy_plugin(self.root, plugin_version)
        (self.squad / "process.md").write_text(squad_text, encoding="utf-8")
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), role, name, "--scope", "sc1", *args], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return (self.calls("agent prompt") or [""])[0]

    def attached(self, name):  # the legacy "rules are attached" sentence (ticket 24)
        return f"Your process rules are attached to this session ({self.squad}/scopes/sc1/roles/{name}.rules.md); read no other process file."

    def test_behind_manager_gets_the_sentence_after_its_own_prompt(self):
        p = self.spawn_from(2, "process-version: 1\n", "manager", "t-mgr-sc1", "--prompt", "Start of run.")
        self.assertTrue(p.startswith(f"agent prompt t-mgr-sc1 Start of run. {self.attached('t-mgr-sc1')} Process update: "), p)
        for s in ("version 1", "is 2", "migrate the process", "Tell the PO in your first message", "Do not migrate unless the PO says so"):
            self.assertIn(s, p)

    def test_empty_prompt_becomes_the_sentence(self):
        p = self.spawn_from(2, "# T\n")
        self.assertTrue(p.startswith("agent prompt t-mgr-sc1 Process update: "), p)
        self.assertIn("treated as version 1", p)

    def test_other_roles_get_nothing(self):
        p = self.spawn_from(2, "process-version: 1\n", "dev", "t-dev-sc1-1", "--prompt", "Do RP-1.")
        self.assertEqual(p, f"agent prompt t-dev-sc1-1 Do RP-1. {self.attached('t-dev-sc1-1')}")

    def test_current_manager_prompt_is_unchanged_and_without_prompt_none_is_sent(self):
        self.assertEqual(self.spawn_from(2, "process-version: 2\n", "manager", "t-mgr-sc1", "--prompt", "Go."),
                         f"agent prompt t-mgr-sc1 Go. {self.attached('t-mgr-sc1')}")
        self.log.unlink()
        self.assertEqual(self.spawn_from(2, "process-version: 2\n", "manager", "t-mgr-sc2"), "")

    def test_a_failing_check_or_a_template_without_the_line_never_stops_the_spawn(self):
        self.assertEqual(self.spawn_from(None, "process-version: 1\n", "manager", "t-mgr-sc1", "--prompt", "Go."),
                         f"agent prompt t-mgr-sc1 Go. {self.attached('t-mgr-sc1')}")
        self.log.unlink()
        plugin = self.root / "plugin"
        (plugin / "bin" / "squad-process").write_text(
            f'#!/bin/sh\n[ "$1" = check ] && exit 1\nexec {BIN_DIR}/squad-process "$@"\n', encoding="utf-8")
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), "manager", "t-mgr-sc1", "--scope", "sc1", "--prompt", "Go."],
                           env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls("agent prompt")[0], f"agent prompt t-mgr-sc1 Go. {self.attached('t-mgr-sc1')}")

    def test_dry_run_is_unchanged(self):
        plugin = toy_plugin(self.root, 2)
        (self.squad / "process.md").write_text("process-version: 1\n", encoding="utf-8")
        r = subprocess.run([str(plugin / "bin" / "squad-spawn"), "manager", "t-mgr-sc1", "--scope", "sc1", "--dry-run"],
                           env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Process update", r.stdout + r.stderr)



class _GateBase(unittest.TestCase):
    """Per-scope squad `t`, scope sc1, a fake herdr that logs every call; `self.created()` lists what a spawn made."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        self.scope = self.squad / "scopes/sc1"
        self.scope_md = self.scope / "scope.md"
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{fake}:{os.environ['PATH']}")

    def set_scope(self, text):
        self.scope_md.write_text(text, encoding="utf-8", newline="")

    def spawn(self, role="dev", name="gate-1", *args, script=SCRIPT, env=None):
        return subprocess.run([str(script), role, name, "--scope", "sc1", "--prompt", "go", *args], env=env or self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=30)

    def created(self):
        """Everything a refused spawn must not leave: a herdr call, a roster row, a label, a rules file."""
        out = []
        if self.log.exists():
            out.append("herdr")
        if "gate-" in (self.scope / "roster.md").read_text(encoding="utf-8"):
            out.append("roster")
        out += [f.name for f in (self.scope / "roles").glob("*")] if (self.scope / "roles").exists() else []
        return out


class SpawnTeamGateTest(_GateBase):
    def test_a_role_not_on_the_team_exits_1_naming_the_role_and_scope_md_and_creates_nothing(self):
        self.set_scope("# Scope\n\nteam: ba, qa-white\n")
        for role in ("team-lead", "tech-lead", "qa-blackbox", "designer", "architect"):
            for extra in (("--dry-run",), ()):
                with self.subTest(role=role, extra=extra):
                    r = self.spawn(role, "gate-1", *extra)
                    self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                    self.assertIn(f"role {role} is not on the team in {self.scope_md}", r.stderr)
                    self.assertEqual(self.created(), [])

    def test_qa_whitebox_is_gated_on_qa_white_and_qa_blackbox_on_qa_black(self):
        for team, role, ok in (("qa-white", "qa-whitebox", True), ("qa-black", "qa-whitebox", False),
                               ("qa-black", "qa-blackbox", True), ("qa-white", "qa-blackbox", False),
                               ("ba, tech-lead", "qa-whitebox", False)):
            with self.subTest(team=team, role=role):
                self.set_scope(f"# Scope\n\nteam: {team}\n")
                r = self.spawn(role, "gate-1", "--dry-run")
                self.assertEqual(r.returncode, 0 if ok else 1, r.stderr)

    def test_dev_token_coach_and_manager_need_no_team_entry_when_the_team_is_none(self):
        self.set_scope("# Scope\n\nteam: none\n")
        for role in ("dev", "token-coach", "manager"):
            with self.subTest(role=role):
                self.assertEqual(self.spawn(role, "gate-1", "--dry-run").returncode, 0)
        self.assertEqual(self.spawn("ba", "gate-1", "--dry-run").returncode, 1)

    def test_an_undecided_team_refuses_every_role_but_the_manager(self):
        for text in ("# Scope\n\nteam:\n", "# Scope\n\ntouches:\n"):
            for role in ("ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "dev", "token-coach", "designer", "architect"):
                with self.subTest(text=text, role=role):
                    self.set_scope(text)
                    r = self.spawn(role, "gate-1")
                    self.assertEqual(r.returncode, 1, r.stderr)
                    self.assertIn("team is undecided", r.stderr)
                    self.assertIn(str(self.scope_md), r.stderr)
                    self.assertEqual(self.created(), [])
            self.set_scope(text)
            self.assertEqual(self.spawn("manager", "gate-1", "--dry-run").returncode, 0)
            self.log.unlink(missing_ok=True)

    def test_an_unpinned_scope_on_size_is_refused_with_the_converter_pointer_for_every_role(self):
        self.set_scope("# Scope\n\nsize: M\nqa-b: yes\n")
        for role in ("manager", "dev", "ba", "qa-whitebox"):
            with self.subTest(role=role):
                r = self.spawn(role, "gate-1")
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("squad-process adopt", r.stderr)
                self.assertIn("size", r.stderr)
                self.assertEqual(self.created(), [])

    def test_the_size_only_home_is_refused_by_the_team_cli_and_by_the_spawn(self):
        """C2: the D1 scaffold is not reachable through `squad-process team` nor `squad-spawn`."""
        self.set_scope("# Scope\n\nsize: L\n")
        t = subprocess.run([str(BIN_DIR / "squad-process"), "team", "--home", str(self.scope)], text=True,
                           encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(t.returncode, 2)
        self.assertIn("squad-process adopt", t.stderr)
        r = self.spawn("dev", "gate-1", "--dry-run")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr.strip().splitlines()[-1], t.stderr.strip().splitlines()[-1])

    def test_a_bad_or_old_key_team_line_fails_naming_the_line_and_the_token(self):
        for line, token in (("team: ba, nobody", "nobody"), ("team: ba, ba", "ba"), ("team: qa-whitebox", "qa-whitebox"),
                            ("team: qa-b", "qa-b")):
            with self.subTest(line=line):
                self.set_scope(f"# Scope\n\n{line}\n")
                for extra in (("--dry-run",), ()):
                    r = self.spawn("dev", "gate-1", *extra)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn(token, r.stderr)
                    self.assertRegex(r.stderr, r"scope\.md:3")
                    self.assertEqual(self.created(), [])

    def test_a_hostile_team_value_runs_nothing(self):
        marker = self.root / "X"
        for value in (f"qa-white; touch {marker}", f"$(touch {marker})", f"`touch {marker}`",
                      f"qa-white && touch {marker}"):
            with self.subTest(value=value):
                self.set_scope(f"# Scope\n\nteam: {value}\n")
                for role in ("qa-whitebox", "dev"):
                    r = self.spawn(role, "gate-1", "--dry-run")
                    self.assertNotEqual(r.returncode, 0, r.stdout)
                    self.assertFalse(marker.exists())

    def test_the_designer_and_architect_follow_the_team(self):
        self.set_scope("# Scope\n\nteam: designer, architect\n")
        for role, agent in (("designer", "squad:designer"), ("architect", "squad:architect")):
            r = self.spawn(role, "gate-1", "--dry-run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"--agent {agent}", r.stdout)

    def test_a_goal_manager_has_no_team_gate(self):
        r = subprocess.run([str(SCRIPT), "manager", "gate-m", "--goal", "g1", "--dry-run"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_the_gate_runs_before_the_scope_model_lines(self):
        self.set_scope("# Scope\n\nteam: ba\nmodel dev: bad line\n")
        r = self.spawn("tech-lead", "gate-1", "--dry-run")
        self.assertEqual(r.returncode, 1)  # not on the team: refused before the malformed model line


def toy_runtime_spawn(path, record, name="squad-spawn"):
    """A stub engine: records its arguments and the env that matters, makes nothing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/usr/bin/env bash\necho "{name} $*" >> "{record}"\nexit 0\n', encoding="utf-8")
    path.chmod(0o755)


BASE_SHA = "294957333ee4b2953e1db26e96e297637ed2343c"  # main at 0.5.2, the pinned fixture's engine (AC 20)


class SpawnPinnedTest(_GateBase):
    def pin(self, version, sha="a" * 40, stub=True, line=None):
        """Composed squad pinned to `version`; its runtime folder holds a stub squad-spawn (when `stub`)."""
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        rt = self.squad / "_runtime" / f"{version}-{sha[:12]}"
        (rt / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (rt / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "squad", "version": version}), encoding="utf-8")
        self.record = self.root / "stub.log"
        if stub:
            toy_runtime_spawn(rt / "bin" / "squad-spawn", self.record)
        self.set_scope(f"# Scope\n\ngoal:\ntouches:\nsize: L\nqa-b: yes\n{line or f'plugin: {version} {sha}'}\n")
        return rt

    def calls(self):
        return self.record.read_text(encoding="utf-8").splitlines() if self.record.exists() else []

    def test_pin_0_5_2_hands_off_to_the_pins_own_squad_spawn_with_the_same_arguments(self):
        self.pin("0.5.2")
        r = self.spawn("qa-whitebox", "gate-1", "--title", "t one")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls(), ["squad-spawn qa-whitebox gate-1 --scope sc1 --prompt go --title t one"])
        self.assertEqual(self.created(), [])  # nothing of the new engine's own

    def test_the_hand_off_also_happens_from_an_agent_session_and_for_a_dry_run(self):
        self.pin("0.5.2")
        env = dict(self.env, SQUAD_NAME="t-mgr-sc1", SQUAD_ROLE="manager")
        self.assertEqual(self.spawn("dev", "gate-1", env=env).returncode, 0)
        self.assertEqual(len(self.calls()), 1)
        r = self.spawn("dev", "gate-2", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would hand off to the pinned runtime", r.stdout)
        self.assertEqual(len(self.calls()), 1)

    def test_pin_0_6_0_uses_the_new_gate_and_does_not_hand_off(self):
        self.pin("0.6.0")
        self.set_scope(self.scope_md.read_text(encoding="utf-8").replace("size: L\nqa-b: yes\n", "team: ba\n"))
        r = self.spawn("tech-lead", "gate-1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("is not on the team", r.stderr)
        self.assertEqual(self.calls(), [])
        r = self.spawn("ba", "gate-1", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("hand off", r.stdout)
        self.assertEqual(self.calls(), [])

    def test_no_pin_line_takes_the_unpinned_path(self):
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        self.set_scope("# Scope\n\nteam: ba\n")
        r = self.spawn("ba", "gate-1")
        self.assertEqual(r.returncode, 2)  # a composed squad needs a pin; the hand-off is not tried
        self.assertIn("pin", r.stderr)
        self.assertEqual(self.created(), [])
        (self.squad / "process.local.md").unlink()
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        self.assertEqual(self.spawn("ba", "gate-1", "--dry-run").returncode, 0)  # legacy squad: the gate, no pin

    def test_a_malformed_plugin_line_is_refused_naming_the_line(self):
        for bad in ("plugin: 0.5.2", "plugin: 0.5.2 zz", "plugin: 0.5.2 abc def"):
            with self.subTest(bad=bad):
                self.pin("0.5.2", line=bad)
                r = self.spawn("dev", "gate-1")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(bad.split(": ")[1].split()[-1], r.stderr)  # the offending value is named
                self.assertEqual(self.calls(), [])
                self.assertEqual(self.created(), [])

    def test_a_runtime_without_squad_spawn_refuses_with_a_warning_and_creates_nothing(self):
        self.pin("0.5.2", stub=False)
        r = self.spawn("dev", "gate-1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("warning:", r.stderr)
        self.assertIn("no bin/squad-spawn", r.stderr)
        self.assertEqual(self.created(), [])  # no worktree, label or herdr call
        self.assertFalse((self.root / ".worktrees").exists())

    def test_the_hand_off_happens_once(self):
        """A runtime whose squad-spawn is this very script is not handed to again (no exec loop)."""
        rt = self.pin("0.5.2", stub=False)
        (rt / "bin").mkdir(parents=True)
        (rt / "bin" / "squad-spawn").symlink_to(SCRIPT)
        r = self.spawn("dev", "gate-1")
        self.assertEqual((r.returncode, "squad-process adopt" in r.stderr), (2, True))  # the new gate, once
        self.assertEqual(self.created(), [])

    def test_the_pinned_scope_md_is_byte_identical_after_spawn_and_the_converter(self):
        self.pin("0.5.2")
        before = self.scope_md.read_bytes()
        self.spawn("dev", "gate-1")
        self.spawn("dev", "gate-2", "--dry-run")
        for args in ((), ("--yes",)):
            c = subprocess.run([str(BIN_DIR / "squad-process"), "adopt", "--squad-dir", str(self.squad), *args], env=self.env,
                               text=True, encoding="utf-8", capture_output=True, timeout=30)
            self.assertIn("pinned", c.stdout + c.stderr, c.stdout + c.stderr)
            self.assertEqual(self.scope_md.read_bytes(), before)
        self.assertEqual(self.scope_md.read_bytes(), before)


@unittest.skipUnless(subprocess.run(["git", "cat-file", "-e", BASE_SHA], capture_output=True).returncode == 0,
                     "base sha 2949573 not in this repository")
class PinnedBaseEngineTest(_GateBase):
    """AC 20 end to end: the pin is the real 0.5.2 engine (git archive of the base sha); the spawn runs it, and
    the composed rules equal what that engine composes on its own (a golden made from the base sha, not by hand)."""

    def test_the_pins_engine_composes_the_scope_and_scope_md_is_unchanged(self):
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        rt = self.squad / "_runtime" / f"0.5.2-{BASE_SHA[:12]}"
        rt.mkdir(parents=True)
        tar = subprocess.run(["git", "archive", "--format=tar", BASE_SHA], cwd=SCRIPT.parent.parent, capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(rt)], input=tar.stdout, check=True)
        self.set_scope(f"# Scope\n\ngoal:\ntouches:\nsize: L\nqa-b: yes\nplugin: 0.5.2 {BASE_SHA}\n")
        before = self.scope_md.read_bytes()
        now = "2026-10-27T00:00:00Z"
        golden = subprocess.run([str(rt / "bin" / "squad-process"), "compose", "dev", "--home", str(self.scope), "--agent", "gate-1",
                                 "--squad-dir", str(self.squad), "--plugin-root", str(rt), "--now", now],
                                text=True, encoding="utf-8", capture_output=True, timeout=60)
        self.assertEqual(golden.returncode, 0, golden.stderr)
        r = self.spawn("dev", "gate-1", env=dict(self.env, SQUAD_COMPOSE_NOW=now))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.scope / "roles" / "gate-1.rules.md").read_text(encoding="utf-8"), golden.stdout)
        self.assertEqual(self.scope_md.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
