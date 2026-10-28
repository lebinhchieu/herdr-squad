"""squad-process scaffold: a new composed squad; temp folders only."""
import os
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


def run(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
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
    def test_show_is_retired_and_apply_needs_legacy(self):
        self.assertNotEqual(run("show", "dev").returncode, 0)
        sq = self.root / ".claude" / "squads" / "x"
        sq.mkdir(parents=True)
        r = run("apply", "--file", str(self.root / "f.md"), "--squad-dir", str(sq))
        self.assertEqual(r.returncode, 2)
        self.assertIn("--legacy", r.stderr)

    def test_no_command_card_or_prompt_calls_show(self):
        hits = []
        for d in ("agents", "skills", "bin", "templates", "hooks"):
            for p in (ROOT / d).rglob("*"):
                if p.is_file() and p.suffix in ("", ".md", ".py", ".json", ".sh") and "history" not in p.parts:
                    t = p.read_text(encoding="utf-8", errors="ignore")
                    if "squad-process show" in t or "ROLE_SECTIONS" in t:
                        hits.append(str(p.relative_to(ROOT)))
        self.assertEqual(hits, [])

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
