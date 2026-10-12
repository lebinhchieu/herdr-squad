"""squad-close: retire the squad's agents, remove merged worktrees, archive the folder, report branches."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get") [[ " ${DEAD:-} " == *" $3 "* ]] && { echo '{"error":{"code":"agent_not_found"}}'; exit 1; }
               echo "{\\"result\\":{\\"agent\\":{\\"tab_id\\":\\"t-$3\\"}}}" ;;
esac
exit 0
"""
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}).stdout


class CloseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git("init", "-q", "-b", "main", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=self.root)
        self.squad = self.root / ".claude" / "squads" / "t"
        (self.squad / "evidence").mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        (self.squad / "evidence" / "proof.md").write_text("kept")
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| manager-t | manager |  |  | live | s0 |\n| t-ba-x | ba | x | biz | live | s1 |\n"
            "| t-dev-x-1 | dev | x | task 1 | live | s2 |\n| t-dev-x-2 | dev | x | task 2 | dead | s3 |\n")
        self.wts = {}
        for n, mode in (("t-dev-x-1", "merged"), ("t-dev-x-2", "unmerged"), ("t-dev-x-3", "dirty")):
            wt = self.root / ".worktrees" / "t" / n
            git("worktree", "add", "-q", str(wt), "-b", f"squad/t/{n}", cwd=self.root)
            if mode == "unmerged":
                git("commit", "-q", "--allow-empty", "-m", "work", cwd=wt)
            if mode == "dirty":
                (wt / "wip.txt").write_text("uncommitted")
            self.wts[n] = wt
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD")}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        DEAD="t-dev-x-2", PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def close(self, *args):
        return subprocess.run([str(BIN / "squad-close"), "t", *args], env=self.env, cwd=self.root,
                              text=True, capture_output=True, timeout=30)

    def test_closes_squad_and_reports_each_branch(self):
        r = self.close()
        self.assertEqual(r.returncode, 0, r.stderr)

        self.assertFalse(self.squad.exists())
        self.assertEqual((self.root / ".claude" / "squads" / "_done" / "t" / "evidence" / "proof.md").read_text(), "kept")

        self.assertFalse(self.wts["t-dev-x-1"].exists())      # merged and clean: removed
        self.assertTrue(self.wts["t-dev-x-2"].exists())       # unmerged: kept
        self.assertTrue(self.wts["t-dev-x-3"].exists())       # merged but uncommitted work: kept
        self.assertIn("squad/t/t-dev-x-1: merged into main, worktree removed", r.stdout)
        self.assertIn("squad/t/t-dev-x-2: NOT merged into main, kept", r.stdout)
        self.assertIn("squad/t/t-dev-x-3: merged into main, kept (uncommitted changes)", r.stdout)
        self.assertIn("squad/t/t-dev-x-1", git("branch", "--list", "squad/t/*", cwd=self.root))  # branches are never deleted

        log = self.log.read_text().splitlines()
        closed = [l for l in log if l.startswith("tab close")]
        self.assertEqual(closed, ["tab close t-t-ba-x", "tab close t-t-dev-x-1", "tab close t-manager-t"])  # dead agent skipped, Manager last
        self.assertEqual(log[-1], "tab close t-manager-t")
        self.assertFalse(any(l.startswith("agent prompt") for l in log))  # nothing to save for a closed goal

    def _add_scope_y_dev(self):
        with (self.squad / "roster.md").open("a") as f:
            f.write("| t-dev-y-1 | dev | y | task 9 | live | s9 |\n")
        wt = self.root / ".worktrees" / "t" / "t-dev-y-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/t/t-dev-y-1", cwd=self.root)
        return wt

    def test_scope_mode_closes_only_that_scopes_agents_and_keeps_the_squad(self):
        y_wt = self._add_scope_y_dev()
        r = self.close("--scope", "x")
        self.assertEqual(r.returncode, 0, r.stderr)

        self.assertTrue(self.squad.exists())                   # folder stays, Manager keeps running
        self.assertFalse(self.wts["t-dev-x-1"].exists())       # merged and clean: removed
        self.assertTrue(self.wts["t-dev-x-2"].exists())        # unmerged: kept
        self.assertTrue(y_wt.exists())                         # other scope untouched
        self.assertNotIn("t-dev-y-1", r.stdout)

        closed = [l for l in self.log.read_text().splitlines() if l.startswith("tab close")]
        self.assertEqual(closed, ["tab close t-t-ba-x", "tab close t-t-dev-x-1"])

        roster = (self.squad / "roster.md").read_text()
        for gone in ("t-ba-x", "t-dev-x-1", "t-dev-x-2"):
            self.assertNotIn(f"| {gone} |", roster)
        self.assertIn("| manager-t |", roster)
        self.assertIn("| t-dev-y-1 |", roster)
        self.assertIn("| Agent | Role |", roster)              # header kept

    def test_scope_mode_dry_run_changes_nothing(self):
        before = (self.squad / "roster.md").read_text()
        r = self.close("--scope", "x", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.squad / "roster.md").read_text(), before)
        self.assertTrue(self.wts["t-dev-x-1"].exists())

    def test_scope_mode_unknown_scope_fails(self):
        r = self.close("--scope", "nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no agents", r.stderr)

    def test_into_picks_the_branch_merges_are_checked_against(self):
        git("branch", "elsewhere", cwd=self.root)
        r = self.close("--into", "elsewhere")
        self.assertIn("squad/t/t-dev-x-2: NOT merged into elsewhere", r.stdout)

    def test_dry_run_changes_nothing(self):
        r = self.close("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.squad.exists())
        self.assertTrue(self.wts["t-dev-x-1"].exists())
        self.assertFalse(self.log.exists() and "tab close" in self.log.read_text())
        self.assertIn("would", r.stdout)

    def test_refuses_to_overwrite_an_existing_archive(self):
        (self.root / ".claude" / "squads" / "_done" / "t").mkdir(parents=True)
        r = self.close()
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(self.squad.exists())
        self.assertTrue(self.wts["t-dev-x-1"].exists())  # refused before touching anything

    def test_unknown_squad_fails(self):
        self.env.pop("SQUAD_DIR")
        r = subprocess.run([str(BIN / "squad-close"), "ghost"], env=self.env, cwd=self.root, text=True, capture_output=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
