"""Ticket 08: effective settings = template + squad overlay (bin/squadsettings.py) and the squad-spawn wiring."""
import json
import os
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

    def test_placeholder_dropped_without_code_paths(self):
        self.local("qa-blackbox", {})
        self.assertNotIn("CODE_PATHS_SET_BY_SQUAD_INIT", json.dumps(self.eff("qa-blackbox")))

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
        return subprocess.run([str(SPAWN), role, "x", "--dry-run"], env=self.env, text=True,
                              encoding="utf-8", capture_output=True, timeout=10)

    def test_overlay_passes_the_effective_file_and_model_from_the_local_file(self):
        self.local("dev", {"model": "haiku"})
        r = self.spawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"--settings {self.squad}/roles/x.settings.json", r.stdout)
        self.assertIn("--model haiku --effort", r.stdout)
        self.assertEqual(r.stderr, "")

    def test_overlay_missing_template_exits_1(self):
        self.local("dev", {})
        # a plugin root whose template for the role is gone
        root = self.dir / "p"
        (root / "templates/squad/settings").mkdir(parents=True)
        r = subprocess.run([sys.executable, str(ROOT / "bin/squadsettings.py"), "effective", "--role", "dev",
                            "--squad-dir", str(self.squad), "--template-root", str(root)],
                           text=True, capture_output=True)
        self.assertEqual(r.returncode, 1)

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
        self.assertEqual(r.stderr, "")

    def test_local_file_wins_over_an_old_full_file(self):
        (self.squad / "settings" / "dev.json").write_text('{"model": "haiku"}', encoding="utf-8")
        self.local("dev", {"model": "opus"})
        r = self.spawn()
        self.assertIn("roles/x.settings.json", r.stdout)
        self.assertIn("--model opus", r.stdout)


if __name__ == "__main__":
    unittest.main()
