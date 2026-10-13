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
               echo "{\\"result\\":{\\"agent\\":{\\"pane_id\\":\\"p-$3\\"}}}" ;;
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
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
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
        closed = [l for l in log if l.startswith("pane close")]
        self.assertEqual(closed, ["pane close p-t-ba-x", "pane close p-t-dev-x-1", "pane close p-manager-t"])  # dead agent skipped, Manager last
        self.assertEqual(log[-1], "pane close p-manager-t")
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

        closed = [l for l in self.log.read_text().splitlines() if l.startswith("pane close")]
        self.assertEqual(closed, ["pane close p-t-ba-x", "pane close p-t-dev-x-1"])

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
        self.assertFalse(self.log.exists() and "pane close" in self.log.read_text())
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


HEAD = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"


class ScopedCloseTest(unittest.TestCase):
    """Per-scope layout: scopes/sc1 (lone), scopes/sc2 and scopes/sc3 (goal g1), goals/g1."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git("init", "-q", "-b", "main", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=self.root)
        self.squad = self.root / ".claude" / "squads" / "t"
        (self.squad / "process.md").parent.mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        for d in ("scopes/sc1", "scopes/sc2", "scopes/sc3", "goals/g1/shared"):
            (self.squad / d).mkdir(parents=True)
        (self.squad / "scopes/sc1/roster.md").write_text(HEAD + "| t-mgr-sc1 | manager | sc1 |  | live | s0 |\n| t-dev-sc1-1 | dev | sc1 | x | live | s1 |\n")
        (self.squad / "scopes/sc1/scope.md").write_text("# Scope\n\ngoal:\n")
        (self.squad / "scopes/sc1/evidence").mkdir()
        (self.squad / "scopes/sc1/evidence/proof.md").write_text("kept")
        (self.squad / "scopes/sc2/roster.md").write_text(HEAD + "| t-dev-sc2-1 | dev | sc2 | x | live | s2 |\n")
        (self.squad / "scopes/sc2/scope.md").write_text("# Scope\n\ngoal: g1\n")
        (self.squad / "scopes/sc3/scope.md").write_text("# Scope\n\ngoal: g1\n")
        (self.squad / "goals/g1/roster.md").write_text(HEAD + "| t-mgr-g1 | manager |  |  | live | s3 |\n")
        (self.squad / "goals/g1/goal.md").write_text("# Goal\n")
        (self.squad / "goals/g1/shared/decisions.md").write_text("# Decisions\n")
        self.wts = {}
        for scope, agent, merged in (("sc1", "t-dev-sc1-1", True), ("sc1", "t-dev-sc1-2", False), ("sc2", "t-dev-sc2-1", True)):
            wt = self.root / ".worktrees" / "t" / scope / agent
            git("worktree", "add", "-q", str(wt), "-b", f"squad/t/{scope}/{agent}", cwd=self.root)
            if not merged:
                git("commit", "-q", "--allow-empty", "-m", "work", cwd=wt)
            self.wts[agent] = wt
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def close(self, *args):
        return subprocess.run([str(BIN / "squad-close"), "t", *args], env=self.env, cwd=self.root,
                              text=True, capture_output=True, timeout=30)

    def closed_tabs(self):
        return [l for l in self.log.read_text().splitlines() if l.startswith("pane close")] if self.log.exists() else []

    def test_scope_close_moves_the_folder_and_tidies_only_that_scopes_worktrees(self):
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.squad / "scopes/sc1").exists())
        self.assertEqual((self.squad / "scopes/_done/sc1/evidence/proof.md").read_text(), "kept")
        self.assertFalse(self.wts["t-dev-sc1-1"].exists())          # merged: removed
        self.assertTrue(self.wts["t-dev-sc1-2"].exists())           # unmerged: kept
        self.assertTrue(self.wts["t-dev-sc2-1"].exists())           # other scope untouched
        self.assertIn("squad/t/sc1/t-dev-sc1-1: merged into main, worktree removed", r.stdout)
        self.assertIn("squad/t/sc1/t-dev-sc1-2: NOT merged into main, kept", r.stdout)
        self.assertNotIn("sc2", r.stdout)
        self.assertEqual(self.closed_tabs(), ["pane close p-t-dev-sc1-1", "pane close p-t-mgr-sc1"])  # the scope's Manager last
        self.assertTrue((self.squad / "scopes/sc2").exists())
        self.assertIn("squad/t/sc1/t-dev-sc1-1", git("branch", "--list", "squad/t/sc1/*", cwd=self.root))  # branches kept

    def test_scope_close_dry_run_changes_nothing(self):
        r = self.close("--scope", "sc1", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.squad / "scopes/sc1").exists())
        self.assertTrue(self.wts["t-dev-sc1-1"].exists())
        self.assertEqual(self.closed_tabs(), [])

    def test_scope_close_refuses_an_existing_archive_and_unknown_scope(self):
        (self.squad / "scopes/_done/sc1").mkdir(parents=True)
        self.assertNotEqual(self.close("--scope", "sc1").returncode, 0)
        self.assertTrue(self.wts["t-dev-sc1-1"].exists())
        self.assertNotEqual(self.close("--scope", "nope").returncode, 0)

    def test_goal_close_refuses_while_a_scope_of_the_goal_is_open(self):
        r = self.close("--goal", "g1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("open scopes", r.stderr)
        self.assertIn("sc2", r.stderr)
        self.assertIn("sc3", r.stderr)
        self.assertTrue((self.squad / "goals/g1").exists())

    def test_goal_close_refuses_unpromoted_decisions_unless_forced(self):
        for s in ("sc2", "sc3"):
            (self.squad / "scopes" / "_done").mkdir(exist_ok=True)
            (self.squad / "scopes" / s).rename(self.squad / "scopes" / "_done" / s)
        (self.squad / "goals/g1/shared/decisions.md").write_text("# Decisions\n\n- the API returns ISO dates\n")
        r = self.close("--goal", "g1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unpromoted", r.stderr)
        self.assertTrue((self.squad / "goals/g1").exists())
        self.assertEqual(self.close("--goal", "g1", "--force").returncode, 0)
        self.assertTrue((self.squad / "goals/_done/g1").exists())

    def test_goal_close_passes_once_promoted_and_retires_the_goal_manager(self):
        for s in ("sc2", "sc3"):
            (self.squad / "scopes" / "_done").mkdir(exist_ok=True)
            (self.squad / "scopes" / s).rename(self.squad / "scopes" / "_done" / s)
        (self.squad / "goals/g1/shared/decisions.md").write_text("# Decisions\n\n- the API returns ISO dates\n")
        (self.squad / "goals/g1/goal.md").write_text("# Goal\n\npromoted: 2026-10-13 abc123\n")
        r = self.close("--goal", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.squad / "goals/g1").exists())
        self.assertEqual(self.closed_tabs(), ["pane close p-t-mgr-g1"])

    def test_squad_close_covers_every_scope_and_goal_roster_and_nested_worktrees(self):
        (self.squad / "goals/g1/shared/decisions.md").write_text("# D\n\n- fact\n")
        r = self.close()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.root / ".claude/squads/_done/t/scopes/sc1/evidence/proof.md").exists())
        tabs = self.closed_tabs()
        self.assertEqual(set(tabs), {"pane close p-t-dev-sc1-1", "pane close p-t-dev-sc2-1", "pane close p-t-mgr-sc1", "pane close p-t-mgr-g1"})
        self.assertEqual(tabs[-2:].count("pane close p-t-mgr-sc1") + tabs[-2:].count("pane close p-t-mgr-g1"), 2)  # Managers last
        self.assertIn("squad/t/sc1/t-dev-sc1-2: NOT merged into main, kept", r.stdout)
        self.assertIn("WARNING: goal g1 has unpromoted decisions", r.stdout)

    def test_flat_squad_with_the_oldest_worktree_layout_is_found_by_agent_name(self):
        squad = self.root / ".claude" / "squads" / "old"
        squad.mkdir(parents=True)
        (squad / "process.md").write_text("x")
        (squad / "roster.md").write_text(HEAD + "| dev-board-1 | dev | board | x | live | s |\n")
        wt = self.root / ".worktrees" / "dev-board-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/dev-board-1", cwd=self.root)
        self.env["SQUAD_DIR"] = str(squad)
        r = subprocess.run([str(BIN / "squad-close"), "old", "--scope", "board"], env=self.env, cwd=self.root,
                           text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad/dev-board-1: merged into main, worktree removed", r.stdout)
        self.assertFalse(wt.exists())


if __name__ == "__main__":
    unittest.main()
