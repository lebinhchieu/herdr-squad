"""Ticket ca-repo/02: install.sh links the scripts per file into a temp HOME, keeps state files, deletes leftovers."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CA = ROOT / "tools" / "claude-accounts"
INSTALL = CA / "install.sh"
FILES = ["lib.sh", "usage-popup.sh", "record-usage.sh", "HANDOFF.md"] + [f"bin/{p.name}" for p in (CA / "bin").iterdir()]
LEFTOVERS = ["lib.sh.bak-t6", "HANDOFF.md.new", "HANDOFF.md.bak", "bin/cswitch.orig", "bin/c1.bak-fix-autoswitch"]


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.acct = self.home / ".claude-accounts"
        self.skill = self.home / ".claude" / "skills" / "claude-accounts"

    def run_install(self, *args):
        env = {**os.environ, "HOME": str(self.home)}
        return subprocess.run(["bash", str(INSTALL), *args], env=env, capture_output=True, text=True)

    def seed_live(self):
        (self.acct / "bin").mkdir(parents=True)
        (self.acct / "workspace-default").mkdir()
        (self.acct / "workspace-default" / "w1").write_text("2\n")
        for name, text in (("default", "3\n"), ("usage-1", "{}"), ("cswitch.log", "log\n")):
            (self.acct / name).write_text(text)
        for f in FILES:
            (self.acct / f).write_text("old copy\n")
        for f in LEFTOVERS:
            (self.acct / f).write_text("x")
        (self.acct / "__pycache__").mkdir()
        (self.acct / "__pycache__" / "a.pyc").write_text("x")
        self.skill.mkdir(parents=True)
        for n in ("SKILL.md", "SKILL.md.bak-t6", "SKILL.md.new"):
            (self.skill / n).write_text("old")

    def test_fresh_home_links_every_script_and_the_skill_dir(self):
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.acct.is_symlink())
        self.assertFalse((self.acct / "bin").is_symlink())
        for f in FILES:
            self.assertTrue((self.acct / f).is_symlink(), f)
            self.assertEqual((self.acct / f).resolve(), (CA / f).resolve())
        self.assertTrue(self.skill.is_symlink())
        self.assertEqual(self.skill.resolve(), (CA / "skill").resolve())
        self.assertTrue((self.skill / "SKILL.md").is_file())

    def test_live_home_keeps_state_and_loses_leftovers(self):
        self.seed_live()
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.acct / "default").read_text(), "3\n")
        self.assertEqual((self.acct / "usage-1").read_text(), "{}")
        self.assertEqual((self.acct / "cswitch.log").read_text(), "log\n")
        self.assertEqual((self.acct / "workspace-default" / "w1").read_text(), "2\n")
        for f in FILES:
            self.assertTrue((self.acct / f).is_symlink(), f)
        for f in LEFTOVERS:
            self.assertFalse((self.acct / f).exists(), f)
        self.assertFalse((self.acct / "__pycache__").exists())
        self.assertTrue(self.skill.is_symlink())
        self.assertEqual(sorted(p.name for p in self.skill.iterdir()), ["SKILL.md"])

    def test_second_run_changes_nothing(self):
        self.seed_live()
        self.run_install()
        before = sorted((str(p), os.readlink(p) if p.is_symlink() else "") for p in self.home.rglob("*"))
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        after = sorted((str(p), os.readlink(p) if p.is_symlink() else "") for p in self.home.rglob("*"))
        self.assertEqual(before, after)
        self.assertNotIn("ln -sfn", r.stdout)

    def test_dry_run_prints_and_changes_nothing(self):
        self.seed_live()
        before = sorted((str(p), p.is_symlink(), p.read_text() if p.is_file() else "") for p in self.home.rglob("*"))
        r = self.run_install("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would:", r.stdout)
        after = sorted((str(p), p.is_symlink(), p.read_text() if p.is_file() else "") for p in self.home.rglob("*"))
        self.assertEqual(before, after)

    def test_dry_run_on_empty_home_creates_nothing(self):
        r = self.run_install("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unknown_argument_is_refused(self):
        r = self.run_install("--bogus")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_skill_dir_with_other_files_is_kept(self):
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("old")
        (self.skill / "mine.txt").write_text("keep")
        r = self.run_install()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.skill / "mine.txt").read_text(), "keep")

    def test_launcher_runs_through_the_links(self):
        self.run_install()
        r = subprocess.run(["bash", "-c", '. "$HOME/.claude-accounts/lib.sh"; default_account'],
                           env={**os.environ, "HOME": str(self.home), "HERDR_ENV": ""}, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "1")


if __name__ == "__main__":
    unittest.main()
