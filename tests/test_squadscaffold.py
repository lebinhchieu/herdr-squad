"""squad-process scaffold: a new composed squad; temp folders only."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadsettings as ss  # noqa: E402

PIN = "0.7.0 abcdef123456"


def run(*args, cwd=None, extra_env=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    env.update(extra_env or {})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(BIN / "squad-process"), *args], capture_output=True,
                          encoding="utf-8", env=env, cwd=cwd)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)


class Scaffold(Base):
    """AC 4: a new squad has no process.md and lints."""

    def test_scaffold_from_a_non_git_plugin_root_pins_from_installed_plugins(self):
        plugin = self.root / "cache" / "squad" / "9.9.9"
        shutil.copytree(ROOT, plugin, ignore=shutil.ignore_patterns(".git", ".worktrees", ".scratch", ".claude", "tests",
                                                                   "__pycache__"))
        version = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        listing = self.root / "installed_plugins.json"
        sha = "c" * 40
        entry = {"squad@market": [{"scope": "user", "installPath": str(plugin), "version": version, "gitCommitSha": sha}]}
        listing.write_text(json.dumps({"version": 2, "plugins": entry}), encoding="utf-8")
        env = {"SQUAD_INSTALLED_PLUGINS": str(listing)}
        sq = self.root / ".claude" / "squads" / "new"
        r = run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(plugin), extra_env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((sq / "plugin.pin").read_text(encoding="utf-8").strip(), f"{version} {sha}")
        listing.write_text(json.dumps({"version": 2, "plugins": {}}), encoding="utf-8")
        r = run("scaffold", "--squad-dir", str(self.root / "other"), "--plugin-root", str(plugin), extra_env=env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--new-pin", r.stderr + r.stdout)

    def test_scaffold_creates_the_composed_layout_and_lints(self):
        sq = self.root / ".claude" / "squads" / "new"
        r = run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((sq / "process.md").exists())
        for f in ("process.local.md", "plugin.pin", "project.md"):
            self.assertTrue((sq / f).is_file(), f)
        self.assertEqual(len(list((sq / "settings").glob("*.local.json"))), 10)
        self.assertEqual(list((sq / "settings").glob("*.json")), list((sq / "settings").glob("*.local.json")))
        self.assertEqual(json.loads((sq / "settings/qa-blackbox.local.json").read_text()), {})
        self.assertEqual(json.loads((sq / "settings/dev.local.json").read_text()), {})
        self.assertEqual(rt.mode(str(sq)), "composed")
        lint = run("lint", "--squad-dir", str(sq), "--plugin-root", str(ROOT))
        self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
        self.assertTrue((sq / "scopes").is_dir() and (sq / "goals").is_dir())

    def test_scaffolded_qa_blackbox_settings_resolve_without_code_paths(self):
        sq = self.root / ".claude" / "squads" / "new"
        run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN)
        eff = ss.effective("qa-blackbox", str(sq), str(ROOT))
        self.assertFalse([e for e in eff["permissions"]["deny"] if e.startswith("Read(")])

    def test_scaffold_never_overwrites_and_refuses_a_legacy_squad(self):
        sq = self.root / ".claude" / "squads" / "new"
        run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN)
        (sq / "process.local.md").write_text("# mine\n", encoding="utf-8")
        (sq / "project.md").write_text("# mine\n", encoding="utf-8")
        r = run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", "0.8.0 1111111")
        self.assertEqual(r.returncode, 0)
        self.assertEqual((sq / "process.local.md").read_text(), "# mine\n")
        self.assertEqual((sq / "plugin.pin").read_text().strip(), PIN)
        old = self.root / ".claude" / "squads" / "old"
        old.mkdir(parents=True)
        (old / "process.md").write_text("# Process\n", encoding="utf-8")
        self.assertEqual(run("scaffold", "--squad-dir", str(old), "--plugin-root", str(ROOT), "--new-pin", PIN).returncode, 2)


class Retirement(Base):

    def test_the_live_squad_overlay_fixture_lints_and_classifies(self):
        import squadupgrade as su
        path = ROOT / "tests/fixtures/upgrade/live-squad.local.md"
        problems = []
        ops = sr.parse_overlay(path.read_text(), path.name, problems)
        self.assertEqual(problems, [])
        new, tombs = su.load_plugin(str(ROOT))
        self.assertEqual([i.op.id for i in su.classify(None, new, tombs, ops).unhandled], [])
        self.assertEqual(sr._lint_ops(ops, new), [])


if __name__ == "__main__":
    unittest.main()
