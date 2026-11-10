"""squad-spawn --dry-run: role defaults and session id."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import winlaunch
from squadtest import BIN, ROOT, clean_env, fake_herdr

SCRIPT = BIN / "squad-spawn"
SETTINGS = ROOT / "templates" / "squad" / "settings"
TABLE = {p.stem: (json.loads(p.read_text(encoding="utf-8"))["model"], json.loads(p.read_text(encoding="utf-8"))["effortLevel"])
         for p in sorted(SETTINGS.glob("*.json"))}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


class SpawnDryRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = Path(self.tmp.name) / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.squad / "scope.md").write_text("team: none\n", encoding="utf-8")  # a decided team: a non-Manager compose of an undecided home exits 2
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, *args):
        r = winlaunch.run_script(SCRIPT, [role, "x", "--dry-run", *args], env=self.env,
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
                r = winlaunch.run_script(SCRIPT, [role, "x", "--dry-run"], env=self.env, text=True, capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stderr.count("without --prompt"), 1, r.stderr)
                self.assertNotIn("without --prompt", r.stdout)

    def test_no_warning_for_a_manager_or_when_prompt_is_given(self):
        for role, args in (("manager", []), ("dev", ["--prompt", "go"]), ("token-coach", ["--prompt", "go"])):
            with self.subTest(role=role, args=args):
                r = winlaunch.run_script(SCRIPT, [role, "x", "--dry-run", *args], env=self.env, text=True, capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("without --prompt", r.stderr)

    def test_flags_override_role_defaults(self):
        self.assertRegex(self.spawn("dev", "--model", "opus", "--effort", "high"), r"--model opus --effort high\b")

    def _squad_settings(self, role, data):
        (self.squad / "settings").mkdir(exist_ok=True)
        (self.squad / "settings" / f"{role}.json").write_text(json.dumps(data), encoding="utf-8")

    def _spawn_any(self, *args):
        return winlaunch.run_script(SCRIPT, ["dev", "x", "--dry-run", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=10)

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
        r = winlaunch.run_script(tpl / "bin/squad-spawn", ["dev", "x", "--dry-run"], env=self.env,
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
        fake_herdr(bin_dir)
        log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(log))
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n| manager | Manager | all | x | live |\n", encoding="utf-8")
        r = winlaunch.run_script(SCRIPT, ["dev", "dev-1", "--scope", "s"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        passed = re.search(rf"--session-id ({UUID})", log.read_text(encoding="utf-8")).group(1)
        self.assertIn(f"| dev-1 | dev | s |  | live | {passed} |", (self.squad / "roster.md").read_text(encoding="utf-8"))
        self.assertIn(passed, r.stdout)

    def _fake_herdr(self, live):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir(exist_ok=True)
        fake_herdr(bin_dir)
        self.log = Path(self.tmp.name) / "herdr.log"
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.log), LIVE=live)
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n", encoding="utf-8")

    def test_refuses_a_name_that_is_already_live_in_another_squad(self):
        self._fake_herdr(live="bill-ba-invoices")
        r = winlaunch.run_script(SCRIPT, ["ba", "bill-ba-invoices"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already live", r.stderr)
        self.assertNotIn("tab create", self.log.read_text(encoding="utf-8"))

    def test_spawns_when_the_name_is_free(self):
        self._fake_herdr(live="other-name")
        r = winlaunch.run_script(SCRIPT, ["ba", "bill-ba-invoices"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_new_tab_is_created_in_the_callers_workspace(self):
        self._fake_herdr(live="")
        self.env.update(HERDR_WORKSPACE_ID="wK")
        r = winlaunch.run_script(SCRIPT, ["ba", "bill-ba-invoices"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        tab_create = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create"))
        self.assertIn("--workspace wK", tab_create)

    def _real_spawn(self, *args, name="dev-1"):
        self._fake_herdr(live="")
        return winlaunch.run_script(SCRIPT, ["dev", name, "--scope", "s", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=10)

    def _respawn_dry(self, name="dev-1"):
        r = winlaunch.run_script(SCRIPT.parent / "squad-respawn", [name, "--dry-run"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        return r

    # --- ticket 24: a legacy squad (process.md, no process.local.md) gets the running plugin's rules attached
    def test_legacy_dry_run_has_the_rules_flag_and_the_running_plugin(self):
        r = self.spawn("dev", "--scope", "s", "--prompt", "Task 1.")
        rules = self.squad / "roles" / "x.rules.md"
        self.assertIn(f"--append-system-prompt-file {rules}", r)
        self.assertIn(f"--plugin-dir {SCRIPT.parent.parent}", r)  # lean start: the user-level install is not read
        self.assertFalse(rules.exists())  # dry run writes nothing

    def test_legacy_dry_run_prints_the_warning_once(self):
        r = self._spawn_any("--scope", "s")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr.count("legacy squad: plugin rules attached, local process.md edits not applied; "
                                        "new squads: squad-process scaffold (or /squad:squad-init)"), 1)

    def test_legacy_real_spawn_writes_the_composed_rules_and_attaches_them(self):
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        rules = self.squad / "roles" / "dev-1.rules.md"
        self.assertTrue(rules.read_text(encoding="utf-8").startswith("# Your process rules"))
        start = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent start"))
        self.assertIn(f"--append-system-prompt-file {rules}", start)
        self.assertEqual(r.stderr.count("legacy squad: plugin rules attached"), 1)
        tab = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create"))
        self.assertNotIn("SQUAD_PLUGIN_DIR", tab)

    def test_legacy_first_prompt_says_the_rules_are_attached(self):
        self.assertEqual(self._real_spawn().returncode, 0)
        # Without --prompt nothing is sent in legacy mode; with one, the sentence follows it.
        self.log.write_text("", encoding="utf-8")
        (self.squad / "roster.md").write_text("| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n", encoding="utf-8")
        r = winlaunch.run_script(SCRIPT, ["dev", "dev-2", "--scope", "s", "--prompt", "Task 1."], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        prompt = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent prompt"))
        self.assertIn("Task 1. Your process rules are attached to this session", prompt)

    # --- lean start: no user-level plugins, skills or agent types; playwright-cli and claude-accounts kept
    def _user_skills(self, *names):
        cfg = Path(self.tmp.name) / "cfg"
        for n in names:
            (cfg / "skills" / n).mkdir(parents=True)
            (cfg / "skills" / n / "SKILL.md").write_text(f"---\nname: {n}\n---\n", encoding="utf-8")
        self.env["CLAUDE_CONFIG_DIR"] = str(cfg)

    def _start_line(self):
        return next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent start"))

    def test_lean_dry_run_drops_the_user_source_and_adds_the_kept_skills_dir(self):
        out = self.spawn("dev", "--scope", "s")
        lean = self.squad / "roles" / "x.skills"
        self.assertIn("--setting-sources project,local", out)
        self.assertIn(f"--add-dir {lean}", out)
        self.assertFalse(lean.exists())  # dry run writes nothing

    def test_lean_real_spawn_copies_only_the_two_kept_skills(self):
        self._user_skills("playwright-cli", "claude-accounts", "frontend-design")
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        skills = self.squad / "roles" / "dev-1.skills" / ".claude" / "skills"
        self.assertEqual(sorted(p.name for p in skills.iterdir()), ["claude-accounts", "playwright-cli"])
        self.assertTrue((skills / "playwright-cli" / "SKILL.md").is_file())
        start = self._start_line()
        self.assertIn("--setting-sources project,local", start)
        self.assertIn(f"--add-dir {skills.parent.parent}", start)
        self.assertIn("--settings", start)  # the role's own settings file still goes with it

    def test_lean_real_spawn_skips_a_kept_skill_the_user_lacks_without_noise(self):
        self._user_skills("playwright-cli")
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([p.name for p in (self.squad / "roles" / "dev-1.skills" / ".claude" / "skills").iterdir()], ["playwright-cli"])
        self.assertNotIn("kept skill", r.stderr)

    def test_lean_legacy_spawn_gets_the_running_plugin_by_flag_but_no_env(self):
        # the user-level source is gone, so an installed squad plugin would vanish: --plugin-dir carries it
        self.assertEqual(self._real_spawn().returncode, 0)
        self.assertIn(f"--plugin-dir {SCRIPT.parent.parent}", self._start_line())
        tab = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create"))
        self.assertNotIn("SQUAD_PLUGIN_DIR", tab)

    def test_lean_settings_file_merges_the_users_hooks_permissions_env_but_not_plugins(self):
        self._user_skills("playwright-cli")
        user = {"enabledPlugins": {"x@y": True}, "extraKnownMarketplaces": {"m": {}}, "env": {"PROBE": "1"}, "model": "opus",
                "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "rtk hook claude"}]}]},
                "permissions": {"allow": ["Bash(rtk:*)", "Bash(git status:*)"]}}
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "settings.json").write_text(json.dumps(user), encoding="utf-8")
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        merged = self.squad / "roles" / "dev-1.lean-settings.json"
        self.assertIn(f"--settings {merged}", self._start_line())
        m = json.loads(merged.read_text(encoding="utf-8"))
        self.assertNotIn("enabledPlugins", m)
        self.assertNotIn("extraKnownMarketplaces", m)
        self.assertEqual(m["env"], {"PROBE": "1"})
        self.assertEqual(m["hooks"], user["hooks"])
        self.assertEqual(m["model"], TABLE["dev"][0])  # the role's own scalar wins over the user's
        allow = m["permissions"]["allow"]
        self.assertEqual(allow.count("Bash(git status:*)"), 1)  # joined without a duplicate
        self.assertIn("Bash(rtk:*)", allow)
        self.assertIn("Bash(git diff:*)", allow)  # from the role's template
        self.assertIn("Bash(git push:*)", m["permissions"]["deny"])

    def test_lean_settings_skips_an_unparsable_user_file_with_one_warning(self):
        self._user_skills("playwright-cli")
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "settings.json").write_text("{nope", encoding="utf-8")
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr.count("is not usable JSON"), 1)
        self.assertIn("templates/squad/settings/dev.json", self._start_line().replace("\\", "/"))

    def test_user_config_env_restores_the_old_start(self):
        self.env["SQUAD_SPAWN_USER_CONFIG"] = "1"
        self.assertEqual(self._real_spawn().returncode, 0)
        start = self._start_line()
        for flag in ("--setting-sources", "--add-dir", "--plugin-dir"):
            self.assertNotIn(flag, start)
        self.assertNotIn("lean-settings", start)
        self.assertFalse((self.squad / "roles" / "dev-1.skills").exists())
        self.assertNotIn("--strict-mcp-config", start)
        self.assertFalse((self.squad / "roles" / "dev-1.mcp.json").exists())

    # --- settings/lean.json: what the lean start keeps (skills, plugins, mcp)
    def _lean_json(self, data):
        (self.squad / "settings").mkdir(exist_ok=True)
        (self.squad / "settings" / "lean.json").write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")

    def _cfg(self, **files):
        cfg = Path(self.tmp.name) / "cfg"
        (cfg / "skills").mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (cfg / name).write_text(json.dumps(data), encoding="utf-8")
        self.env["CLAUDE_CONFIG_DIR"] = str(cfg)
        return cfg

    def test_lean_without_a_lean_json_defaults_to_no_mcp_servers(self):
        self._cfg()  # no user settings.json: --settings stays the template file
        out = self.spawn("dev", "--model", "m", "--effort", "low").replace("\\", "/")
        flags = out.split(" -- ", 1)[1].strip()
        sq, root = str(self.squad).replace("\\", "/"), str(ROOT).replace("\\", "/")
        want = (f"--agent squad:dev --name x --session-id <S> --permission-mode auto --settings {root}/templates/squad/settings/dev.json "
                f"--model m --effort low --setting-sources project,local --add-dir {sq}/roles/x.skills "
                f"--strict-mcp-config --mcp-config {sq}/roles/x.mcp.json --plugin-dir {root} --append-system-prompt-file {sq}/roles/x.rules.md")
        self.assertEqual(re.sub(UUID, "<S>", flags), want)
        r = self._real_spawn()  # a real start writes the empty server list
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads((self.squad / "roles" / "dev-1.mcp.json").read_text(encoding="utf-8")), {"mcpServers": {}})

    def test_lean_json_keeps_exactly_the_listed_skills_and_warns_once_for_an_unknown_one(self):
        self._user_skills("playwright-cli", "claude-accounts", "frontend-design")
        self._lean_json({"skills": ["frontend-design", "nope", "claude-accounts", "nope"]})
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        skills = self.squad / "roles" / "dev-1.skills" / ".claude" / "skills"
        self.assertEqual(sorted(p.name for p in skills.iterdir()), ["claude-accounts", "frontend-design"])
        self.assertEqual(r.stderr.count("skill 'nope' not found"), 1, r.stderr)
        self.assertIn("--strict-mcp-config", self._start_line())  # no mcp key: strict with no servers

    def test_a_bad_lean_json_refuses_before_any_file_or_herdr_call(self):
        for bad in ("{nope", "[]", '{"skills": "playwright-cli"}', '{"mcp": [1]}', '{"plugins": ["../x"]}'):
            with self.subTest(bad=bad):
                self._lean_json(bad)
                r = self._real_spawn()
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("lean.json", r.stderr)
                self.assertFalse((self.squad / "roles").exists())
                self.assertNotIn("tab create", self.log.read_text(encoding="utf-8") if self.log.exists() else "")
                dry = self._spawn_any()
                self.assertEqual(dry.returncode, 2)  # a dry run refuses too

    def test_user_config_env_does_not_read_lean_json(self):
        self._lean_json("{nope")
        self.env["SQUAD_SPAWN_USER_CONFIG"] = "1"
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("--setting-sources", self._start_line())

    def test_lean_json_plugins_come_back_only_when_the_user_enabled_them(self):
        self._cfg(**{"settings.json": {"enabledPlugins": {"reply-style@m": True, "off@m": False, "other@m": True}}})
        self._lean_json({"plugins": ["reply-style", "off", "nope", "squad@x", "nope"]})
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        merged = json.loads((self.squad / "roles" / "dev-1.lean-settings.json").read_text(encoding="utf-8"))
        self.assertEqual(merged["enabledPlugins"], {"reply-style@m": True})
        self.assertEqual(r.stderr.count("plugin 'nope'"), 1, r.stderr)
        self.assertEqual(r.stderr.count("plugin 'off'"), 1, r.stderr)
        self.assertEqual(r.stderr.count("plugin 'squad@x' skipped"), 1, r.stderr)

    def test_lean_json_mcp_restricts_the_role_to_the_listed_servers(self):
        cfg = self._cfg(**{".claude.json": {"mcpServers": {"a": {"type": "http", "url": "https://a"}, "b": {"command": "b"}}}})
        self._lean_json({"mcp": ["a", "zzz"]})
        dry = self.spawn("dev", "--scope", "s")  # a dry run prints the flags and writes nothing
        mcp = self.squad / "roles" / "x.mcp.json"
        self.assertIn(f"--strict-mcp-config --mcp-config {mcp}", dry)
        self.assertFalse(mcp.exists())
        r = self._real_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        file = self.squad / "roles" / "dev-1.mcp.json"
        self.assertEqual(json.loads(file.read_text(encoding="utf-8")), {"mcpServers": {"a": {"type": "http", "url": "https://a"}}})
        self.assertEqual(r.stderr.count("MCP server 'zzz' not found"), 1, r.stderr)
        self.assertIn(f"--strict-mcp-config --mcp-config {file}", self._start_line())
        if os.name != "nt":
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
        self._lean_json({"mcp": []})  # a present, empty key still restricts: nothing loads
        self.assertEqual(self._real_spawn(name="dev-2").returncode, 0)
        self.assertEqual(json.loads((self.squad / "roles" / "dev-2.mcp.json").read_text(encoding="utf-8")), {"mcpServers": {}})
        self._lean_json({"skills": []})  # key dropped on a respawn: the stale server list goes, the file holds none
        self.assertEqual(self._real_spawn(name="dev-1").returncode, 0)
        self.assertEqual(json.loads(file.read_text(encoding="utf-8")), {"mcpServers": {}})

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
        r = winlaunch.run_script(plugin / "bin" / "squad-spawn", ["dev", "dev-1", "--scope", "s"], env=self.env,
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
                r = winlaunch.run_script(SCRIPT.parent / "squad-respawn", ["dev-1"], env=self.env,
                                   text=True, encoding="utf-8", capture_output=True, timeout=10)
                self.assertEqual(r.returncode, 1)
                self.assertNotIn("agent rename", self.log.read_text(encoding="utf-8"))
                self.assertNotIn("pane close", self.log.read_text(encoding="utf-8"))

    def test_a_failed_agent_start_leaves_the_old_overrides_file(self):
        self.assertEqual(self._real_spawn("--effort", "low").returncode, 0)
        herdr = Path(self.tmp.name) / "bin" / "herdr"
        head, tail = herdr.read_text(encoding="utf-8").rsplit("exit 0\n", 1)  # the script's final line
        herdr.write_text(head + '[[ "$1 $2" == "agent start" ]] && exit 1\nexit 0\n' + tail, encoding="utf-8", newline="\n")
        r = winlaunch.run_script(SCRIPT, ["dev", "dev-1", "--scope", "s", "--effort", "high"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.squad / "roles" / "dev-1.overrides").read_text(encoding="utf-8"), "effort=low\n")

    def test_a_flat_squad_manager_keeps_its_model_across_a_respawn(self):
        self._fake_herdr(live="")
        r = winlaunch.run_script(SCRIPT, ["manager", "m-1", "--model", "sonnet"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.squad / "roles" / "m-1.overrides").read_text(encoding="utf-8"), "model=sonnet\n")
        r = self._respawn_dry("m-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"squad-spawn manager m-1 .*--model sonnet ")

    def test_dry_run_records_nothing(self):
        self.spawn("dev", "--effort", "low")
        self.assertFalse((self.squad / "roles").exists())


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


def add_task_fixtures(scope, nns, duties="design-notes=dev, tech-ac=qa-white", files="`bin/squad-spawn`"):
    """Tickets `tasks/NN-t.md` with the Duties:/Files: lines, and the manager and both QA rows `--task` needs."""
    (scope / "tasks").mkdir(exist_ok=True)
    for nn in nns:
        (scope / "tasks" / f"{nn}-t.md").write_text(f"# {nn}: t\nStatus: ready-for-agent\nDuties: {duties}\nFiles: {files}\n", encoding="utf-8")
    with (scope / "roster.md").open("a", encoding="utf-8") as fh:
        fh.write("| t-mgr | manager | sc1 |  | live | s1 |\n| t-qaw | qa-whitebox | sc1 |  | live | s2 |\n"
                 "| t-qab | qa-blackbox | sc1 |  | live | s3 |\n")


class SpawnScopedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))

    def tearDown(self):
        self.tmp.cleanup()

    def run_spawn(self, role, name, *args):
        return winlaunch.run_script(SCRIPT, [role, name, "--dry-run", *args], env=self.env,
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
        fake_herdr(bin_dir)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        r = winlaunch.run_script(SCRIPT, ["dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(repo), "--base", "passed"],
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
        fake_herdr(bin_dir)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        run = lambda base: winlaunch.run_script(SCRIPT, ["dev", "t-dev-sc1-2", "--scope", "sc1", "--repo", str(repo), "--base", base],
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
        fake_herdr(bin_dir)
        self.env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", HERDR_LOG=str(self.root / "h.log"))
        r = winlaunch.run_script(SCRIPT, ["tech-lead", "t-tech-sc1", "--scope", "sc1"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| t-tech-sc1 | tech-lead | sc1 |", (self.squad / "scopes" / "sc1" / "roster.md").read_text(encoding="utf-8"))
        self.assertNotIn("t-tech-sc1", (self.squad / "scopes" / "sc2" / "roster.md").read_text(encoding="utf-8"))


class SpawnTaskPromptTest(unittest.TestCase):
    """`--task NN` builds the first prompt (ticket 06): HANDIN target by team, refusals before any side effect."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake_herdr(self.bin)
        self.log = self.root / "h.log"

    def scope(self, team, ticket_lines="Duties: tech-ac=qa-white\nFiles: `bin/x`\n", rows=""):
        shutil.rmtree(self.root / ".claude", ignore_errors=True)
        squad = scoped_squad(self.root, team=team)
        self.squad = squad
        sc = squad / "scopes" / "sc1"
        add_task_fixtures(sc, ())
        (sc / "tasks").mkdir(exist_ok=True)
        (sc / "tasks" / "07-t.md").write_text(f"# 07: t\nStatus: ready-for-agent\n{ticket_lines}", encoding="utf-8")
        with (sc / "roster.md").open("a", encoding="utf-8") as fh:
            fh.write(rows)
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(squad), HERDR_LOG=str(self.log), PATH=f"{self.bin}:{os.environ['PATH']}")
        return sc

    def spawn(self, *args, role="dev", dry=True):
        return winlaunch.run_script(SCRIPT, [role, "t-dev-sc1-1", "--scope", "sc1", *args, *(["--dry-run"] if dry else [])],
                                    env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=30)

    def prompt_of(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        (line,) = [l for l in r.stdout.splitlines() if l.startswith("would run: herdr agent prompt")]
        return line

    def test_a_qa_team_hands_in_to_both_qas(self):  # AC1, AC2
        self.scope("qa-white, qa-black")
        p = self.prompt_of(self.spawn("--task", "07", "--prompt", "EXTRA"))
        self.assertIn("HANDIN to t-qaw and t-qab", p)
        self.assertIn("Ticket 07 of scope sc1", p)
        self.assertTrue(p.endswith(" EXTRA"), p)  # --prompt text comes after the built part

    def test_a_no_qa_team_hands_in_to_the_team_lead_else_the_manager(self):  # AC2
        self.scope("team-lead", rows="| t-tl | team-lead | sc1 |  | live | s4 |\n")
        self.assertIn("HANDIN to t-tl.", self.prompt_of(self.spawn("--task", "07", "--prompt", "x")))
        self.scope("none")
        self.assertIn("HANDIN to t-mgr.", self.prompt_of(self.spawn("--task", "07", "--prompt", "x")))

    def refused(self, *args, msg):
        r = self.spawn(*args, dry=False)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn(msg, r.stderr)
        self.assertFalse(self.log.exists() and self.log.read_text(encoding="utf-8").strip(), "herdr was called")
        self.assertFalse((self.root / ".worktrees").exists())

    def test_a_ticket_with_a_missing_field_or_roster_row_stops_the_spawn(self):  # AC3, T1
        self.scope("qa-white, qa-black", ticket_lines="Files: x\n")
        self.refused("--task", "07", msg="no Duties: line")
        self.scope("qa-white, qa-black", ticket_lines="Duties: a=b\n")
        self.refused("--task", "07", msg="no Files: line")
        self.refused("--task", "99", msg="no ticket file for task 99")
        self.refused("--task", "../x", msg="bad --task value")
        self.scope("team-lead")  # a Team Lead on the team but no roster row
        self.refused("--task", "07", msg="no team-lead row")
        self.assertEqual(self.spawn("--task", "07", "--dry-run", dry=False).returncode, 2)

    def test_ticket_lines_are_quoted_data_and_nothing_runs(self):  # T4
        evil = "`a` \"q\" $(touch pwned) ; touch pwned2 \\n"
        self.scope("qa-white, qa-black", ticket_lines=f"Duties: x\nFiles: {evil}\n")
        p = self.prompt_of(self.spawn("--task", "07"))
        self.assertIn(json.dumps(evil.strip()), p)
        self.assertFalse(list(self.root.rglob("pwned*")))

    def test_a_checker_gets_a_prompt_and_claims_nothing(self):  # T6
        self.scope("qa-white, qa-black")
        r = self.spawn("--task", "07", role="qa-whitebox")
        p = self.prompt_of(r)
        self.assertIn("the Developer who owns the ticket", p)
        self.assertNotIn("warning", r.stderr.replace("legacy squad", ""))
        self.assertNotIn("squad-task claim", r.stdout)
        self.scope("qa-white, qa-black", rows="| t-dev-z | dev | sc1 | ticket 07 | live | s9 |\n")
        self.assertIn("when t-dev-z sends HANDIN", self.prompt_of(self.spawn("--task", "07", role="qa-blackbox")))


class SpawnTaskClaimTest(unittest.TestCase):
    """`--task NN` (dev only): a claim event once the pane is up (design 5.2). Warns, never fails the spawn."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        self.repo = self.root / "code"
        self.repo.mkdir()
        self.git = lambda *a: subprocess.run(
            ["git", *a], cwd=self.repo, check=True, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}).stdout.strip()
        self.git("init", "-q", "-b", "main")
        self.git("commit", "-q", "--allow-empty", "-m", "init")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake_herdr(bin_dir)
        add_task_fixtures(self.squad / "scopes" / "sc1", ("03", "04"))  # --task now builds a prompt: it needs a ticket and roster
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.root / "h.log"),
                        PATH=f"{bin_dir}:{os.environ['PATH']}")

    def spawn(self, *args, role="dev", name="t-dev-sc1-1", env=None):
        return winlaunch.run_script(SCRIPT, [role, name, "--scope", "sc1", *args], env=env or self.env, text=True,
                                    encoding="utf-8", capture_output=True, timeout=30)

    def events(self):
        return [json.loads(l) for f in (self.squad / "task-events").glob("*.jsonl")
                for l in f.read_text(encoding="utf-8").splitlines()]

    def test_task_claims_the_ticket_for_the_agent_and_its_branch(self):  # AC2, T7
        r = self.spawn("--repo", str(self.repo), "--task", "03")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "ready")  # stdout stays the one JSON line
        (ev,) = self.events()
        self.assertEqual((ev["ev"], ev["task"], ev["by"], ev["branch"]), ("claim", "03", "t-dev-sc1-1", "squad/t/sc1/t-dev-sc1-1"))

    def test_claim_with_an_open_blocker_is_recorded_with_w1_and_never_refused(self):  # AC8
        drafts = self.squad / "scopes" / "sc1" / "tasks"
        drafts.mkdir(exist_ok=True)
        (drafts / "03-t.md").write_text("# 03\n\nStatus: ready-for-agent\nBlocked by: 02\nDuties: tech-ac=qa-white\nFiles: x\n", encoding="utf-8")
        r = self.spawn("--repo", str(self.repo), "--task", "03")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "ready")
        self.assertIn("W1", r.stderr)
        (ev,) = self.events()
        self.assertEqual(ev["ev"], "claim")
        self.assertTrue(ev["warn"][0].startswith("W1"), ev["warn"])

    def test_env_task_claims_too_and_a_worktree_respawn_does_not_reclaim(self):  # T7
        r = self.spawn("--repo", str(self.repo), env={**self.env, "SQUAD_SPAWN_TASK": "04"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([e["task"] for e in self.events()], ["04"])
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-1"
        r = self.spawn("--worktree", str(wt), "--task", "04", name="t-dev-sc1-2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.events()), 1)

    def test_dry_run_plans_the_claim_and_writes_nothing_and_a_non_dev_ignores_task(self):  # T7
        r = self.spawn("--repo", str(self.repo), "--task", "03", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"would run: squad-task claim 03 --scope-home \S+/scopes/sc1 --owner t-dev-sc1-1 --branch squad/t/sc1/t-dev-sc1-1")
        self.assertFalse((self.squad / "task-events").exists())
        r = self.spawn("--task", "03", "--dry-run", role="tech-lead", name="t-tech-sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--task ignored", r.stderr)
        self.assertNotIn("squad-task claim", r.stdout)

    def test_a_token_coach_spawn_prints_the_coach_rules_and_other_roles_do_not(self):  # 10 T5
        r = self.spawn("--prompt", "go", role="token-coach", name="t-coach-sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "ready")  # stdout stays the one JSON line
        self.assertIn("## ITER-6c", r.stderr)
        r = self.spawn("--prompt", "go", role="tech-lead", name="t-tech-sc1")
        self.assertNotIn("ITER-6c", r.stderr + r.stdout)

    def test_a_bad_task_value_is_refused_and_a_claim_failure_never_fails_the_spawn(self):  # T1
        self.assertEqual(self.spawn("--task", "x3", "--dry-run").returncode, 2)
        shutil.copytree(BIN, self.root / "p" / "bin", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "templates", self.root / "p" / "templates")
        broken = self.root / "p" / "bin" / "squad-task"
        broken.write_text("#!/usr/bin/env bash\nexit 9\n", encoding="utf-8")
        script = self.root / "p" / "bin" / "squad-spawn"
        r = winlaunch.run_script(script, ["dev", "t-dev-sc1-1", "--scope", "sc1", "--repo", str(self.repo), "--task", "03", "--prompt", "go"],
                                 env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)


class SpawnLabelTest(unittest.TestCase):
    """The tab label is "<emoji> <Role>[ n][ · title]"; the address name stays as it is."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake_herdr(bin_dir)
        self.log = self.root / "herdr.log"
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{bin_dir}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def spawn(self, role, name, *args, scope="sc1"):
        where = ("--goal", scope) if role == "manager" and scope.startswith("g") else ("--scope", scope)
        r = winlaunch.run_script(SCRIPT, [role, name, *where, *args], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
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
            r = winlaunch.run_script(SCRIPT, ["tech-lead", "t-tech-sc1", "--scope", "sc1", *extra],
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
        self.assertIn("tab rename tab-t-dev-sc1-1 🤖 Dev 1", self.log.read_text(encoding="utf-8"))
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
        shutil.copytree(BIN, stub / "bin", ignore=shutil.ignore_patterns("__pycache__"))  # copies: squad-spawn finds its plugin via the real path
        os.symlink(ROOT / "agents", stub / "agents")
        os.symlink(ROOT / "templates", stub / "templates")
        (stub / "bin" / "squad-label").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stub / "bin" / "squad-label").chmod(0o755)
        r = winlaunch.run_script(stub / "bin" / "squad-spawn", ["ba", "t-ba-sc1", "--scope", "sc1"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning", r.stderr)
        self.assertIn("--label t-ba-sc1 --no-focus", self.calls("tab create")[0])

    def test_dry_run_prints_the_label_and_writes_no_store_file(self):
        r = winlaunch.run_script(SCRIPT, ["dev", "t-dev-sc1-1", "--scope", "sc1", "--title", "x", "--dry-run"],
                           env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--label 🤖 Dev · x --no-focus", r.stdout)
        self.assertFalse((self.squad / "scopes" / "sc1" / "labels").exists())


class SpawnLegacyPromptTest(unittest.TestCase):
    """No role's first prompt carries a process-update sentence, whatever the squad's process.md says."""
    setUp, tearDown, calls = SpawnLabelTest.setUp, SpawnLabelTest.tearDown, SpawnLabelTest.calls

    def spawn(self, squad_text, role="manager", name="t-mgr-sc1", *args):
        (self.squad / "process.md").write_text(squad_text, encoding="utf-8")
        r = winlaunch.run_script(BIN / "squad-spawn", [role, name, "--scope", "sc1", *args], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r, (self.calls("agent prompt") or [""])[0]

    def attached(self, name):  # the legacy "rules are attached" sentence (ticket 24)
        return f"Your process rules are attached to this session ({self.squad}/scopes/sc1/roles/{name}.rules.md); read no other process file."


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
        fake_herdr(fake)
        self.log = self.root / "herdr.log"
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{fake}:{os.environ['PATH']}")

    def set_scope(self, text):
        self.scope_md.write_text(text, encoding="utf-8", newline="")

    def spawn(self, role="dev", name="gate-1", *args, script=SCRIPT, env=None):
        return winlaunch.run_script(script, [role, name, "--scope", "sc1", "--prompt", "go", *args], env=env or self.env,
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

    def test_an_unpinned_scope_on_size_is_refused_with_the_team_line_pointer_for_every_role(self):
        self.set_scope("# Scope\n\nsize: M\nqa-b: yes\n")
        for role in ("manager", "dev", "ba", "qa-whitebox"):
            with self.subTest(role=role):
                r = self.spawn(role, "gate-1")
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("one `team:` line", r.stderr)
                self.assertIn("size", r.stderr)
                self.assertEqual(self.created(), [])

    def test_the_size_only_home_is_refused_by_the_team_cli_and_by_the_spawn(self):
        """C2: the D1 scaffold is not reachable through `squad-process team` nor `squad-spawn`."""
        self.set_scope("# Scope\n\nsize: L\n")
        t = winlaunch.run_script(BIN / "squad-process", ["team", "--home", str(self.scope)], text=True,
                           encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(t.returncode, 2)
        self.assertIn("one `team:` line", t.stderr)
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
        r = winlaunch.run_script(SCRIPT, ["manager", "gate-m", "--goal", "g1", "--dry-run"], env=self.env,
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

    def test_the_hand_off_drops_task_from_the_args_and_passes_it_as_env(self):  # T7: an old runtime rejects --task
        rt = self.pin("0.5.2")
        (rt / "bin" / "squad-spawn").write_text(
            f'#!/usr/bin/env bash\necho "squad-spawn $* task=${{SQUAD_SPAWN_TASK:-}}" >> "{self.record}"\nexit 0\n', encoding="utf-8")
        r = self.spawn("dev", "gate-1", "--task", "03", "--title", "t")
        self.assertEqual(r.returncode, 0, r.stderr)
        (call,) = self.calls()
        self.assertNotIn("--task", call)
        self.assertTrue(call.endswith("--title t task=03"), call)

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

    def test_a_dry_run_without_the_pins_squad_spawn_also_warns_and_exits_1(self):
        self.pin("0.5.2", stub=False)
        r = self.spawn("dev", "gate-1", "--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no bin/squad-spawn", r.stderr)
        self.assertNotIn("would hand off", r.stdout)

    def test_a_composed_scope_with_size_and_no_pin_gets_the_converter_pointer_not_the_pin_text(self):
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        self.set_scope("# Scope\n\nname: s\nsize: M\n")
        for extra in ((), ("--dry-run",)):
            r = self.spawn("manager", "gate-1", *extra)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertRegex(r.stderr, r"scope\.md:\d+: old format `size:`")
            self.assertIn("one `team:` line", r.stderr)
            self.assertNotIn("needs a pin", r.stderr)
            self.assertEqual(self.created(), [])

    def test_the_hand_off_happens_once(self):
        """A runtime whose squad-spawn is this very script is not handed to again (no exec loop)."""
        rt = self.pin("0.5.2", stub=False)
        (rt / "bin").mkdir(parents=True)
        (rt / "bin" / "squad-spawn").symlink_to(SCRIPT)
        r = self.spawn("dev", "gate-1")
        self.assertEqual((r.returncode, "one `team:` line" in r.stderr), (2, True))  # the new gate, once
        self.assertEqual(self.created(), [])

    def test_the_pinned_scope_md_is_byte_identical_after_spawn(self):
        self.pin("0.5.2")
        before = self.scope_md.read_bytes()
        self.spawn("dev", "gate-1")
        self.spawn("dev", "gate-2", "--dry-run")
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
        golden = winlaunch.run_script(rt / "bin" / "squad-process", ["compose", "dev", "--home", str(self.scope), "--agent", "gate-1", "--squad-dir", str(self.squad), "--plugin-root", str(rt), "--now", now],
                                text=True, encoding="utf-8", capture_output=True, timeout=60)
        self.assertEqual(golden.returncode, 0, golden.stderr)
        r = self.spawn("dev", "gate-1", env=dict(self.env, SQUAD_COMPOSE_NOW=now))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.scope / "roles" / "gate-1.rules.md").read_text(encoding="utf-8"), golden.stdout)
        self.assertEqual(self.scope_md.read_bytes(), before)


PATH_HERDR = r"""#!/usr/bin/env bash
[[ "$1 $2" == "agent get" ]] && { echo '{"error":{"code":"agent_not_found"}}'; exit 1; }
[[ "$1 $2" == "tab create" ]] || exit 0
printf '%s\n' "$@" > "$HERDR_ARGV"
echo "$PATH" > "$HERDR_CALLER_PATH"
echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


class SpawnRuntimePathEnvTest(unittest.TestCase):
    """The `PATH=` env sent to `herdr tab create`: the pinned runtime's bin dir in POSIX form (herdr is a native exe on
    Windows; a `C:` + backslash or `C:/` segment in a colon list makes the new shell's PATH unusable)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.squad = scoped_squad(self.root)
        (self.squad / "process.local.md").write_text("", encoding="utf-8")  # composed
        self.plugin = self.root / "plugin"  # a copy of bin/ whose squad-process is a stub: the runtime is ours
        shutil.copytree(BIN, self.plugin / "bin", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "templates", self.plugin / "templates")
        stub = self.plugin / "bin" / "squad-process"
        stub.write_text('#!/usr/bin/env bash\ncase $1 in\n  runtime) printf "%s\\n" "$STUB_RUNTIME" ;;\n'
                        '  compose) while [[ $# -gt 0 ]]; do [[ $1 == --out ]] && : > "$2"; shift; done ;;\n'
                        '  *) ;;\nesac\nexit 0\n', encoding="utf-8")
        stub.chmod(0o755)
        self.fake = self.root / "fakebin"
        self.fake.mkdir()
        self.write_exe("herdr", PATH_HERDR)
        self.argv, self.caller = self.root / "argv.txt", self.root / "caller_path.txt"
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_ARGV=str(self.argv),
                        HERDR_CALLER_PATH=str(self.caller), PATH=f"{self.fake}:{os.environ['PATH']}")

    def write_exe(self, name, text):
        (self.fake / name).write_text(text, encoding="utf-8", newline="\n")
        (self.fake / name).chmod(0o755)

    def spawn(self, runtime):
        self.env["STUB_RUNTIME"] = runtime
        script = self.plugin / "bin" / "squad-spawn"
        r = winlaunch.run_script(script, ["dev", "pa-1", "--scope", "sc1", "--prompt", "go"],
                                 env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        path_args = [a for a in self.argv.read_text(encoding="utf-8").splitlines() if a.startswith("PATH=")]
        self.assertEqual(len(path_args), 1, path_args)
        return path_args[0], self.caller.read_text(encoding="utf-8").strip()

    CYGPATH = r"""#!/usr/bin/env bash
[[ $1 == -u ]] && shift
p=${1//\\//}
[[ $p =~ ^([A-Za-z]):(.*)$ ]] && p=/${BASH_REMATCH[1],,}${BASH_REMATCH[2]}
printf '%s\n' "$p"
"""

    def test_a_windows_form_runtime_reaches_herdr_as_a_posix_path_before_the_callers_path(self):
        self.write_exe("cygpath", self.CYGPATH)
        arg, caller = self.spawn(r"C:\Users\me\sq\_runtime\0.6.3-aaaaaaaaaaaa")
        self.assertEqual(arg, f"PATH=/c/Users/me/sq/_runtime/0.6.3-aaaaaaaaaaaa/bin:{caller}")
        self.assertNotRegex(arg[len("PATH="):].removesuffix(caller), r"[A-Za-z]:[\\/]")

    def test_a_posix_runtime_is_passed_unchanged(self):
        arg, caller = self.spawn("/opt/rt/0.6.3-aaaaaaaaaaaa")  # no cygpath on Linux; on Windows cygpath keeps a POSIX path
        self.assertEqual(arg, f"PATH=/opt/rt/0.6.3-aaaaaaaaaaaa/bin:{caller}")

    def test_a_failing_cygpath_leaves_the_runtime_unchanged(self):
        self.write_exe("cygpath", "#!/usr/bin/env bash\nexit 1\n")
        arg, caller = self.spawn("/opt/rt/0.6.3-aaaaaaaaaaaa")
        self.assertEqual(arg, f"PATH=/opt/rt/0.6.3-aaaaaaaaaaaa/bin:{caller}")


if __name__ == "__main__":
    unittest.main()
