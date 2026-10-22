"""squadruntime (mode, pin, pinned runtime) and the composed paths of squad-spawn, squad-respawn, squad-start (ticket 05).

The plugin under test is a throwaway git copy of this plugin with the 04 fixture rule files (tests/fixtures/rules/compose)
in templates/squad/process/: this branch has no converted rule files yet.
"""
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
FIX = Path(__file__).resolve().parent / "fixtures" / "rules" / "compose"
sys.path.insert(0, str(BIN))
import squadruntime as rt  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get")
    grep -q "^agent rename $3 " "$HERDR_LOG" && { echo '{"error":{"code":"agent_not_found"}}'; exit 1; }
    [[ " ${LIVE:-} " == *" $3 "* ]] && { echo '{"result":{"agent":{"pane_id":"p-old"}}}'; exit 0; }
    echo '{"error":{"code":"agent_not_found"}}'; exit 1 ;;
  "tab create") echo '{"result":{"root_pane":{"pane_id":"p-new"},"tab":{"tab_id":"t-new"}}}' ;;
esac
exit 0
"""


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **GIT_ENV}).stdout.strip()


def make_plugin(dest):
    """Copy of this plugin plus the fixture rule files, committed in a fresh repo -> (path, version, sha)."""
    dest = Path(dest)
    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git", ".worktrees", ".scratch", "tests", "__pycache__"))
    pdir = dest / "templates" / "squad" / "process"
    pdir.mkdir(parents=True, exist_ok=True)
    for f in (FIX / "templates" / "squad" / "process").glob("*.md"):
        shutil.copy(f, pdir / f.name)
    git("init", "-q", cwd=dest)
    git("add", "-A", cwd=dest)
    git("commit", "-q", "-m", "fixture plugin", cwd=dest)
    version = json.loads((dest / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    return dest, version, git("rev-parse", "HEAD", cwd=dest)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._ptmp = tempfile.TemporaryDirectory()
        cls.plugin, cls.version, cls.sha = make_plugin(Path(cls._ptmp.name) / "plugin")

    @classmethod
    def tearDownClass(cls):
        cls._ptmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.squad = self.root / ".claude" / "squads" / "t"
        (self.squad / "scopes").mkdir(parents=True)
        (self.squad / "goals").mkdir()
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log), PATH=f"{fake}:{os.environ['PATH']}")

    def composed(self):
        (self.squad / "process.local.md").write_text("", encoding="utf-8")

    def scope(self, name="sc1", size="M", pin="default", goal=""):
        d = self.squad / "scopes" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "roles").mkdir(exist_ok=True)
        pin = f"{self.version} {self.sha}" if pin == "default" else pin
        text = f"# Scope: {name}\n\ngoal: {goal}\ntouches: x\nsize: {size}\nqa: full\ndesign: no\n"
        if pin:
            text += f"plugin: {pin}\n"
        (d / "scope.md").write_text(text + "\n## Constraints\n", encoding="utf-8", newline="\n")
        (d / "roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n",
                                     encoding="utf-8")
        return d

    def herdr(self):
        return self.log.read_text(encoding="utf-8") if self.log.exists() else ""

    def run_bin(self, name, *args, plugin=None):
        return subprocess.run([str((plugin or self.plugin) / "bin" / name), *args], env=self.env, text=True,
                              encoding="utf-8", capture_output=True, timeout=60)

    def spawn(self, role="dev", name="t-dev-sc1", *args, scope="sc1"):
        return self.run_bin("squad-spawn", role, name, "--scope", scope, *args)

    def runtime_dir(self):
        return self.squad / "_runtime" / f"{self.version}-{self.sha[:12]}"


class ModeTest(Base):
    def test_three_layouts(self):
        self.assertEqual(rt.mode(str(self.squad)), "none")
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        self.assertEqual(rt.mode(str(self.squad)), "legacy")
        self.composed()
        self.assertEqual(rt.mode(str(self.squad)), "composed")  # process.local.md wins, with or without process.md
        (self.squad / "process.md").unlink()
        self.assertEqual(rt.mode(str(self.squad)), "composed")

    def test_cli_prints_the_mode(self):
        r = subprocess.run([sys.executable, str(BIN / "squad-process"), "mode", "--squad-dir", str(self.squad)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "none"))

    def test_check_is_quiet_in_a_composed_squad(self):
        self.composed()
        r = subprocess.run([sys.executable, str(BIN / "squad-process"), "check", "--quiet", "--squad-dir", str(self.squad)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))


class PinTest(Base):
    def test_a_bad_sha_or_version_exits_2(self):
        for sha in ("--upload-pack=x", "../x", "abcdef", "ABCDEF1", "a" * 41):
            with self.subTest(sha=sha), self.assertRaises(rt.RuntimeError_) as c:
                rt.materialise(str(self.squad), "1.0.0", sha, str(self.plugin))
            self.assertEqual(c.exception.code, 2)
        for version in ("../1", "-x", "1 2", ""):
            with self.subTest(version=version), self.assertRaises(rt.RuntimeError_) as c:
                rt.materialise(str(self.squad), version, "abc1234", str(self.plugin))
            self.assertEqual(c.exception.code, 2)
        self.assertFalse((self.squad / "_runtime").exists())

    def test_the_cli_exits_2_for_an_unparseable_pin_and_for_a_missing_one(self):
        for pin in ("only-one-token", "1.0.0 --upload-pack=x", "1.0.0 abc1234 extra"):
            with self.subTest(pin=pin):
                home = self.scope(pin=pin)
                r = self.run_bin("squad-process", "runtime", "--squad-dir", str(self.squad), "--home", str(home))
                self.assertEqual(r.returncode, 2, r.stderr)
        home = self.scope(pin="")
        r = self.run_bin("squad-process", "runtime", "--squad-dir", str(self.squad), "--home", str(home))
        self.assertEqual(r.returncode, 2)
        self.assertIn("plugin: <version> <sha>", r.stderr)

    def test_plugin_pin_file(self):
        self.assertIsNone(rt.read_pin_file(str(self.squad)))
        (self.squad / "plugin.pin").write_text("1.2.3 abc1234\n", encoding="utf-8")
        self.assertEqual(rt.read_pin_file(str(self.squad)), ("1.2.3", "abc1234"))
        (self.squad / "plugin.pin").write_text("garbage\n", encoding="utf-8")
        with self.assertRaises(rt.RuntimeError_) as c:
            rt.read_pin_file(str(self.squad))
        self.assertEqual(c.exception.code, 2)

    def test_versions_compare_as_numbers(self):
        self.assertLess(rt.vkey("0.9.0"), rt.vkey("0.10.0"))


class MaterialiseTest(Base):
    def test_builds_a_complete_tree_once_and_reuses_it(self):
        target = rt.materialise(str(self.squad), self.version, self.sha, str(self.plugin))
        self.assertEqual(Path(target), self.runtime_dir().resolve())
        self.assertTrue((Path(target) / "templates/squad/process/core.md").is_file())
        self.assertFalse((Path(target) / ".git").exists())
        self.assertTrue(os.access(Path(target) / "bin" / "squad-spawn", os.X_OK))
        self.assertFalse([p for p in Path(target).rglob("*") if p.is_symlink()])
        (Path(target) / "marker").write_text("m", encoding="utf-8")
        again = rt.materialise(str(self.squad), self.version, self.sha, str(self.plugin))
        self.assertEqual(again, target)
        self.assertTrue((Path(target) / "marker").exists())  # reused, not rebuilt
        self.assertEqual([p.name for p in (self.squad / "_runtime").iterdir()], [Path(target).name])

    def test_a_short_sha_names_the_folder_with_what_it_has(self):
        target = rt.materialise(str(self.squad), self.version, self.sha[:7], str(self.plugin))
        self.assertTrue(Path(target).name.endswith("-" + self.sha[:7]))

    def test_dry_run_creates_nothing(self):
        target = rt.materialise(str(self.squad), self.version, self.sha, str(self.plugin), dry_run=True)
        self.assertTrue(target.endswith(f"{self.version}-{self.sha[:12]}"))
        self.assertFalse((self.squad / "_runtime").exists())

    def test_concurrent_materialisations_leave_one_complete_folder(self):
        barrier, results, errors = threading.Barrier(4), [], []

        def go():
            try:
                barrier.wait()
                results.append(rt.materialise(str(self.squad), self.version, self.sha, str(self.plugin)))
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=go) for _ in range(4)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(errors, [])
        self.assertEqual(len(set(results)), 1)
        self.assertEqual([p.name for p in (self.squad / "_runtime").iterdir()], [self.runtime_dir().name])
        self.assertTrue((self.runtime_dir() / "bin" / "squad-spawn").is_file())

    def test_a_precreated_target_wins_the_rename_and_the_temp_folder_goes(self):
        real = os.rename

        def racing(src, dst):  # another spawn lands the target between our extract and our rename
            shutil.copytree(src, dst)
            return real(src, dst)  # now fails: the target exists

        orig = rt.os.rename
        rt.os.rename = racing
        try:
            target = rt.materialise(str(self.squad), self.version, self.sha, str(self.plugin))
        finally:
            rt.os.rename = orig
        self.assertEqual([p.name for p in (self.squad / "_runtime").iterdir()], [Path(target).name])

    def test_a_version_that_differs_from_the_commit_is_refused_and_nothing_stays(self):
        with self.assertRaises(rt.RuntimeError_) as c:
            rt.materialise(str(self.squad), "0.0.1", self.sha, str(self.plugin))
        self.assertEqual(c.exception.code, 1)
        self.assertIn("0.0.1", str(c.exception))
        self.assertEqual(list((self.squad / "_runtime").iterdir()), [])

    def test_an_existing_runtime_of_another_version_is_removed(self):
        bad = self.squad / "_runtime" / f"0.0.1-{self.sha[:12]}"
        (bad / ".claude-plugin").mkdir(parents=True)
        (bad / ".claude-plugin" / "plugin.json").write_text('{"version": "9.9.9"}', encoding="utf-8")
        with self.assertRaises(rt.RuntimeError_) as c:
            rt.materialise(str(self.squad), "0.0.1", self.sha, str(self.plugin))
        self.assertEqual(c.exception.code, 1)
        self.assertFalse(bad.exists())

    def test_an_unknown_commit_exits_1_with_the_restore_command(self):
        with self.assertRaises(rt.RuntimeError_) as c:
            rt.materialise(str(self.squad), self.version, "deadbeef" * 5, str(self.plugin))
        self.assertEqual(c.exception.code, 1)
        text = str(c.exception)
        self.assertIn("deadbeef", text)
        self.assertIn("git -C", text)
        self.assertIn("archive", text)
        self.assertEqual(list((self.squad / "_runtime").iterdir()), [])

    def test_no_repo_uses_the_installed_cache_only_when_its_sha_matches(self):
        norepo = self.root / "norepo"
        shutil.copytree(self.plugin, norepo, ignore=shutil.ignore_patterns(".git"))
        listing = self.root / "installed_plugins.json"
        entry = {"squad@market": [{"scope": "user", "installPath": str(norepo), "version": self.version,
                                   "gitCommitSha": self.sha}]}
        listing.write_text(json.dumps({"version": 2, "plugins": entry}), encoding="utf-8")
        os.environ["SQUAD_INSTALLED_PLUGINS"] = str(listing)
        self.addCleanup(os.environ.pop, "SQUAD_INSTALLED_PLUGINS", None)
        # the plugin root is a folder without a repo (a marketplace copy)
        got = rt.materialise(str(self.squad), self.version, self.sha, str(norepo))
        self.assertEqual(got, str(norepo))
        self.assertFalse((self.squad / "_runtime" / f"{self.version}-{self.sha[:12]}").exists())
        with self.assertRaises(rt.RuntimeError_) as c:
            rt.materialise(str(self.squad), self.version, "abcdef1234567890", str(norepo))
        self.assertEqual(c.exception.code, 1)
        self.assertIn("abcdef1234567890", str(c.exception))

    def test_a_runtime_inside_a_repo_is_not_taken_for_the_plugin_repo(self):
        project = self.root / "project"
        project.mkdir()
        git("init", "-q", cwd=project)
        runtime = project / ".claude" / "squads" / "t" / "_runtime" / "v"
        runtime.mkdir(parents=True)
        self.assertFalse(rt.is_repo_root(str(runtime)))
        self.assertTrue(rt.is_repo_root(str(project)))
        with self.assertRaises(rt.RuntimeError_) as c:  # no repo of its own, no cache: refuses, never the project's repo
            rt.running_pin(str(runtime))
        self.assertEqual(c.exception.code, 1)

    def test_running_pin_reports_a_dirty_tree(self):
        clone = self.root / "clone"
        shutil.copytree(self.plugin, clone)
        self.assertEqual(rt.running_pin(str(clone))[1:], (self.sha, False))
        (clone / "extra.txt").write_text("x", encoding="utf-8")
        self.assertTrue(rt.running_pin(str(clone))[2])


class SpawnComposedTest(Base):
    def setUp(self):
        super().setUp()
        self.composed()

    def calls(self, prefix):
        return [ln for ln in self.herdr().splitlines() if ln.startswith(prefix)]

    def test_argv_has_the_rules_file_the_pinned_plugin_and_path(self):
        self.scope()
        r = self.spawn("dev", "t-dev-sc1", "--prompt", "Task 05 is yours.")
        self.assertEqual(r.returncode, 0, r.stderr)
        rules = self.squad / "scopes" / "sc1" / "roles" / "t-dev-sc1.rules.md"
        start = self.calls("agent start")[0]
        self.assertIn(f"--append-system-prompt-file {rules}", start)
        self.assertEqual(start.count("--plugin-dir"), 1)
        self.assertIn(f"--plugin-dir {self.runtime_dir()}", start)
        self.assertEqual(start.count("--settings"), 1)
        self.assertNotIn("enabledPlugins", start)
        tab = self.calls("tab create")[0]
        self.assertIn(f"PATH={self.runtime_dir()}/bin:", tab)
        self.assertIn(f"SQUAD_PLUGIN_DIR={self.runtime_dir()}", tab)
        text = rules.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Your process rules"), text[:60])
        self.assertIn("agent: t-dev-sc1 · role: dev · scope: sc1 (size M", text)
        self.assertIn(f"plugin: {self.version} {self.sha}", text)
        self.assertTrue((self.runtime_dir() / "bin" / "squad-spawn").is_file())

    def test_the_first_prompt_does_not_say_read_process_md(self):
        self.scope()
        self.spawn("dev", "t-dev-sc1", "--prompt", "Task 05 is yours.")
        prompt = self.calls("agent prompt")[0]
        self.assertIn("Task 05 is yours.", prompt)
        self.assertIn("rules are attached", prompt)
        self.assertNotIn("process.md", prompt)

    def test_no_pin_exits_2_before_any_herdr_call_or_worktree(self):
        self.scope(pin="")
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "i", cwd=repo)
        r = self.spawn("dev", "t-dev-sc1", "--repo", str(repo))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("plugin: <version> <sha>", r.stderr)
        self.assertEqual(self.herdr(), "")
        self.assertFalse((self.root / ".worktrees").exists())
        self.assertFalse((self.squad / "scopes" / "sc1" / "labels").exists())

    def test_an_unparseable_pin_exits_2_and_a_missing_runtime_exits_1_naming_the_pin(self):
        self.scope(pin="nonsense")
        self.assertEqual(self.spawn().returncode, 2)
        self.scope(pin=f"{self.version} {'ab' * 8}")
        r = self.spawn()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("ab" * 8, r.stderr)
        self.assertIn("archive", r.stderr)
        self.assertEqual(self.herdr(), "")

    def test_a_compose_failure_exits_2_and_launches_nothing(self):
        self.scope()
        (self.squad / "process.local.md").write_text("## remove NOPE-1 @abcdef12\n\nwhy: x\n", encoding="utf-8")
        r = self.spawn()
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(self.herdr(), "")

    def test_a_squad_with_only_process_local_md_is_found_without_squad(self):
        self.scope()
        env = {k: v for k, v in self.env.items() if k != "SQUAD_DIR"}
        project = self.root
        r = subprocess.run([str(self.plugin / "bin" / "squad-spawn"), "dev", "t-dev-sc1", "--scope", "sc1", "--dry-run"],
                           env=env, cwd=project, text=True, encoding="utf-8", capture_output=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_dry_run_builds_nothing_and_prints_the_flag(self):
        self.scope()
        r = self.spawn("dev", "t-dev-sc1", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--append-system-prompt-file", r.stdout)
        self.assertIn(str(self.runtime_dir()), r.stdout)
        self.assertFalse((self.squad / "_runtime").exists())
        self.assertFalse((self.squad / "scopes" / "sc1" / "roles" / "t-dev-sc1.rules.md").exists())

    def test_a_goal_manager_home_composes_with_the_goal_pin(self):
        g = self.squad / "goals" / "g1"
        (g / "roles").mkdir(parents=True)
        (g / "goal.md").write_text(f"# Goal: g1\n\nplugin: {self.version} {self.sha}\n", encoding="utf-8")
        (g / "roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n", encoding="utf-8")
        r = self.run_bin("squad-spawn", "manager", "t-mgr-g1", "--goal", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = (g / "roles" / "t-mgr-g1.rules.md").read_text(encoding="utf-8")
        self.assertIn("scope: goal g1", text)

    def test_a_scope_inside_a_goal_uses_its_own_pin(self):
        g = self.squad / "goals" / "g1"
        g.mkdir(parents=True)
        (g / "goal.md").write_text(f"# Goal\n\nplugin: {self.version} {self.sha}\n", encoding="utf-8")
        self.scope(goal="g1")
        self.assertEqual(self.spawn().returncode, 0)

    def test_legacy_layout_attaches_plugin_rules_without_runtime_or_path(self):
        (self.squad / "process.local.md").unlink()
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        self.scope(pin="")
        r = self.spawn("dev", "t-dev-sc1", "--prompt", "Read process.md then go.")
        self.assertEqual(r.returncode, 0, r.stderr)
        start = self.calls("agent start")[0]
        rules = self.squad / "scopes" / "sc1" / "roles" / "t-dev-sc1.rules.md"
        self.assertIn(f"--append-system-prompt-file {rules}", start)
        self.assertNotIn("--plugin-dir", start)
        self.assertNotIn("PATH=", self.calls("tab create")[0])
        self.assertEqual(self.calls("agent prompt")[0], "agent prompt t-dev-sc1 Read process.md then go. "
                         f"Your process rules are attached to this session ({rules}); read no other process file.")
        self.assertFalse((self.squad / "_runtime").exists())

    def test_no_marker_files_at_all_is_not_a_squad(self):
        (self.squad / "process.local.md").unlink()
        r = self.spawn()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no squad folder", r.stderr)


class RespawnComposedTest(Base):
    def setUp(self):
        super().setUp()
        self.composed()
        self.scope()
        (self.squad / "scopes" / "sc1" / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| t-qaw-sc1 | QA whitebox | sc1 | x | live | old |\n", encoding="utf-8")
        self.env.update(SCOPE_DIR=str(self.squad / "scopes" / "sc1"), LIVE="t-qaw-sc1")
        self.rules = self.squad / "scopes" / "sc1" / "roles" / "t-qaw-sc1.rules.md"

    def respawn(self):
        return self.run_bin("squad-respawn", "t-qaw-sc1")

    def test_a_size_change_shows_in_the_new_rules_and_the_prompt_points_at_the_notes(self):
        self.assertEqual(self.run_bin("squad-usage", "--squad-dir", str(self.squad / "scopes" / "sc1"),
                                      "--set-session", "t-qaw-sc1", "00000000-0000-0000-0000-000000000001",
                                      "--role", "qa-whitebox", "--scope", "sc1").returncode, 0)
        sc = self.squad / "scopes" / "sc1" / "scope.md"
        sc.write_text(sc.read_text(encoding="utf-8").replace("size: M", "size: S"), encoding="utf-8", newline="\n")
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        small = self.rules.read_text(encoding="utf-8")
        self.assertIn("(size S", small)
        sc.write_text(sc.read_text(encoding="utf-8").replace("size: S", "size: M"), encoding="utf-8", newline="\n")
        self.log.unlink()
        self.assertEqual(self.respawn().returncode, 0)
        big = self.rules.read_text(encoding="utf-8")
        self.assertIn("(size M", big)
        self.assertNotEqual(small, big)
        prompt = [ln for ln in self.herdr().splitlines() if ln.startswith("agent prompt")][0]
        self.assertIn("roles/t-qaw-sc1.notes.md", prompt)
        self.assertNotIn("process.md", prompt)
        self.assertNotIn("squad-process show", prompt)

    def test_no_pin_exits_2_before_the_old_pane_is_touched(self):
        self.scope(pin="")
        r = self.respawn()
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(self.herdr(), "")

    def test_a_missing_runtime_exits_1_before_any_herdr_call(self):
        self.scope(pin=f"{self.version} {'cd' * 8}")
        r = self.respawn()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(self.herdr(), "")


    def test_the_none_layout_is_not_a_squad(self):
        (self.squad / "process.local.md").unlink()
        r = self.respawn()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(self.herdr(), "")

    def test_a_goal_manager_respawns_with_the_goal_pin_and_a_notes_only_prompt(self):
        g = self.squad / "goals" / "g1"
        (g / "roles").mkdir(parents=True)
        (g / "goal.md").write_text(f"# Goal: g1\n\nplugin: {self.version} {self.sha}\n", encoding="utf-8")
        (g / "roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
                                     "| t-mgr-g1 | Manager | | x | live | old |\n", encoding="utf-8")
        env = {k: v for k, v in self.env.items() if k != "SCOPE_DIR"}
        env.update(GOAL_DIR=str(g), LIVE="t-mgr-g1")
        subprocess.run([str(self.plugin / "bin" / "squad-usage"), "--squad-dir", str(g), "--set-session", "t-mgr-g1",
                        "00000000-0000-0000-0000-000000000002", "--role", "manager", "--scope", ""], env=env, check=True)
        r = subprocess.run([str(self.plugin / "bin" / "squad-respawn"), "t-mgr-g1"], env=env, text=True,
                           encoding="utf-8", capture_output=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = (g / "roles" / "t-mgr-g1.rules.md").read_text(encoding="utf-8")
        self.assertIn("scope: goal g1", text)
        self.assertIn("## Index of other rules", text)
        start = [ln for ln in self.herdr().splitlines() if ln.startswith("agent start")][0]
        self.assertIn("--append-system-prompt-file", start)
        prompt = [ln for ln in self.herdr().splitlines() if ln.startswith("agent prompt")][0]
        self.assertIn("goals/g1/roles/t-mgr-g1.notes.md".replace("goals/g1", "$GOAL_DIR"), prompt)
        self.assertNotIn("process.md", prompt)

    def test_check_and_version_json_stay_json_in_a_composed_squad(self):
        self.composed()
        r = subprocess.run([sys.executable, str(BIN / "squad-process"), "check", "--json", "--squad-dir", str(self.squad)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(json.loads(r.stdout)["state"], "composed")


class StartComposedTest(Base):
    def setUp(self):
        super().setUp()
        self.composed()

    def start(self, *args):
        return self.run_bin("squad-start", *args)

    def scope_md(self, name="sc1"):
        return (self.squad / "scopes" / name / "scope.md").read_text(encoding="utf-8")

    def test_a_scope_gets_the_running_plugin_pin_and_a_runtime(self):
        r = self.start("do the thing", "--name", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"\nplugin: {self.version} {self.sha}\n", self.scope_md())
        self.assertTrue(self.runtime_dir().is_dir())

    def test_plugin_pin_file_beats_the_running_plugin(self):
        clone = self.root / "clone"
        shutil.copytree(self.plugin, clone)
        (clone / "later.txt").write_text("x", encoding="utf-8")
        git("add", "-A", cwd=clone)
        git("commit", "-q", "-m", "later", cwd=clone)
        self.assertNotEqual(git("rev-parse", "HEAD", cwd=clone), self.sha)
        (self.squad / "plugin.pin").write_text(f"{self.version} {self.sha}\n", encoding="utf-8")
        r = self.run_bin("squad-start", "do the thing", "--name", "sc1", plugin=clone)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")
        self.assertIn(f"\nplugin: {self.version} {self.sha}\n", self.scope_md())
        self.assertTrue(self.runtime_dir().is_dir())

    def test_an_older_pin_than_the_running_plugin_warns_and_goes_on(self):
        (self.squad / "plugin.pin").write_text(f"0.0.1 {self.sha}\n", encoding="utf-8")
        r = self.start("do the thing", "--name", "sc1")
        self.assertIn("plugin.pin is 0.0.1, older than the installed plugin", r.stderr)
        self.assertEqual(r.returncode, 1)  # the commit holds this version, not 0.0.1: refused, nothing created
        self.assertFalse((self.squad / "scopes" / "sc1").exists())

    def test_an_unparseable_plugin_pin_exits_2(self):
        (self.squad / "plugin.pin").write_text("what\n", encoding="utf-8")
        r = self.start("do the thing", "--name", "sc1")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse((self.squad / "scopes" / "sc1").exists())

    def test_in_goal_copies_the_goals_pin(self):
        g = self.squad / "goals" / "g1"
        g.mkdir()
        (g / "goal.md").write_text(f"# Goal: g1\n\nplugin: {self.version} {self.sha}\n\n## Scopes\n", encoding="utf-8")
        (self.squad / "plugin.pin").write_text("0.0.1 abc1234\n", encoding="utf-8")  # ignored: the goal's pin wins
        r = self.start("a scope", "--in-goal", "g1", "--name", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"\nplugin: {self.version} {self.sha}\n", self.scope_md())
        self.assertNotIn("0.0.1", self.scope_md())

    def test_a_goal_gets_a_pin_line_and_a_dirty_tree_warns(self):
        clone = self.root / "dirty"
        shutil.copytree(self.plugin, clone)
        (clone / "extra.txt").write_text("x", encoding="utf-8")
        r = self.run_bin("squad-start", "goal: big thing", "--name", "g1", plugin=clone)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plugin tree has uncommitted changes, pin uses commit", r.stderr)
        self.assertIn(f"\nplugin: {self.version} {self.sha}\n", (self.squad / "goals" / "g1" / "goal.md").read_text(encoding="utf-8"))
        spawn = [ln for ln in self.herdr().splitlines() if ln.startswith("agent start")]
        self.assertIn("--append-system-prompt-file", spawn[0])

    def test_the_resume_prompt_does_not_send_the_manager_to_process_md(self):
        self.start("a scope", "--name", "sc1")
        self.log.unlink()
        r = self.start("--resume", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        prompt = [ln for ln in self.herdr().splitlines() if ln.startswith("agent prompt")][0]
        self.assertNotIn("process.md", prompt)
        self.assertIn("notes", prompt)

    def test_the_legacy_layout_gets_plugin_rules_but_no_pin_or_runtime(self):
        (self.squad / "process.local.md").unlink()
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        r = self.start("a scope", "--name", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("plugin:", self.scope_md())
        self.assertFalse((self.squad / "_runtime").exists())
        self.assertIn("--append-system-prompt-file", self.herdr())  # ticket 24: legacy rules come from the running plugin

    def test_a_dry_run_creates_nothing_and_names_the_pin(self):
        r = self.start("a scope", "--name", "sc1", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"would pin plugin: {self.version} {self.sha}", r.stdout)
        self.assertFalse((self.squad / "_runtime").exists())
        self.assertFalse((self.squad / "scopes" / "sc1").exists())


class RuntimeIsNotAScopeTest(Base):
    """AC 10: a materialised runtime holds templates/scope.md and goal.md; no scanner may read it as a scope or goal."""

    def test_scanners_read_fixed_paths_only(self):
        self.composed()
        self.scope("sc1")
        rt.materialise(str(self.squad), self.version, self.sha, str(self.plugin))
        self.assertTrue((self.runtime_dir() / "templates" / "scope" / "scope.md").is_file())
        # squad-label: lookup homes
        loader = importlib.machinery.SourceFileLoader("squad_label_mod", str(BIN / "squad-label"))
        spec = importlib.util.spec_from_loader("squad_label_mod", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        old = os.environ.get("SQUAD_DIR")
        os.environ["SQUAD_DIR"] = str(self.squad)
        try:
            os.environ.pop("SCOPE_DIR", None)
            os.environ.pop("GOAL_DIR", None)
            homes = mod.homes_for_lookup()
        finally:
            os.environ.pop("SQUAD_DIR") if old is None else os.environ.update(SQUAD_DIR=old)
        self.assertEqual(homes, [str(self.squad), str(self.squad / "scopes" / "sc1")])
        # squad-report: _runtime is not a scope or goal name
        import squadreport_build as build
        with self.assertRaises(build.Refused):
            build.resolve(self.squad, "_runtime")
        self.assertEqual(build.resolve(self.squad, "sc1")[0], "scope")
        # squad-start's overlap scan
        starter = importlib.machinery.SourceFileLoader("squad_start_mod", str(BIN / "squad-start"))
        sspec = importlib.util.spec_from_loader("squad_start_mod", starter)
        smod = importlib.util.module_from_spec(sspec)
        starter.exec_module(smod)
        self.assertEqual([n for n, _ in smod.open_scope_touches(self.squad)], ["sc1"])

    def test_no_script_walks_the_squad_folder_recursively(self):
        scanners = ("squad-label", "squadlabel.py", "squad-report", "squadreport", "squad-inbox", "squadinbox", "squad-start",
                    "squad-usage", "squad-notify", "squad-log-message", "squad-retire", "squad-close")
        for f in sorted(BIN.iterdir()):
            if f.is_file() and f.suffix != ".pyc" and f.name.startswith(scanners):
                text = f.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"rglob\(|os\.walk\(|glob\([^)]*\*\*", f.name)


if __name__ == "__main__":
    unittest.main()
