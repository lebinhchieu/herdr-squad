"""Ticket 08: effective settings = template + squad overlay (bin/squadsettings.py) and the squad-spawn wiring."""
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadsettings as ss  # noqa: E402

SPAWN = ROOT / "bin" / "squad-spawn"


class MergeTest(unittest.TestCase):
    def test_scalar_local_wins(self):
        self.assertEqual(ss.merge({"model": "sonnet", "x": 1}, {"model": "opus"}), {"model": "opus", "x": 1})

    def test_allow_union_keeps_order_and_drops_duplicates(self):
        t = {"permissions": {"allow": ["a", "b"]}}
        l = {"permissions": {"allow": ["c", "a"]}}
        self.assertEqual(ss.merge(t, l)["permissions"]["allow"], ["a", "b", "c"])

    def test_deny_union(self):
        t = {"permissions": {"deny": ["x"]}}
        l = {"permissions": {"deny": ["y", "x"]}}
        self.assertEqual(ss.merge(t, l)["permissions"]["deny"], ["x", "y"])

    def test_nested_objects_merge_recursively(self):
        t = {"env": {"A": "1", "B": "2"}, "permissions": {"allow": ["a"]}}
        l = {"env": {"B": "3", "C": "4"}}
        r = ss.merge(t, l)
        self.assertEqual(r["env"], {"A": "1", "B": "3", "C": "4"})
        self.assertEqual(r["permissions"]["allow"], ["a"])

    def test_inputs_are_not_changed(self):
        t = {"permissions": {"allow": ["a"]}}
        ss.merge(t, {"permissions": {"allow": ["b"]}})
        self.assertEqual(t, {"permissions": {"allow": ["a"]}})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = Path(self.tmp.name) / "sq"
        (self.squad / "settings").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def local(self, role, data):
        (self.squad / "settings" / f"{role}.local.json").write_text(json.dumps(data), encoding="utf-8")


class EffectiveTest(Base):
    def eff(self, role):
        return ss.effective(role, str(self.squad), str(ROOT))

    def test_no_local_file_means_no_overlay(self):
        self.assertIsNone(self.eff("dev"))

    def test_template_missing_exits_1(self):
        self.local("dev", {})
        with self.assertRaises(ss.SettingsError) as c:
            ss.effective("dev", str(self.squad), str(self.squad))
        self.assertEqual(c.exception.code, 1)

    def test_bad_local_json_exits_2(self):
        (self.squad / "settings" / "dev.local.json").write_text("{nope", encoding="utf-8")
        with self.assertRaises(ss.SettingsError) as c:
            self.eff("dev")
        self.assertEqual(c.exception.code, 2)

    def test_team_lead_empty_local_has_spawn_dev_and_herdr_entries(self):
        # v4 gap in SETTINGS-NOTES.md: a squad file written before T5 lacked these; the overlay cannot lose them.
        self.local("team-lead", {})
        allow = self.eff("team-lead")["permissions"]["allow"]
        for e in ("Bash(squad-spawn dev:*)", "Bash(squad-retire:*)", "Bash(herdr agent list:*)",
                  "Bash(herdr agent get:*)", "Bash(herdr agent read:*)"):
            self.assertIn(e, allow)

    def test_qa_blackbox_denies_the_local_code_paths_not_the_placeholder(self):
        self.local("qa-blackbox", {"codePaths": ["/home/me/proj/bin", "/home/me/proj/tests/"]})
        e = self.eff("qa-blackbox")
        deny = e["permissions"]["deny"]
        self.assertIn("Read(//home/me/proj/bin/**)", deny)
        self.assertIn("Read(//home/me/proj/tests/**)", deny)
        self.assertNotIn("codePaths", e)
        self.assertNotIn("CODE_PATHS_SET_BY_SQUAD_INIT", json.dumps(e))
        self.assertIn("Bash(git push:*)", deny)  # template deny kept

    def test_placeholder_without_code_paths_fails_closed(self):
        for data in ({}, {"codePaths": []}):
            with self.subTest(data=data):
                self.local("qa-blackbox", data)
                with self.assertRaises(ss.SettingsError) as c:
                    self.eff("qa-blackbox")
                self.assertEqual(c.exception.code, 2)

    def test_qa_blackbox_also_denies_the_project_worktrees(self):
        self.local("qa-blackbox", {"codePaths": ["/p/bin"]})
        deny = ss.effective("qa-blackbox", str(self.squad), str(ROOT), "/p")["permissions"]["deny"]
        self.assertIn("Read(//p/.worktrees/**)", deny)

    def test_ask_unions_and_other_arrays_are_replaced(self):
        r = ss.merge({"permissions": {"ask": ["a"]}, "l": [1, 2]}, {"permissions": {"ask": ["b"]}, "l": [3]})
        self.assertEqual(r["permissions"]["ask"], ["a", "b"])
        self.assertEqual(r["l"], [3])

    def test_relative_code_path_refused(self):
        self.local("qa-blackbox", {"codePaths": ["bin"]})
        with self.assertRaises(ss.SettingsError):
            self.eff("qa-blackbox")


class SpawnTest(Base):
    def setUp(self):
        super().setUp()
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad))
        self.dir = Path(self.tmp.name)

    def spawn(self, role="dev"):
        return subprocess.run([str(SPAWN), role, "x", "--dry-run", "--prompt", "hello"], env=self.env, text=True,
                              encoding="utf-8", capture_output=True, timeout=10)

    def test_overlay_passes_the_effective_file_and_model_from_the_local_file(self):
        self.local("dev", {"model": "haiku"})
        r = self.spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--settings {self.squad}/roles/x.settings.json", r.stdout)
        self.assertIn("--model haiku --effort", r.stdout)
        self.assertNotIn("settings", r.stderr)  # the legacy-squad notice (ticket 24) is not a settings warning

    def test_overlay_missing_template_exits_1(self):
        self.local("dev", {})
        # a plugin root whose template for the role is gone
        root = self.dir / "p"
        (root / "templates/squad/settings").mkdir(parents=True)
        r = subprocess.run([sys.executable, str(ROOT / "bin/squadsettings.py"), "effective", "--role", "dev",
                            "--squad-dir", str(self.squad), "--template-root", str(root)],
                           text=True, capture_output=True)
        self.assertEqual(r.returncode, 1)

    def test_dry_run_qa_blackbox_without_code_paths_is_refused(self):
        self.local("qa-blackbox", {})
        r = self.spawn("qa-blackbox")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("would run: herdr agent start", r.stdout)

    def test_old_layout_keeps_the_file_and_warns_once(self):
        (self.squad / "settings" / "dev.json").write_text(json.dumps({"model": "haiku", "effortLevel": "low"}), encoding="utf-8")
        r = self.spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--settings {self.squad}/settings/dev.json", r.stdout)
        self.assertEqual(r.stderr.count("warning:"), 1)
        self.assertIn("09", r.stderr)

    def test_no_squad_files_uses_the_template_without_warning(self):
        r = self.spawn()
        self.assertIn(str(ROOT / "templates/squad/settings/dev.json"), r.stdout)
        self.assertNotIn("settings", r.stderr)  # the legacy-squad notice (ticket 24) is not a settings warning

    def test_local_file_wins_over_an_old_full_file(self):
        (self.squad / "settings" / "dev.json").write_text('{"model": "haiku"}', encoding="utf-8")
        self.local("dev", {"model": "opus"})
        r = self.spawn()
        self.assertIn("roles/x.settings.json", r.stdout)
        self.assertIn("--model opus", r.stdout)
        self.assertEqual(r.stderr.count("warning:"), 1)
        self.assertIn("ignored", r.stderr)


FAKE_HERDR = """#!/usr/bin/env bash
[[ "$1 $2" == "agent get" ]] && exit 1
[[ $1 == tab ]] && echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


class ComposedSpawnTest(Base):
    """A composed squad: the pinned runtime's template is the one merged, dry-run or not."""
    VERSION = "0.6.0"  # the copy of the running plugin below stands for a release with the team language (no hand-off)
    SHA = "a" * 40

    def setUp(self):
        super().setUp()
        self.proj = Path(self.tmp.name) / "proj"
        self.squad = self.proj / ".claude" / "squads" / "t"
        (self.squad / "settings").mkdir(parents=True)
        (self.squad / "scopes/sc1").mkdir(parents=True)
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        (self.squad / "scopes/sc1/scope.md").write_text(f"# Scope\n\nteam: ba\nplugin: {self.VERSION} {self.SHA}\n", encoding="utf-8")
        rt = self.squad / "_runtime" / f"{self.VERSION}-{self.SHA[:12]}"
        shutil.copytree(ROOT, rt, ignore=shutil.ignore_patterns(".git", ".worktrees", ".scratch", "tests", "__pycache__"))
        pj = rt / ".claude-plugin" / "plugin.json"
        pj.write_text(re.sub(r'("version"\s*:\s*)"[^"]*"', rf'\1"{self.VERSION}"', pj.read_text(encoding="utf-8")), encoding="utf-8")
        d = json.loads((rt / "templates/squad/settings/dev.json").read_text(encoding="utf-8"))
        d["permissions"]["allow"].append("Bash(pinned-only:*)")
        (rt / "templates/squad/settings/dev.json").write_text(json.dumps(d), encoding="utf-8")
        self.local("dev", {"model": "haiku", "permissions": {"allow": ["Bash(mine:*)"]}})
        (self.squad / "scopes/sc1/roster.md").write_text("| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n", encoding="utf-8")
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        (self.bin / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (self.bin / "herdr").chmod(0o755)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}")

    def run_spawn(self, *args):
        return subprocess.run([str(SPAWN), "dev", "x", "--scope", "sc1", *args], env=self.env, text=True,
                              encoding="utf-8", capture_output=True, timeout=30)

    def test_dry_run_exits_0_prints_the_effective_path_and_writes_nothing(self):
        # the pinned runtime is not materialised in dry mode: it still previews (finding 1)
        shutil.rmtree(self.squad / "_runtime")
        r = self.run_spawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--settings {self.squad / 'scopes/sc1'}/roles/x.settings.json", r.stdout)
        self.assertIn("--model haiku", r.stdout)
        self.assertFalse((self.squad / "scopes/sc1/roles/x.settings.json").exists())

    def test_real_spawn_writes_the_effective_file_from_the_pinned_template(self):
        r = self.run_spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        f = self.squad / "scopes/sc1/roles/x.settings.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual(d["model"], "haiku")
        self.assertIn("Bash(pinned-only:*)", d["permissions"]["allow"])  # the pinned template, not the running plugin's
        self.assertIn("Bash(mine:*)", d["permissions"]["allow"])
        self.assertNotIn("CODE_PATHS_SET_BY_SQUAD_INIT", f.read_text(encoding="utf-8"))
        self.assertFalse(f.with_name(f.name + ".tmp").exists())

    def test_a_moved_pin_reaches_the_next_spawn_without_migration(self):
        # B08-6: a template entry added after the first pin shows up once the pin moves (a respawn re-runs spawn).
        sha2 = "b" * 40
        rt1 = self.squad / "_runtime" / f"{self.VERSION}-{self.SHA[:12]}"
        rt2 = self.squad / "_runtime" / f"{self.VERSION}-{sha2[:12]}"
        shutil.copytree(rt1, rt2)
        f = rt2 / "templates/squad/settings/dev.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        d["permissions"]["allow"].append("Bash(added-later:*)")
        f.write_text(json.dumps(d), encoding="utf-8")
        out = self.squad / "scopes/sc1/roles/x.settings.json"
        self.assertEqual(self.run_spawn().returncode, 0)
        self.assertNotIn("added-later", out.read_text(encoding="utf-8"))
        sc = self.squad / "scopes/sc1/scope.md"
        sc.write_text(sc.read_text(encoding="utf-8").replace(self.SHA, sha2), encoding="utf-8")
        self.assertEqual(self.run_spawn().returncode, 0)
        self.assertIn("Bash(added-later:*)", out.read_text(encoding="utf-8"))

    def test_no_local_file_still_uses_the_pinned_template(self):
        # QA blackbox 08 finding: model/effort and --settings came from the running plugin's template.
        rt = self.squad / "_runtime" / f"{self.VERSION}-{self.SHA[:12]}"
        f = rt / "templates/squad/settings/ba.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        d["model"] = "pinnedmodel"
        f.write_text(json.dumps(d), encoding="utf-8")
        r = subprocess.run([str(SPAWN), "ba", "x", "--scope", "sc1", "--dry-run"], env=self.env, text=True,
                           encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--settings {f}", r.stdout)
        self.assertIn("--model pinnedmodel", r.stdout)

    def test_missing_pinned_template_exits_1_naming_the_path(self):
        rt = self.squad / "_runtime" / f"{self.VERSION}-{self.SHA[:12]}"
        (rt / "templates/squad/settings/dev.json").unlink()
        r = self.run_spawn()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no settings template for dev at", r.stderr)


if __name__ == "__main__":
    unittest.main()

