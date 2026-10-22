"""squad-start: text in, scope or goal folder + brief + fresh Manager out."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-start"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
if [[ "$1 $2" == "agent get" ]]; then echo '{"error":{"code":"agent_not_found"}}'; exit 1; fi
[[ $1 == tab ]] && echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


def run_child(cmd, env, timeout=30):
    """Run a child with UTF-8 bytes for argv and env: the parent may itself run under an ASCII locale."""
    enc = lambda x: str(x).encode("utf-8", "surrogateescape")
    return subprocess.run([enc(c) for c in cmd], env={enc(k): enc(v) for k, v in env.items()},
                          encoding="utf-8", capture_output=True, timeout=timeout)


class StartTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / ".claude" / "squads" / "t"
        (self.squad / "scopes").mkdir(parents=True)
        (self.squad / "goals").mkdir()
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def start(self, *args):
        return run_child([str(SCRIPT), *args], env=self.env)

    def herdr(self):
        return self.log.read_text(encoding="utf-8") if self.log.exists() else ""

    def test_lone_task_creates_the_scope_folder_brief_and_a_fresh_manager(self):
        r = self.start("Fix SEC-04: remove the committed default bypass key", "--touches", "wpapi")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["kind"], out["name"], out["manager"]), ("scope", "sec04", "t-mgr-sec04"))
        self.assertEqual(set(out), {"kind", "name", "dir", "manager", "tab", "process_update"})
        self.assertNotIn("board", (r.stdout + r.stderr).replace(str(ROOT), "").lower())
        sc = self.squad / "scopes" / "sec04"
        brief = (sc / "scope.md").read_text(encoding="utf-8")
        self.assertIn("Fix SEC-04: remove the committed default bypass key", brief)
        self.assertRegex(brief, r"(?m)^touches: wpapi$")
        self.assertRegex(brief, r"(?m)^goal:\s*$")
        for d in ("iterations", "tasks", "evidence", "roles"):
            self.assertTrue((sc / d).is_dir(), d)
        self.assertTrue((sc / "escalations.md").exists())
        h = self.herdr()
        self.assertIn("--label 🦀 Manager", h)
        self.assertIn(f"SCOPE_DIR={sc}", h)
        self.assertIn("scope.md", next(l for l in h.splitlines() if l.startswith("agent prompt")))
        self.assertIn("| t-mgr-sec04 | manager | sec04 |", (sc / "roster.md").read_text(encoding="utf-8"))

    def test_model_flag_sets_the_managers_model_else_the_role_default_applies(self):
        self.assertEqual(self.start("Task one", "--name", "one", "--touches", "a", "--model", "opus", "--effort", "medium").returncode, 0)
        self.assertRegex(self.herdr(), r"--model opus --effort medium\b")
        self.log.unlink()
        self.assertEqual(self.start("Task two", "--name", "two", "--touches", "b").returncode, 0)
        self.assertRegex(self.herdr(), r"--model sonnet --effort high\b")

    def test_the_managers_model_override_survives_a_respawn_for_a_scope_and_a_goal(self):
        for text, kind, var, flag in (("Task one", "scopes", "SCOPE_DIR", "--scope"), ("goal: Big thing", "goals", "GOAL_DIR", "--goal")):
            with self.subTest(kind=kind):
                name = "one" if kind == "scopes" else "big"
                r = self.start(text, "--name", name, "--touches", name, "--model", "sonnet", "--effort", "low")
                self.assertEqual(r.returncode, 0, r.stderr)
                home = self.squad / kind / name
                self.assertEqual((home / "roles" / f"t-mgr-{name}.overrides").read_text(encoding="utf-8"), "model=sonnet\neffort=low\n")
                env = {**self.env, var: str(home)}
                d = run_child([str(SCRIPT.parent / "squad-respawn"), f"t-mgr-{name}", "--dry-run"], env=env)
                self.assertEqual(d.returncode, 0, d.stderr)
                self.assertRegex(d.stdout, rf"squad-spawn manager t-mgr-{name} {flag} {name} .*--model sonnet --effort low ")

    def test_name_comes_from_a_ticket_id_else_a_short_slug_and_can_be_overridden(self):
        self.assertEqual(json.loads(self.start("Regroup the settings tabs", "--touches", "x").stdout)["name"], "regroup-settings")
        self.assertEqual(json.loads(self.start("Anything", "--name", "mine", "--touches", "y").stdout)["name"], "mine")

    def test_goal_prefix_creates_a_goal_folder_and_a_goal_manager(self):
        r = self.start("goal: Rebuild the settings page", "--name", "settings", "--touches", "wpfe")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["kind"], out["name"], out["manager"]), ("goal", "settings", "t-mgr-settings"))
        g = self.squad / "goals" / "settings"
        self.assertIn("Rebuild the settings page", (g / "goal.md").read_text(encoding="utf-8"))
        self.assertNotIn("goal:", (g / "goal.md").read_text(encoding="utf-8").splitlines()[2])  # the prefix is not part of the brief
        for p in ("shared/decisions.md", "shared/summaries", "shared/contracts", "roles", "roster.md", "escalations.md"):
            self.assertTrue((g / p).exists(), p)
        self.assertIn(f"GOAL_DIR={g}", self.herdr())
        self.assertNotIn("SCOPE_DIR", self.herdr())
        self.assertIn("| t-mgr-settings | manager |", (g / "roster.md").read_text(encoding="utf-8"))

    def test_in_goal_creates_only_the_scope_folder_naming_its_goal(self):
        self.start("goal: Rebuild", "--name", "g1", "--touches", "wpfe")
        self.log.unlink()
        r = self.start("Tabs regroup", "--in-goal", "g1", "--name", "s1", "--touches", "wpfe/tabs", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex((self.squad / "scopes" / "s1" / "scope.md").read_text(encoding="utf-8"), r"(?m)^goal: g1$")
        self.assertNotIn("agent start", self.herdr())  # the goal Manager runs it, no Manager of its own
        self.assertEqual(json.loads(r.stdout)["manager"], None)

    def test_in_goal_needs_an_existing_goal(self):
        self.assertNotEqual(self.start("x", "--in-goal", "nope", "--name", "s1").returncode, 0)

    def test_name_clash_with_a_scope_a_goal_or_an_archived_one_is_refused(self):
        self.start("one", "--name", "dup", "--touches", "a")
        self.log.unlink()
        for existing in ("scopes/dup", "goals/dup", "scopes/_done/dup", "goals/_done/dup"):
            with self.subTest(existing=existing):
                p = self.squad / existing
                p.mkdir(parents=True, exist_ok=True)
                kind = ["goal: two"] if existing.startswith("scopes") else ["two"]
                r = self.start(*kind, "--name", "dup", "--touches", "b")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("already", r.stderr)
                self.assertEqual(self.herdr(), "")

    def test_overlap_with_an_open_scope_warns_and_creates_nothing_until_yes(self):
        self.start("first", "--name", "one", "--touches", "wpfe/src/settings")
        self.log.unlink()
        r = self.start("second", "--name", "two", "--touches", "wpfe")
        self.assertEqual(r.returncode, 3)
        self.assertIn("one", r.stderr)
        self.assertFalse((self.squad / "scopes" / "two").exists())
        self.assertEqual(self.herdr(), "")
        r = self.start("second", "--name", "two", "--touches", "wpfe", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_disjoint_touches_and_archived_scopes_do_not_count_as_overlap(self):
        self.start("first", "--name", "one", "--touches", "wpapi")
        done = self.squad / "scopes" / "_done" / "old"
        done.mkdir(parents=True)
        (done / "scope.md").write_text("touches: wpfe\n", encoding="utf-8")
        self.assertEqual(self.start("second", "--name", "two", "--touches", "wpfe").returncode, 0)

    def test_a_flat_squad_is_refused_so_it_is_not_converted_by_accident(self):
        (self.squad / "scopes").rmdir()
        (self.squad / "goals").rmdir()
        (self.squad / "roster.md").write_text("| Agent |\n|---|\n", encoding="utf-8")
        r = self.start("x", "--name", "one")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("flat", r.stderr)

    def test_a_manager_name_over_32_characters_is_refused(self):
        r = self.start("x", "--name", "a" * 30)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--name", r.stderr)

    def test_failed_spawn_rolls_the_new_folder_back(self):
        self.env["HERDR_ENV"] = "0"
        r = self.start("x", "--name", "one", "--touches", "z")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.squad / "scopes" / "one").exists())

    def test_resume_starts_a_new_manager_for_an_existing_scope_without_touching_its_files(self):
        self.start("Fix it", "--name", "one", "--touches", "a")
        sc = self.squad / "scopes" / "one"
        (sc / "tasks" / "T-1.md").write_text("keep me", encoding="utf-8")
        self.log.unlink()
        r = self.start("--resume", "one")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["manager"], "t-mgr-one")
        self.assertNotIn("board", json.loads(r.stdout))
        self.assertEqual((sc / "tasks" / "T-1.md").read_text(encoding="utf-8"), "keep me")
        h = self.herdr()
        self.assertIn(f"SCOPE_DIR={sc}", h)
        prompt = next(l for l in h.splitlines() if l.startswith("agent prompt"))
        self.assertIn("RESPAWN", prompt)
        self.assertIn("roles/t-mgr-one.notes.md", prompt)

    def test_resume_a_goal_uses_goal_dir(self):
        self.start("goal: Rebuild", "--name", "g1", "--touches", "wpfe")
        self.log.unlink()
        r = self.start("--resume", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"GOAL_DIR={self.squad / 'goals' / 'g1'}", self.herdr())

    def test_resume_refuses_a_scope_that_belongs_to_a_goal_unknown_names_and_extra_text(self):
        self.start("goal: Rebuild", "--name", "g1", "--touches", "wpfe")
        self.start("Tabs", "--in-goal", "g1", "--name", "s1", "--touches", "wpfe/tabs", "--yes")
        r = self.start("--resume", "s1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("g1", r.stderr)
        self.assertNotEqual(self.start("--resume", "nope").returncode, 0)
        self.assertNotEqual(self.start("text", "--resume", "g1").returncode, 0)

    def test_dry_run_creates_nothing(self):
        r = self.start("x", "--name", "one", "--touches", "z", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.squad / "scopes" / "one").exists())
        self.assertEqual(self.herdr(), "")
        self.assertIn("would", r.stdout)
        self.assertNotIn("board", (r.stdout + r.stderr).replace(str(ROOT), "").lower())


    def dry_lines(self, *args):
        r = self.start(*args, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.herdr(), "")
        return [l for l in r.stdout.splitlines() if l.startswith("manager ")]

    def test_dry_run_shows_the_managers_model_and_effort_with_their_source(self):
        new = ("x", "--name", "one", "--touches", "z")
        self.assertEqual(self.dry_lines(*new), ["manager model: sonnet (from template)", "manager effort: high (from template)"])
        (self.squad / "settings").mkdir()
        (self.squad / "settings" / "manager.local.json").write_text('{"model": "haiku"}', encoding="utf-8")
        self.assertEqual(self.dry_lines(*new), ["manager model: haiku (from squad settings)", "manager effort: high (from template)"])
        self.assertEqual(self.dry_lines(*new, "--model", "opus", "--effort", "low"),
                         ["manager model: opus (from flag)", "manager effort: low (from flag)"])
        self.assertEqual(len(self.dry_lines("goal: Big", "--name", "g")), 2)

    def test_resume_dry_run_shows_them_too_and_in_goal_has_no_manager_lines(self):
        (self.squad / "scopes" / "one").mkdir()
        self.assertEqual(self.dry_lines("--resume", "one", "--model", "opus"),
                         ["manager model: opus (from flag)", "manager effort: high (from template)"])
        roles = self.squad / "scopes" / "one" / "roles"
        roles.mkdir()
        (roles / "t-mgr-one.overrides").write_text("model=opus\neffort=low\n", encoding="utf-8")
        self.assertEqual(self.dry_lines("--resume", "one"), ["manager model: opus (from recorded override)", "manager effort: low (from recorded override)"])
        self.assertEqual(self.dry_lines("--resume", "one", "--effort", "max"), ["manager model: opus (from recorded override)", "manager effort: max (from flag)"])
        self.start("Two", "--name", "two", "--touches", "q", "--model", "opus", "--effort", "low")  # keep: recorded choice is passed on
        self.log.unlink()
        r = self.start("--resume", "two")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(self.herdr(), r"--model opus --effort low\b")
        self.assertTrue((self.squad / "scopes" / "two" / "roles" / "t-mgr-two.overrides").exists())
        (self.squad / "goals" / "g1").mkdir()
        self.assertEqual(self.dry_lines("x", "--in-goal", "g1", "--name", "two"), [])


class WorkspaceRenameTest(unittest.TestCase):
    """squad-start names the caller's herdr workspace after the goal or lone scope; failures never stop the start."""

    def setUp(self):
        StartTest.setUp(self)
        self.env["HERDR_WORKSPACE_ID"] = "wK"

    tearDown = StartTest.tearDown
    start = StartTest.start
    herdr = StartTest.herdr

    def renames(self):
        return [l for l in self.herdr().splitlines() if l.startswith("workspace rename")]

    def fake(self, extra):
        f = Path(self.tmp.name) / "fakebin" / "herdr"
        f.write_text(FAKE_HERDR.replace("exit 0\n", "") + extra + "\nexit 0\n", encoding="utf-8")

    def test_a_lone_scope_names_the_workspace_after_the_scope(self):
        self.assertEqual(self.start("Task one", "--name", "one", "--touches", "a").returncode, 0)
        self.assertEqual(self.renames(), ["workspace rename wK one"])

    def test_a_goal_names_the_workspace_after_the_goal(self):
        self.start("goal: Big", "--name", "g1", "--touches", "a")
        self.assertEqual(self.renames(), ["workspace rename wK g1"])

    def test_a_scope_in_a_goal_leaves_the_name_alone(self):
        self.start("goal: Big", "--name", "g1", "--touches", "a")
        self.log.unlink()
        self.start("Part", "--in-goal", "g1", "--name", "p1", "--touches", "b")
        self.assertEqual(self.renames(), [])

    def test_resume_renames_to_the_resumed_name(self):
        self.start("goal: Big", "--name", "g1", "--touches", "a")
        self.start("Task one", "--name", "one", "--touches", "b")
        self.log.unlink()
        self.start("--resume", "one")
        self.start("--resume", "g1")
        self.assertEqual(self.renames(), ["workspace rename wK one", "workspace rename wK g1"])

    def test_two_starts_in_a_row_each_rename(self):
        self.start("Task one", "--name", "one", "--touches", "a")
        self.start("Task two", "--name", "two", "--touches", "b")
        self.assertEqual(self.renames(), ["workspace rename wK one", "workspace rename wK two"])

    def test_dry_run_renames_nothing(self):
        self.start("x", "--name", "one", "--dry-run")
        self.start("x", "--name", "one", "--touches", "a")
        self.log.unlink()
        self.start("--resume", "one", "--dry-run")
        self.assertEqual(self.renames(), [])

    def test_without_a_workspace_id_nothing_is_run_and_nothing_is_said(self):
        del self.env["HERDR_WORKSPACE_ID"]
        r = self.start("x", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.renames(), [])
        self.assertNotIn("workspace", r.stderr)

    def test_outside_herdr_the_rename_is_never_reached(self):
        # spawn itself needs HERDR_ENV=1, so a start outside herdr dies before the rename; the guard is in name_workspace
        self.env["HERDR_ENV"] = "0"
        self.start("x", "--name", "one", "--touches", "a")
        self.assertEqual(self.renames(), [])

    def test_a_refusing_herdr_gives_one_warning_and_the_start_goes_on(self):
        self.fake('[[ "$1 $2" == "workspace rename" ]] && { echo "no such workspace" >&2; exit 1; }')
        r = self.start("Task one", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["manager"], "t-mgr-one")
        self.assertEqual(r.stderr.strip().splitlines().count("workspace not renamed: no such workspace"), 1)
        self.assertTrue((self.squad / "scopes" / "one" / "scope.md").exists())

    def test_a_failed_manager_start_does_not_rename(self):
        self.fake('[[ $1 == tab ]] && exit 1')
        r = self.start("x", "--name", "one", "--touches", "a")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.renames(), [])


ROOT = SCRIPT.parent.parent


class ProcessUpdateTest(unittest.TestCase):
    """squad-start warns (stderr and `process_update` in the JSON) when process.md is not current; it never blocks."""

    def setUp(self):
        StartTest.setUp(self)

    tearDown = StartTest.tearDown
    herdr = StartTest.herdr

    def plugin(self, version):
        plugin = Path(self.tmp.name) / "plugin"
        shutil.rmtree(plugin, ignore_errors=True)
        shutil.copytree(ROOT / "bin", plugin / "bin", ignore=shutil.ignore_patterns("__pycache__"))
        os.symlink(ROOT / "agents", plugin / "agents")
        shutil.copytree(ROOT / "templates", plugin / "templates")
        (plugin / "templates" / "squad" / "process.md").write_text(
            "# T\n" + (f"\nprocess-version: {version}\n" if version else ""), encoding="utf-8")
        return plugin / "bin" / "squad-start"

    def run_start(self, plugin_version, squad_text, *args):
        (self.squad / "process.md").write_text(squad_text, encoding="utf-8")
        return run_child([str(self.plugin(plugin_version)), *args], env=self.env)

    def test_each_state_gives_its_one_line_and_the_json_key(self):
        for squad_text, plugin_v, words in (
                ("process-version: 1\n", 2, ("version 1", "is 2", "migrate the process", "/squad:squad-process-update")),
                ("# T\n", 2, ("no process-version line", "treated as version 1")),
                ("process-version: 1.2\n", 2, ("malformed", "treated as version 1")),
                ("process-version: 3\n", 2, ("newer than this plugin's 2", "update the plugin"))):
            with self.subTest(squad_text=squad_text):
                name = f"s{abs(hash(squad_text)) % 10**6}"
                r = self.run_start(plugin_v, squad_text, "Task", "--name", name, "--touches", name)
                self.assertEqual(r.returncode, 0, r.stderr)
                msg = json.loads(r.stdout)["process_update"]
                line = next(l for l in r.stderr.splitlines() if l.startswith("process update: "))
                self.assertEqual(line, "process update: " + msg)
                for w in words:
                    self.assertIn(w, msg)

    def test_current_squad_is_silent_and_the_key_is_null(self):
        r = self.run_start(2, "process-version: 2\n", "Task", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIsNone(json.loads(r.stdout)["process_update"])
        self.assertNotIn("process update", r.stderr)

    def test_dry_run_and_resume_warn_too(self):
        r = self.run_start(2, "process-version: 1\n", "x", "--name", "one", "--touches", "z", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("process update: ", r.stderr)
        self.assertFalse((self.squad / "scopes" / "one").exists())
        self.run_start(2, "process-version: 2\n", "Task", "--name", "one", "--touches", "a")
        r = self.run_start(2, "process-version: 1\n", "--resume", "one")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("process update: ", r.stderr)
        self.assertIn("migrate the process", json.loads(r.stdout)["process_update"])

    def test_a_template_without_the_line_or_a_missing_squad_file_never_stops_the_start(self):
        r = self.run_start(None, "process-version: 1\n", "Task", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIsNone(json.loads(r.stdout)["process_update"])
        self.assertIn("process version not checked", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_the_warning_changes_no_file(self):
        (self.squad / "process.md").write_text("process-version: 1\n", encoding="utf-8")
        self.run_start(2, "process-version: 1\n", "x", "--name", "one", "--touches", "z", "--dry-run")
        self.assertEqual((self.squad / "process.md").read_text(encoding="utf-8"), "process-version: 1\n")
        self.assertEqual(sorted(p.name for p in self.squad.iterdir()), ["goals", "process.md", "scopes"])


def load_squad_start():
    from importlib.machinery import SourceFileLoader
    return SourceFileLoader("squad_start_mod", str(SCRIPT)).load_module()


class PickBashTest(unittest.TestCase):
    """pick_bash is pure: which/exists are injected, so the Windows rules run on Linux."""

    GIT = "C:\\Program Files\\Git"
    ROOT = "C:\\Windows"

    def pick(self, bash, git=None, existing=()):
        mod = load_squad_start()
        which = {"bash": bash, "git": git}.get
        return mod.pick_bash(which, lambda p: p in existing, True, self.ROOT)

    def test_a_path_bash_is_taken(self):
        self.assertEqual(self.pick(self.GIT + "\\bin\\bash.exe"), self.GIT + "\\bin\\bash.exe")

    def test_the_system32_and_windowsapps_hits_are_rejected(self):
        for bad in ("C:\\Windows\\System32\\bash.exe", "c:/windows/system32/bash.exe",
                    "C:\\Users\\x\\AppData\\Local\\Microsoft\\WindowsApps\\bash.exe"):
            with self.subTest(bad=bad):
                self.assertIsNone(self.pick(bad))

    def test_the_fallback_finds_git_bash_from_each_git_exe_location(self):
        want = self.GIT + "\\bin\\bash.exe"
        for git in ("\\cmd\\git.exe", "\\bin\\git.exe", "\\mingw64\\bin\\git.exe"):
            with self.subTest(git=git):
                self.assertEqual(self.pick("C:\\Windows\\System32\\bash.exe", self.GIT + git, (want,)), want)

    def test_no_bash_anywhere_is_none(self):
        self.assertIsNone(self.pick(None))
        self.assertIsNone(self.pick(None, self.GIT + "\\cmd\\git.exe"))

    def test_off_windows_any_hit_is_taken(self):
        mod = load_squad_start()
        self.assertEqual(mod.pick_bash({"bash": "/usr/bin/bash"}.get, lambda p: False, False, ""), "/usr/bin/bash")


class LauncherTest(unittest.TestCase):
    """squad-start runs squad-spawn as [bash, <path>] and needs bash before it writes anything."""

    def setUp(self):
        StartTest.setUp(self)
        self.real_bash = shutil.which("bash")
        self.argv = self.root / "bash.argv"
        stub = self.root / "fakebin" / "bash"
        stub.write_text(f'#!{self.real_bash}\n[ -e "$BASH_ARGV_LOG" ] || printf "%s\\n" "$@" > "$BASH_ARGV_LOG"\nexec {self.real_bash} "$@"\n', encoding="utf-8")
        stub.chmod(0o755)
        self.env["BASH_ARGV_LOG"] = str(self.argv)

    tearDown = StartTest.tearDown
    start = StartTest.start
    herdr = StartTest.herdr

    def test_new_scope_and_resume_run_squad_spawn_through_bash(self):
        for args in (("Task one", "--name", "one", "--touches", "a"), ("--resume", "one")):
            with self.subTest(args=args):
                self.argv.unlink(missing_ok=True)
                r = self.start(*args)
                self.assertEqual(r.returncode, 0, r.stderr)
                lines = self.argv.read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines[0], (SCRIPT.parent / "squad-spawn").as_posix())
                self.assertEqual(lines[1:3], ["manager", "t-mgr-one"])

    def test_no_bash_is_one_line_and_nothing_is_written_for_a_new_scope_and_for_resume(self):
        self.assertEqual(self.start("Task one", "--name", "one", "--touches", "a").returncode, 0)
        self.log.unlink()
        self.env.update(HERDR_WORKSPACE_ID="wK", PATH=str(self.root / "fakebin"))
        (self.root / "fakebin" / "bash").unlink()
        for args, made in ((("Task two", "--name", "two", "--touches", "b"), "two"), (("--resume", "one"), None)):
            with self.subTest(args=args):
                r = run_child([shutil.which("python3"), str(SCRIPT), *args], env=self.env)
                self.assertNotEqual(r.returncode, 0)
                lines = [l for l in r.stderr.splitlines() if not l.startswith("process update")]
                self.assertEqual(len(lines), 1, r.stderr)
                self.assertIn("bash", lines[0])
                self.assertIn("Git for Windows", lines[0])
                self.assertNotIn("Traceback", r.stderr)
                if made:
                    self.assertFalse((self.squad / "scopes" / made).exists())
                self.assertEqual(self.herdr(), "")

    def test_dry_run_needs_no_bash(self):
        self.env["PATH"] = str(self.root / "fakebin")
        (self.root / "fakebin" / "bash").unlink()
        r = run_child([shutil.which("python3"), str(SCRIPT), "x", "--name", "one", "--dry-run"],
                           env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would run: ", r.stdout)

    def test_a_c_locale_with_an_emoji_label_runs_clean_and_writes_utf8_lf(self):
        self.env.update(PYTHONUTF8="0", LC_ALL="C", PYTHONIOENCODING="cp1252")
        r = self.start("Fix 🦀 café", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout)["manager"], "t-mgr-one")
        raw = (self.squad / "scopes" / "one" / "scope.md").read_bytes()
        self.assertIn("Fix 🦀 café".encode("utf-8"), raw)
        self.assertNotIn(b"\r", raw)
        self.assertEqual(self.start("--resume", "one").returncode, 0)

    def test_a_project_dir_with_a_space_and_an_emoji_works_for_new_and_resume(self):
        odd = self.root / os.fsdecode("with space 🦀".encode("utf-8"))
        odd.mkdir()
        squad = odd / ".claude" / "squads" / "t"
        shutil.copytree(self.squad, squad)
        self.env["SQUAD_DIR"] = str(squad)
        self.assertEqual(self.start("Task one", "--name", "one", "--touches", "a").returncode, 0)
        r = self.start("--resume", "one")
        self.assertEqual(r.returncode, 0, r.stderr)
        want = str(squad / "scopes" / "one").encode("utf-8", "surrogateescape").decode("utf-8")
        self.assertIn(f"SCOPE_DIR={want}", self.herdr())


class InstructionsTest(unittest.TestCase):
    def test_squad_init_scaffolds_a_composed_squad_and_never_copies_process_md(self):  # ticket 09
        text = (ROOT / "skills" / "squad-init" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("squad-process scaffold", text)
        self.assertIn("never copies `process.md`", text)
        self.assertIn("squad-process adopt", text)
        self.assertNotIn("Copy everything from", text)

    def test_squad_start_skill_tells_the_user_and_never_runs_the_update_unasked(self):
        text = (ROOT / "skills" / "squad-start" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`process_update`", text)
        self.assertIn("Never run it unasked", text)

    def test_skill_confirms_the_managers_model_and_effort_before_the_run_for_start_and_resume(self):  # ticket 19
        text = (ROOT / "skills" / "squad-start" / "SKILL.md").read_text(encoding="utf-8")
        confirm = text.index("Confirm the Manager's model and effort")
        self.assertLess(confirm, text.index("6. Run:"))
        self.assertIn("also before `--resume`", text)
        self.assertIn("then do step 5a", text)
        for word in ("keep", "change model", "change effort", "`--model`", "`--effort`", "`opus`", "`max`", ".overrides"):
            self.assertIn(word, text)


if __name__ == "__main__":
    unittest.main()
