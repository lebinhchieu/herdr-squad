"""Ticket ca-repo/02: install.sh links the scripts per file into a temp HOME, keeps state files, deletes leftovers."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CA = ROOT / "tools" / "claude-accounts"
INSTALL = CA / "install.sh"
FILES = ["lib.sh", "usage-popup.sh", "record-usage.sh", "HANDOFF.md"] + [f"bin/{p.name}" for p in (CA / "bin").iterdir()]
LEFTOVERS = ["lib.sh.bak-t6", "HANDOFF.md.new", "bin/cswitch.orig", "bin/c1.bak-fix-autoswitch"]


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.acct = self.home / ".claude-accounts"
        self.skill = self.home / ".claude" / "skills" / "claude-accounts"

    def run_install(self, *args, worktree=True):
        if worktree:
            args = ("--allow-worktree", *args)
        env = {**os.environ, "HOME": str(self.home)}
        return subprocess.run(["bash", str(INSTALL), *args], env=env, capture_output=True, text=True)

    def seed_live(self):
        (self.acct / "bin").mkdir(parents=True)
        (self.acct / "workspace-default").mkdir()
        (self.acct / "workspace-default" / "w1").write_text("2\n")
        for name, text in (("default", "3\n"), ("usage-1", "{}"), ("cswitch.log", "log\n")):
            (self.acct / name).write_text(text)
        for f in FILES:
            (self.acct / f).write_bytes((CA / f).read_bytes())
        for f in LEFTOVERS:
            (self.acct / f).write_text("x")
        (self.acct / "__pycache__").mkdir()
        (self.acct / "__pycache__" / "a.pyc").write_text("x")
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_bytes((CA / "skill" / "SKILL.md").read_bytes())
        for n in ("SKILL.md.bak-t6", "SKILL.md.new"):
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
        self.assertNotIn("link:", r.stdout.replace("ok:", ""))

    def test_dry_run_prints_and_changes_nothing(self):
        self.seed_live()
        before = sorted((str(p), p.is_symlink(), p.read_text() if p.is_file() else "") for p in self.home.rglob("*"))
        r = self.run_install("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would link:", r.stdout)
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
        (self.skill / "SKILL.md").write_bytes((CA / "skill" / "SKILL.md").read_bytes())
        (self.skill / "mine.txt").write_text("keep")
        (self.skill / "SKILL.md.new").write_text("leftover")
        r = self.run_install()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.skill / "mine.txt").read_text(), "keep")
        self.assertTrue((self.skill / "SKILL.md").is_file())
        self.assertTrue((self.skill / "SKILL.md.new").exists())
        self.assertFalse((self.acct / "lib.sh").exists())

    def test_differing_real_file_stops_everything_until_force(self):
        self.seed_live()
        (self.acct / "bin" / "c1").write_text("my edit\n")
        snap = sorted((str(p), p.is_symlink(), p.read_text() if p.is_file() else "") for p in self.home.rglob("*"))
        for args in ((), ("--dry-run",)):
            r = self.run_install(*args)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("diff", r.stderr)
            self.assertIn(str(self.acct / "bin" / "c1"), r.stderr)
        r = self.run_install()
        self.assertEqual(sorted((str(p), p.is_symlink(), p.read_text() if p.is_file() else "") for p in self.home.rglob("*")), snap)
        r = self.run_install("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.acct / "bin" / "c1").is_symlink())

    def test_identical_real_file_and_stray_link_are_replaced_without_force(self):
        self.seed_live()
        (self.acct / "lib.sh").write_text((CA / "lib.sh").read_text())
        (self.acct / "bin" / "c2").unlink()
        (self.acct / "bin" / "c2").symlink_to("/nowhere")
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.acct / "lib.sh").resolve(), (CA / "lib.sh").resolve())
        self.assertEqual((self.acct / "bin" / "c2").resolve(), (CA / "bin" / "c2").resolve())

    def test_differing_skill_md_stops_the_install(self):
        self.seed_live()
        (self.skill / "SKILL.md").write_text("my edit")
        r = self.run_install()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.skill / "SKILL.md").read_text(), "my edit")
        self.assertTrue((self.skill / "SKILL.md.new").exists())
        self.assertFalse(self.skill.is_symlink())

    def test_git_dir_and_extra_files_are_kept_and_named(self):
        self.seed_live()
        (self.acct / ".git").mkdir()
        (self.acct / ".git" / "x.bak").write_text("h")
        (self.acct / "mine.txt").write_text("m")
        (self.acct / "bin" / "mytool").write_text("m")
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.acct / ".git" / "x.bak").exists())
        self.assertTrue((self.acct / "mine.txt").exists())
        self.assertIn("unexpected: " + str(self.acct / "mine.txt"), r.stdout)
        self.assertIn("unexpected: " + str(self.acct / "bin" / "mytool"), r.stdout)
        self.assertNotIn("unexpected: " + str(self.acct / "default"), r.stdout)
        self.assertTrue(r.stdout.strip().splitlines()[-1].startswith(str(self.acct / ".git")))
        self.assertIn("left alone", r.stdout.strip().splitlines()[-1])

    def test_linked_worktree_is_refused_without_the_flag(self):
        main = self.home / "main"
        shutil.copytree(CA, main / "tools" / "claude-accounts")
        g = lambda *a, cwd=main: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                                                env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        g("init", "-q"); g("add", "-A"); g("commit", "-qm", "x"); g("worktree", "add", "-q", str(self.home / "wt"))
        env = {**os.environ, "HOME": str(self.home)}
        for src, rc in ((self.home / "wt", 1), (main, 0)):
            r = subprocess.run(["bash", str(src / "tools/claude-accounts/install.sh")], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, rc, r.stderr)
            self.assertIn(f"installing from: {(src / 'tools/claude-accounts').resolve()}", r.stdout)
            if rc:
                self.assertIn("worktree", r.stderr)
                self.assertFalse(self.acct.exists())
        r = self.run_install()
        self.assertIn("warning", r.stdout)

    def test_empty_or_non_directory_home_is_refused(self):
        for home in ("", str(self.home / "nope")):
            r = subprocess.run(["bash", str(INSTALL), "--allow-worktree"], env={**os.environ, "HOME": home}, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_force_moves_the_original_to_install_backup(self):
        self.seed_live()
        (self.acct / "bin" / "c1").write_text("my edit\n")
        r = self.run_install("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.acct / ".install-backup" / "bin" / "c1").read_text(), "my edit\n")
        self.assertTrue((self.acct / "bin" / "c1").is_symlink())

    def test_force_backs_up_a_differing_skill_dir(self):
        self.seed_live()
        (self.skill / "SKILL.md").write_text("my edit")
        r = self.run_install("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.acct / ".install-backup" / "skill" / "SKILL.md").read_text(), "my edit")
        self.assertTrue(self.skill.is_symlink())

    def test_second_run_keeps_every_link_mtime_and_leaves_no_temp(self):
        self.seed_live()
        self.run_install()
        links = [p for p in self.home.rglob("*") if p.is_symlink()]
        before = {p: p.lstat().st_mtime_ns for p in links}
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(before, {p: p.lstat().st_mtime_ns for p in links})
        self.assertEqual([p for p in self.home.rglob("*.install-tmp")], [])

    def test_only_the_pos_leftover_names_are_deleted(self):
        self.seed_live()
        (self.acct / "notes.new").write_text("po")
        (self.acct / "usage-1.bak").write_text("po")
        (self.acct / "workspace-default" / "x.new").write_text("po")
        (self.acct / "__pycache__" / "mine.txt").write_text("po")
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        for f, shown in (("notes.new", "notes.new"), ("usage-1.bak", "usage-1.bak"), ("workspace-default/x.new", "workspace-default/x.new"),
                         ("__pycache__/mine.txt", "__pycache__")):
            self.assertTrue((self.acct / f).exists(), f)
            self.assertIn("unexpected: " + str(self.acct / shown), r.stdout)
        self.assertFalse((self.acct / "lib.sh.bak-t6").exists())

    def test_pyc_only_pycache_is_deleted(self):
        self.seed_live()
        (self.acct / "bin" / "__pycache__").mkdir()
        (self.acct / "bin" / "__pycache__" / "a.pyc").write_text("x")
        self.assertEqual(self.run_install().returncode, 0)
        self.assertFalse((self.acct / "bin" / "__pycache__").exists())
        self.assertFalse((self.acct / "__pycache__").exists())

    def test_no_leftover_is_deleted_on_a_refused_run(self):
        self.seed_live()
        (self.acct / "bin" / "c1").write_text("my edit\n")
        self.run_install()
        self.assertTrue((self.acct / "lib.sh.bak-t6").exists())

    def test_unlink_restores_regular_copies_and_is_idempotent(self):
        self.seed_live()
        self.run_install()
        r = self.run_install("--dry-run", "--unlink")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.acct / "lib.sh").is_symlink())
        r = self.run_install("--unlink")
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in FILES:
            p = self.acct / f
            self.assertFalse(p.is_symlink(), f)
            self.assertEqual(p.read_bytes(), (CA / f).read_bytes())
            self.assertEqual(p.stat().st_mode & 0o777, (CA / f).stat().st_mode & 0o777, f)
        self.assertTrue(self.skill.is_dir() and not self.skill.is_symlink())
        self.assertEqual((self.skill / "SKILL.md").read_bytes(), (CA / "skill" / "SKILL.md").read_bytes())
        self.assertEqual((self.acct / "default").read_text(), "3\n")
        self.assertEqual(self.run_install("--unlink").returncode, 0)

    def test_gitignore_names_the_state_files(self):
        for name in ("default", "workspace-default/w1", "usage-1", "cswitch.log", ".install-backup/c1", "x.bak-1", "x.new", "x.orig"):
            r = subprocess.run(["git", "check-ignore", "-q", "--no-index", "tools/claude-accounts/" + name], cwd=ROOT)
            self.assertEqual(r.returncode, 0, name)
        r = subprocess.run(["git", "check-ignore", "-q", "--no-index", "tools/claude-accounts/usage-popup.sh"], cwd=ROOT)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
