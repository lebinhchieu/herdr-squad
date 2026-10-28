"""squad-close: retire the squad's agents, remove merged worktrees, archive the folder, report branches."""
import os
import shutil
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
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **GIT_ENV}).stdout


class CloseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git("init", "-q", "-b", "main", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=self.root)
        self.squad = self.root / ".claude" / "squads" / "t"
        (self.squad / "evidence").mkdir(parents=True)
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.squad / "evidence" / "proof.md").write_text("kept", encoding="utf-8")
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| manager-t | manager |  |  | live | s0 |\n| t-ba-x | ba | x | biz | live | s1 |\n"
            "| t-dev-x-1 | dev | x | task 1 | live | s2 |\n| t-dev-x-2 | dev | x | task 2 | dead | s3 |\n", encoding="utf-8")
        self.wts = {}
        for n, mode in (("t-dev-x-1", "merged"), ("t-dev-x-2", "unmerged"), ("t-dev-x-3", "dirty")):
            wt = self.root / ".worktrees" / "t" / n
            git("worktree", "add", "-q", str(wt), "-b", f"squad/t/{n}", cwd=self.root)
            if mode == "unmerged":
                git("commit", "-q", "--allow-empty", "-m", "work", cwd=wt)
            if mode == "dirty":
                (wt / "wip.txt").write_text("uncommitted", encoding="utf-8")
                git("add", "wip.txt", cwd=wt)  # staged: a tracked change blocks removal; a plain untracked file does not
            self.wts[n] = wt
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        DEAD="t-dev-x-2", PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def close(self, *args):
        return subprocess.run([str(BIN / "squad-close"), "t", *args], env=self.env, cwd=self.root,
                              text=True, encoding="utf-8", capture_output=True, timeout=30)

    def test_closes_squad_and_reports_each_branch(self):
        r = self.close()
        self.assertEqual(r.returncode, 0, r.stderr)

        self.assertFalse(self.squad.exists())
        self.assertEqual((self.root / ".claude" / "squads" / "_done" / "t" / "evidence" / "proof.md").read_text(encoding="utf-8"), "kept")

        self.assertFalse(self.wts["t-dev-x-1"].exists())      # merged and clean: removed
        self.assertTrue(self.wts["t-dev-x-2"].exists())       # unmerged: kept
        self.assertTrue(self.wts["t-dev-x-3"].exists())       # merged but uncommitted work: kept
        self.assertIn("squad/t/t-dev-x-1: merged into main, worktree removed", r.stdout)
        self.assertIn("squad/t/t-dev-x-2: NOT merged into main, kept", r.stdout)
        self.assertIn("squad/t/t-dev-x-3: merged into main, kept (uncommitted changes)", r.stdout)
        self.assertIn("squad/t/t-dev-x-1", git("branch", "--list", "squad/t/*", cwd=self.root))  # branches are never deleted

        log = self.log.read_text(encoding="utf-8").splitlines()
        closed = [l for l in log if l.startswith("pane close")]
        self.assertEqual(closed, ["pane close p-t-ba-x", "pane close p-t-dev-x-1", "pane close p-manager-t"])  # dead agent skipped, Manager last
        self.assertEqual(log[-1], "pane close p-manager-t")
        self.assertFalse(any(l.startswith("agent prompt") for l in log))  # nothing to save for a closed goal

    def _add_scope_y_dev(self):
        with (self.squad / "roster.md").open("a", encoding="utf-8") as f:
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

        closed = [l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("pane close")]
        self.assertEqual(closed, ["pane close p-t-ba-x", "pane close p-t-dev-x-1"])

        roster = (self.squad / "roster.md").read_text(encoding="utf-8")
        for gone in ("t-ba-x", "t-dev-x-1", "t-dev-x-2"):
            self.assertNotIn(f"| {gone} |", roster)
        self.assertIn("| manager-t |", roster)
        self.assertIn("| t-dev-y-1 |", roster)
        self.assertIn("| Agent | Role |", roster)              # header kept

    def test_scope_mode_dry_run_changes_nothing(self):
        before = (self.squad / "roster.md").read_text(encoding="utf-8")
        r = self.close("--scope", "x", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.squad / "roster.md").read_text(encoding="utf-8"), before)
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
        self.assertFalse(self.log.exists() and "pane close" in self.log.read_text(encoding="utf-8"))
        self.assertIn("would", r.stdout)

    def test_refuses_to_overwrite_an_existing_archive(self):
        (self.root / ".claude" / "squads" / "_done" / "t").mkdir(parents=True)
        r = self.close()
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(self.squad.exists())
        self.assertTrue(self.wts["t-dev-x-1"].exists())  # refused before touching anything

    def test_unknown_squad_fails(self):
        self.env.pop("SQUAD_DIR")
        r = subprocess.run([str(BIN / "squad-close"), "ghost"], env=self.env, cwd=self.root, text=True, encoding="utf-8", capture_output=True, timeout=10)
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
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        for d in ("scopes/sc1", "scopes/sc2", "scopes/sc3", "goals/g1/shared"):
            (self.squad / d).mkdir(parents=True)
        (self.squad / "scopes/sc1/roster.md").write_text(HEAD + "| t-mgr-sc1 | manager | sc1 |  | live | s0 |\n| t-dev-sc1-1 | dev | sc1 | x | live | s1 |\n", encoding="utf-8")
        (self.squad / "scopes/sc1/scope.md").write_text("# Scope\n\ngoal:\n", encoding="utf-8")
        (self.squad / "scopes/sc1/evidence").mkdir()
        (self.squad / "scopes/sc1/evidence/proof.md").write_text("kept", encoding="utf-8")
        (self.squad / "scopes/sc2/roster.md").write_text(HEAD + "| t-dev-sc2-1 | dev | sc2 | x | live | s2 |\n", encoding="utf-8")
        (self.squad / "scopes/sc2/scope.md").write_text("# Scope\n\ngoal: g1\n", encoding="utf-8")
        (self.squad / "scopes/sc3/scope.md").write_text("# Scope\n\ngoal: g1\n", encoding="utf-8")
        (self.squad / "goals/g1/roster.md").write_text(HEAD + "| t-mgr-g1 | manager |  |  | live | s3 |\n", encoding="utf-8")
        (self.squad / "goals/g1/goal.md").write_text("# Goal\n", encoding="utf-8")
        (self.squad / "goals/g1/shared/decisions.md").write_text("# Decisions\n", encoding="utf-8")
        self.wts = {}
        for scope, agent, merged in (("sc1", "t-dev-sc1-1", True), ("sc1", "t-dev-sc1-2", False), ("sc2", "t-dev-sc2-1", True)):
            wt = self.root / ".worktrees" / "t" / scope / agent
            git("worktree", "add", "-q", str(wt), "-b", f"squad/t/{scope}/{agent}", cwd=self.root)
            if not merged:
                git("commit", "-q", "--allow-empty", "-m", "work", cwd=wt)
            self.wts[agent] = wt
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def close(self, *args):
        return subprocess.run([str(BIN / "squad-close"), "t", *args], env=self.env, cwd=self.root,
                              text=True, encoding="utf-8", capture_output=True, timeout=30)

    def closed_tabs(self):
        return [l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("pane close")] if self.log.exists() else []

    def test_scope_close_moves_the_folder_and_tidies_only_that_scopes_worktrees(self):
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.squad / "scopes/sc1").exists())
        self.assertEqual((self.squad / "scopes/_done/sc1/evidence/proof.md").read_text(encoding="utf-8"), "kept")
        self.assertFalse(self.wts["t-dev-sc1-1"].exists())          # merged: removed
        self.assertTrue(self.wts["t-dev-sc1-2"].exists())           # unmerged: kept
        self.assertTrue(self.wts["t-dev-sc2-1"].exists())           # other scope untouched
        self.assertIn("squad/t/sc1/t-dev-sc1-1: merged into main, worktree removed", r.stdout)
        self.assertIn("squad/t/sc1/t-dev-sc1-2: NOT merged into main, kept", r.stdout)
        self.assertNotIn("sc2", r.stdout)
        self.assertEqual(self.closed_tabs(), ["pane close p-t-dev-sc1-1", "pane close p-t-mgr-sc1"])  # the scope's Manager last
        self.assertTrue((self.squad / "scopes/sc2").exists())
        self.assertIn("squad/t/sc1/t-dev-sc1-1", git("branch", "--list", "squad/t/sc1/*", cwd=self.root))  # branches kept

    def test_scope_close_lists_untracked_root_files_and_still_closes(self):
        stray = self.root / ".scratch" / "x" / "issues"
        stray.mkdir(parents=True)
        (stray / "01.md").write_text("draft", encoding="utf-8")
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING: untracked files in the project root", r.stdout)
        self.assertIn(".scratch/x/issues/01.md", r.stdout)
        listed = [l for l in r.stdout.split("== agents")[0].splitlines() if l.startswith("  ")]
        self.assertIn("  .scratch/x/issues/01.md", listed)
        self.assertFalse([l for l in listed if ".claude/squads" in l or ".worktrees" in l])  # not reported
        self.assertFalse((self.squad / "scopes/sc1").exists())               # the close went through

    def test_scope_close_without_stray_files_prints_no_warning(self):
        (self.root / ".gitignore").write_text("fakebin/\nherdr.log\n.gitignore\n", encoding="utf-8")
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("WARNING: untracked", r.stdout)

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
        (self.squad / "goals/g1/shared/decisions.md").write_text("# Decisions\n\n- the API returns ISO dates\n", encoding="utf-8")
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
        (self.squad / "goals/g1/shared/decisions.md").write_text("# Decisions\n\n- the API returns ISO dates\n", encoding="utf-8")
        (self.squad / "goals/g1/goal.md").write_text("# Goal\n\npromoted: 2026-10-13 abc123\n", encoding="utf-8")
        r = self.close("--goal", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.squad / "goals/g1").exists())
        self.assertEqual(self.closed_tabs(), ["pane close p-t-mgr-g1"])

    def test_squad_close_covers_every_scope_and_goal_roster_and_nested_worktrees(self):
        (self.squad / "goals/g1/shared/decisions.md").write_text("# D\n\n- fact\n", encoding="utf-8")
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
        (squad / "process.md").write_text("x", encoding="utf-8")
        (squad / "roster.md").write_text(HEAD + "| dev-board-1 | dev | board | x | live | s |\n", encoding="utf-8")
        wt = self.root / ".worktrees" / "dev-board-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/dev-board-1", cwd=self.root)
        self.env["SQUAD_DIR"] = str(squad)
        r = subprocess.run([str(BIN / "squad-close"), "old", "--scope", "board"], env=self.env, cwd=self.root,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad/dev-board-1: merged into main, worktree removed", r.stdout)
        self.assertFalse(wt.exists())


if __name__ == "__main__":
    unittest.main()


class WorktreeFinderTest(unittest.TestCase):
    """Worktrees are found by branch from `git worktree list`, not by folder: .worktrees/<name> works too."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git("init", "-q", "-b", "main", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=self.root)
        self.squad = self.root / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.squad / "roster.md").write_text(HEAD + "| dev-a | dev | x | t | live | s1 |\n", encoding="utf-8")
        self.wts = {}
        for name, branch in (("dev-a", "squad/dev-a"),          # old layout: .worktrees/<name>, branch squad/<name>
                             ("dev-b", "squad/t/x/dev-b"),      # nested, scope layout
                             ("dev-c", "squad/dev-c"),          # unmerged
                             ("dev-d", "squad/dev-d"),          # tracked change
                             ("dev-e", "squad/other/dev-e"),    # another squad's, not in the roster
                             ("hand", "feature/hand")):         # not a squad branch
            wt = self.root / ".worktrees" / name
            git("worktree", "add", "-q", str(wt), "-b", branch, cwd=self.root)
            self.wts[name] = wt
        git("commit", "-q", "--allow-empty", "-m", "work", cwd=self.wts["dev-c"])
        (self.wts["dev-d"] / "README").write_text("x", encoding="utf-8")
        git("add", "README", cwd=self.wts["dev-d"])
        (self.wts["dev-a"] / "__pycache__").mkdir()
        (self.wts["dev-a"] / "__pycache__" / "m.pyc").write_text("c", encoding="utf-8")
        (self.wts["dev-a"] / "agent.pid").write_text("1", encoding="utf-8")
        with (self.squad / "roster.md").open("a", encoding="utf-8") as f:
            f.write("| dev-b | dev | x | t | live | s2 |\n| dev-c | dev | y | t | live | s3 |\n| dev-d | dev | y | t | live | s4 |\n")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.root / "h.log"),
                        PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def close(self, *args):
        return subprocess.run([str(BIN / "squad-close"), "t", *args], env=self.env, cwd=self.root,
                              text=True, encoding="utf-8", capture_output=True, timeout=30)

    def test_removes_merged_clean_worktrees_in_any_folder_and_lists_untracked(self):
        r = self.close("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad/dev-a: merged into main, would remove worktree; untracked files would go with it: "
                      "__pycache__/, agent.pid", r.stdout)
        self.assertTrue(self.wts["dev-a"].exists())  # dry run changes nothing

        r = self.close()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad/dev-a: merged into main, worktree removed; untracked files removed with it: __pycache__/, agent.pid", r.stdout)
        self.assertIn("squad/t/x/dev-b: merged into main, worktree removed", r.stdout)
        self.assertFalse(self.wts["dev-a"].exists())
        self.assertFalse(self.wts["dev-b"].exists())
        self.assertIn("squad/dev-c: NOT merged into main, kept", r.stdout)
        self.assertIn("squad/dev-d: merged into main, kept (uncommitted changes)", r.stdout)
        for kept in ("dev-c", "dev-d", "dev-e", "hand"):
            self.assertTrue(self.wts[kept].exists(), kept)
        self.assertNotIn("feature/hand", r.stdout)
        self.assertNotIn("squad/other/dev-e", r.stdout)
        self.assertIn("squad/dev-a", git("branch", "--list", "squad/dev-a", cwd=self.root))  # branches stay

    def test_target_is_the_branch_of_the_main_worktree(self):
        git("checkout", "-q", "-b", "release", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", "on release", cwd=self.root)
        r = self.close("--dry-run")
        self.assertIn("squad/dev-a: merged into release, would remove worktree", r.stdout)

    def test_scope_mode_takes_the_scope_branches_and_roster_names(self):
        (self.squad / "scopes" / "x").mkdir(parents=True)
        (self.squad / "scopes" / "x" / "roster.md").write_text(HEAD + "| dev-b | dev | x | t | live | s2 |\n", encoding="utf-8")
        r = self.close("--scope", "x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.wts["dev-b"].exists())
        self.assertTrue(self.wts["dev-a"].exists())  # not a worktree of this scope


ESC = ("# Escalations\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n"
       "| 2 | 2026-10-14 | Ship it? | (a) yes; (b) no | a | X | |\n"
       "| 1 | 2026-10-14 | Old one | (a) x | | | (a) x |\n")


class InboxGuardTest(unittest.TestCase):
    setUp, tearDown, close = ScopedCloseTest.setUp, ScopedCloseTest.tearDown, ScopedCloseTest.close
    """PI-06 (B-29): a scope or goal with open answer items is not closed unless --force."""

    def put(self, folder, text=ESC):
        (self.squad / folder / "escalations.md").write_text(text, encoding="utf-8")

    def inbox(self, folder, *args, body=""):
        env = {**self.env, "SQUAD_ROLE": "manager", "SQUAD_INBOX_NOW": "2026-10-15T10:00:00Z"}
        return subprocess.run([str(BIN / "squad-inbox"), "--home", str(self.squad / folder), *args], env=env,
                              text=True, encoding="utf-8", capture_output=True, timeout=30, input=body)

    def assertNothingDone(self, folder):
        self.assertTrue((self.squad / folder).exists())
        self.assertFalse(self.log.exists() and self.log.read_text(encoding="utf-8").strip())

    def test_open_item_refuses_scope_close(self):
        self.put("scopes/sc1")
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("scope sc1 has 1 open answer items: E2 Ship it?", r.stderr)
        self.assertIn("--force", r.stderr)
        self.assertNothingDone("scopes/sc1")
        self.assertTrue(self.wts["t-dev-sc1-1"].exists())

    def test_answered_waiting_blocks_but_delivered_withdrawn_and_read_do_not(self):
        self.put("scopes/sc1")
        self.assertEqual(self.inbox("scopes/sc1", "answer", "E2", "--option", "a", "--source", "pane").returncode, 0)
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("E2 Ship it? (answered, not yet read by the Manager)", r.stderr)
        self.assertNothingDone("scopes/sc1")
        self.assertEqual(self.inbox("scopes/sc1", "delivered", "E2", "--session", "s").returncode, 0)
        self.assertEqual(self.inbox("scopes/sc1", "add", "--kind", "read", "--title", "FYI", body="details").returncode, 0)
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_withdrawn_does_not_block(self):
        self.put("scopes/sc1")
        self.assertEqual(self.inbox("scopes/sc1", "withdraw", "E2", "--reason", "gone").returncode, 0)
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)

    def test_force_closes_and_dry_run_reports_without_acting(self):
        self.put("scopes/sc1")
        r = self.close("--scope", "sc1", "--dry-run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("open answer items", r.stderr)
        self.assertNothingDone("scopes/sc1")
        r = self.close("--scope", "sc1", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.squad / "scopes/_done/sc1").exists())

    def test_goal_checks_only_its_own_folder_and_promoted_comes_first(self):
        for s in ("sc2", "sc3"):
            self.close("--scope", s, "--force")
        self.put("goals/g1")
        r = self.close("--goal", "g1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("goal g1 has 1 open answer items: E2 Ship it?", r.stderr)
        (self.squad / "goals/g1/shared/decisions.md").write_text("# D\n\n- fact\n", encoding="utf-8")
        self.assertIn("unpromoted", self.close("--goal", "g1").stderr)
        self.assertEqual(self.close("--goal", "g1", "--force").returncode, 0)

    def test_open_item_elsewhere_does_not_block(self):
        self.put("scopes/sc2")
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)

    def test_malformed_row_warns_naming_file_and_row(self):
        self.put("scopes/sc1", ESC.replace("| 2 | 2026-10-14 | Ship it? | (a) yes; (b) no | a | X | |\n", "")
                 + "| 3 | 2026-10-14 | Too many | | | | | | | |\n")
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning: escalations.md row 6:", r.stderr)

    def test_refused_close_leaves_the_folder_untouched(self):
        self.put("scopes/sc1")
        folder = self.squad / "scopes/sc1"
        snap = {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}
        self.assertEqual(self.close("--scope", "sc1").returncode, 1)
        self.assertEqual({p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}, snap)

    def test_two_blockers_are_counted_and_joined(self):
        self.put("scopes/sc1", ESC.replace("| 1 | 2026-10-14 | Old one | (a) x | | | (a) x |\n", "| 1 | 2026-10-14 | Other one | (a) x; (b) y | | | |\n"))
        self.assertEqual(self.inbox("scopes/sc1", "answer", "E1", "--option", "a", "--source", "pane").returncode, 0)
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("scope sc1 has 2 open answer items: E2 Ship it?, E1 Other one (answered, not yet read by the Manager) (answer", r.stderr)

    def test_blocker_snippet_prints_lf_only_and_sets_it_first(self):
        # On Windows a text-mode stdout turns "\n" into "\r\n", which would land in $blockers.
        src = (BIN / "squad-close").read_text(encoding="utf-8")
        snippet = src.split("python3 -X utf8 -c '", 1)[1].split("\n' \"$1\"", 1)[0]
        self.assertTrue(snippet.lstrip().splitlines()[1].startswith('sys.stdout.reconfigure(newline="\\n")'), snippet[:120])
        payload = b'{"items": [{"kind": "answer", "state": "open", "id": "E1", "title": "A"}, ' \
                  b'{"kind": "answer", "state": "open", "id": "E2", "title": "B"}], "errors": []}'
        r = subprocess.run(["python3", "-X", "utf8", "-c", snippet, "x"], input=payload, capture_output=True, timeout=30)
        self.assertEqual((r.returncode, r.stdout), (0, b"E1 A\nE2 B\n"), r.stderr)

    def test_missing_cli_warns_and_does_not_block(self):
        self.put("scopes/sc1")
        lone = self.root / "lonebin"
        lone.mkdir()
        for n in ("squad-close", "squad-retire"):
            (lone / n).write_text((BIN / n).read_text(encoding="utf-8"))
            (lone / n).chmod(0o755)
        r = subprocess.run([str(lone / "squad-close"), "t", "--scope", "sc1"], env=self.env, cwd=self.root,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning", r.stderr)

    def test_non_json_output_warns_and_does_not_block(self):
        self.put("scopes/sc1")
        lone = self.root / "lonebin"
        lone.mkdir()
        for n in ("squad-close", "squad-retire"):
            (lone / n).write_text((BIN / n).read_text(encoding="utf-8"))
            (lone / n).chmod(0o755)
        (lone / "squad-inbox").write_text("#!/bin/sh\necho not json\n", encoding="utf-8")
        (lone / "squad-inbox").chmod(0o755)
        r = subprocess.run([str(lone / "squad-close"), "t", "--scope", "sc1"], env=self.env, cwd=self.root,
                           text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("did not answer with JSON", r.stderr)


class ReportHookTest(unittest.TestCase):
    """squad-close builds the report first (a stub squad-report in a copied bin/) and never fails because of it."""
    setUp = ScopedCloseTest.setUp
    tearDown = ScopedCloseTest.tearDown
    closed_tabs = ScopedCloseTest.closed_tabs

    REC = ("#!/usr/bin/env python3\n"
           "import os, sys\n"
           "d = sys.argv[sys.argv.index('--squad') + 1]\n"
           "open(os.environ['CALLS'], 'a').write(' '.join(sys.argv[1:]) + '|' + str(os.path.isdir(d + '/scopes/sc1')) + '|' + "
           "str(os.path.isdir(d + '/goals/g1')) + '|' + str(os.path.exists(os.environ['HERDR_LOG'])) + '\\n')\n")

    def stub_bin(self, body):
        lone = self.root / "stubbin"
        lone.mkdir()
        for n in ("squad-close", "squad-retire", "squad-inbox"):
            (lone / n).write_text((BIN / n).read_text(encoding="utf-8"), encoding="utf-8")
            (lone / n).chmod(0o755)
        for p in BIN.glob("squad*.py"):
            (lone / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        (lone / "squad-report").write_text(body, encoding="utf-8")
        self.calls = self.root / "report.calls"
        self.env["CALLS"] = str(self.calls)
        self.env.pop("SQUAD_DIR", None)  # squad-close finds the folder itself; the report must still get it
        return lone

    def run_close(self, lone, *args):
        return subprocess.run([str(lone / "squad-close"), "t", *args], env=self.env, cwd=self.root,
                              text=True, encoding="utf-8", capture_output=True, timeout=30)

    def test_scope_close_builds_the_report_first_with_the_deadline(self):
        r = self.run_close(self.stub_bin(self.REC), "--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls.read_text(encoding="utf-8").splitlines(), ["sc1 --squad %s --final --quiet --deadline 60|True|True|False" % self.squad.resolve()])
        self.assertTrue((self.squad / "scopes/_done/sc1").exists())
        self.assertNotIn("warning", r.stderr)

    def test_goal_close_passes_the_goal_name(self):
        for s in ("sc2", "sc3"):
            (self.squad / "scopes" / "_done").mkdir(exist_ok=True)
            (self.squad / "scopes" / s).rename(self.squad / "scopes" / "_done" / s)
        r = self.run_close(self.stub_bin(self.REC), "--goal", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls.read_text(encoding="utf-8").splitlines(), ["g1 --squad %s --final --quiet --deadline 60|True|True|False" % self.squad.resolve()])
        self.assertTrue((self.squad / "goals/_done/g1").exists())

    def test_failing_or_noisy_report_warns_once_and_changes_nothing_else(self):
        base = self.run_close(self.stub_bin("#!/usr/bin/env python3\n"), "--scope", "sc1")  # stub exits 0: the no-hook close
        base_out = base.stdout.replace(str(self.root), "ROOT")
        self.assertEqual(base.returncode, 0, base.stderr)
        self.tearDown()
        self.setUp()
        lone = self.stub_bin("#!/usr/bin/env python3\nimport sys\nprint('junk <<<')\nsys.exit(7)\n")
        r = self.run_close(lone, "--scope", "sc1")
        self.assertEqual(r.returncode, base.returncode)
        self.assertEqual(r.stdout.replace(str(self.root), "ROOT"), base_out)
        self.assertEqual(r.stderr.strip(), "warning: report not generated (squad-report exited 7)")
        self.assertTrue((self.squad / "scopes/_done/sc1/evidence/proof.md").exists())
        self.assertEqual(self.closed_tabs(), ["pane close p-t-dev-sc1-1", "pane close p-t-mgr-sc1"])

    def test_dry_run_never_calls_the_report(self):
        r = self.run_close(self.stub_bin(self.REC), "--scope", "sc1", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.calls.exists())
        self.assertTrue((self.squad / "scopes/sc1").exists())


FILLED = """# Iteration 1

## Log
- 2026-10-22 started

## Retro
- **Went well:** shipped
- **Friction:** loops
- **Process changes made:** none
"""


class RetroCloseTest(ScopedCloseTest):
    """Ticket 13: no scope closes with a blank retro (ITER-16)."""

    def iter_file(self, text, n="1"):
        d = self.squad / "scopes/sc1/iterations"
        d.mkdir(exist_ok=True)
        (d / f"{n}.md").write_text(text, encoding="utf-8", newline="\n")
        return d / f"{n}.md"

    def refused(self, text, label):
        self.iter_file(text)
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(label, r.stderr)
        self.assertTrue((self.squad / "scopes/sc1").exists())      # nothing moved
        self.assertEqual(self.closed_tabs(), [])                    # nothing retired

    def test_each_empty_label_refuses_and_is_named(self):
        for label in ("Went well", "Friction", "Process changes made"):
            with self.subTest(label=label):
                line = next(l for l in FILLED.splitlines() if f"**{label}:**" in l)
                self.refused(FILLED.replace(line, f"- **{label}:**"), label)

    def test_placeholder_alone_is_empty_but_text_with_brackets_is_not(self):
        self.refused(FILLED.replace("loops", "<loops, blocked panes>"), "Friction")
        self.iter_file(FILLED.replace("loops", "<2> loops"))
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)

    def test_none_dash_and_continuation_lines_count_as_text(self):
        for text in ("none", "-", "n/a"):
            with self.subTest(text=text):
                self.tearDown(); self.setUp()
                self.iter_file(FILLED.replace("shipped", text))
                self.assertEqual(self.close("--scope", "sc1").returncode, 0)
        self.tearDown(); self.setUp()
        self.iter_file(FILLED.replace("- **Friction:** loops", "- **Friction:**\n  slow review\n- **Other:** x"))
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)
        self.tearDown(); self.setUp()
        self.iter_file(FILLED.replace("- **Friction:** loops", "- **Friction:**\n  - one sub-bullet"))
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)

    def test_free_retro_heading_and_label_missing(self):
        self.iter_file(FILLED.replace("## Retro", "## Retro / Coach"))
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)
        self.tearDown(); self.setUp()
        self.refused(FILLED.replace("- **Went well:** shipped\n", ""), "Went well")

    def test_no_iteration_file_and_flat_squad_are_not_checked(self):
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)

    def test_last_iteration_is_the_highest_number_and_aux_files_are_ignored(self):
        self.iter_file(FILLED.replace("loops", ""), "9")            # blank, but not the last
        self.iter_file(FILLED, "10")
        d = self.squad / "scopes/sc1/iterations"
        for aux in ("10.log.md", "10.summary.md", "10.coach.md"):
            (d / aux).write_text("# blank\n- **Friction:**\n", encoding="utf-8")
        self.assertEqual(self.close("--scope", "sc1").returncode, 0)
        self.tearDown(); self.setUp()
        self.iter_file(FILLED, "9")
        self.iter_file(FILLED.replace("loops", ""), "10")        # 10 > 9 numerically, "10" < "9" as a string
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("Friction", r.stderr)


    def test_force_closes_and_logs_with_and_without_a_log_section(self):
        blank = FILLED.replace("loops", "")
        f = self.iter_file(blank)
        r = self.close("--scope", "sc1", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Friction", r.stdout)
        done = (self.squad / "scopes/_done/sc1/iterations/1.md").read_text(encoding="utf-8")
        self.assertRegex(done, r"## Log\n- 2026-10-22 started\n- \d{4}-\d\d-\d\d squad-close --force: empty retro \(Friction\)\n\n## Retro")
        self.tearDown(); self.setUp()
        f = self.iter_file(blank.replace("## Log\n- 2026-10-22 started\n\n", ""))
        self.assertEqual(self.close("--scope", "sc1", "--force").returncode, 0)
        done = (self.squad / "scopes/_done/sc1/iterations/1.md").read_text(encoding="utf-8")
        self.assertRegex(done, r"\n## Log\n- \d{4}-\d\d-\d\d squad-close --force: empty retro")

    def test_force_on_a_filled_retro_and_dry_run_write_nothing(self):
        f = self.iter_file(FILLED)
        self.assertEqual(self.close("--scope", "sc1", "--force").returncode, 0)
        self.assertEqual((self.squad / "scopes/_done/sc1/iterations/1.md").read_text(encoding="utf-8"), FILLED)
        self.tearDown(); self.setUp()
        f = self.iter_file(FILLED.replace("loops", ""))
        before = f.read_text(encoding="utf-8")
        self.assertEqual(self.close("--scope", "sc1", "--force", "--dry-run").returncode, 0)
        self.assertEqual(f.read_text(encoding="utf-8"), before)


X, Y, Z = "1.0-" + "a" * 12, "1.0-" + "b" * 12, "1.0-" + "c" * 12


class RuntimePruneCloseTest(ScopedCloseTest):
    """Ticket 25: closing frees the pinned runtimes nobody holds, never the one the script runs from."""

    def setUp(self):
        super().setUp()
        (self.squad / "scopes/sc1/scope.md").write_text(f"# Scope\n\ngoal:\nplugin: 1.0 {'a' * 12}\n", encoding="utf-8")
        (self.squad / "scopes/sc2/scope.md").write_text(f"# Scope\n\ngoal: g1\nplugin: 1.0 {'b' * 12}\n", encoding="utf-8")
        self.rt = self.squad / "_runtime"
        for n in (X, Y, Z):
            (self.rt / n / "bin").mkdir(parents=True)
            (self.rt / n / "bin" / "f").write_text("x" * 1048576, encoding="utf-8")
        # the fake herdr records whether runtime X still exists when a pane is closed
        fake = self.root / "fakebin" / "herdr"
        fake.write_text(FAKE_HERDR.replace('echo "$@" >> "$HERDR_LOG"',
                        'echo "$@ rt=$([ -d "$RT_X" ] && echo yes || echo no)" >> "$HERDR_LOG"'), encoding="utf-8")
        self.env["RT_X"] = str(self.rt / X)

    def test_scope_close_removes_its_runtime_and_the_orphan_and_keeps_the_held_one(self):
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("== runtimes", r.stdout)
        self.assertIn(f"removed {X} (1.0 MB)", r.stdout)
        self.assertIn(f"removed {Z} (1.0 MB)", r.stdout)          # an orphan
        self.assertIn(f"kept {Y} (held by scope sc2)", r.stdout)
        self.assertIn("freed 2.0 MB in 2 runtimes", r.stdout)
        self.assertEqual(sorted(p.name for p in self.rt.iterdir()), [Y])

    def test_prune_runs_after_the_agents_and_before_the_managers_pane_is_closed(self):
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        closes = [l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("pane close")]
        self.assertEqual(len(closes), 2, closes)
        self.assertTrue(closes[0].startswith("pane close p-t-dev-sc1-1") and closes[0].endswith("rt=yes"))   # before the prune
        self.assertTrue(closes[1].startswith("pane close p-t-mgr-sc1") and closes[1].endswith("rt=no"))     # after it
        self.assertLess(r.stdout.index("== branches"), r.stdout.index("== runtimes"))
        self.assertLess(r.stdout.index("== runtimes"), r.stdout.index("== folder"))

    def test_goal_pin_keeps_a_scope_runtime_until_the_goal_closes(self):
        (self.squad / "goals/g1/goal.md").write_text(f"# Goal\nplugin: 1.0 {'b' * 12}\n", encoding="utf-8")
        r = self.close("--scope", "sc2")
        self.assertIn(f"kept {Y} (held by goal g1)", r.stdout)
        self.assertTrue((self.rt / Y).exists())
        (self.squad / "scopes/_done").mkdir(exist_ok=True)
        (self.squad / "scopes/sc3").rename(self.squad / "scopes/_done/sc3")
        r = self.close("--goal", "g1")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn(f"removed {Y}", r.stdout)                   # the goal's own pin is not a holder
        self.assertEqual(sorted(p.name for p in self.rt.iterdir()), [X])   # X is still held by sc1

    def test_dry_run_removes_nothing_and_says_would_remove(self):
        r = self.close("--scope", "sc1", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"would remove {X} (1.0 MB)", r.stdout)
        self.assertIn("would free 2.0 MB in 2 runtimes", r.stdout)
        self.assertEqual(sorted(p.name for p in self.rt.iterdir()), [X, Y, Z])

    def test_whole_squad_close_prunes_all_before_the_archive(self):
        r = self.close()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn(f"removed {Y} (1.0 MB)", r.stdout)          # even though sc2 pins it
        self.assertFalse((self.root / ".claude/squads/_done/t/_runtime").exists())
        self.assertLess(r.stdout.index("== runtimes"), r.stdout.index("== folder"))

    def test_runtime_the_script_runs_from_is_kept_and_archived_with_a_whole_squad(self):
        shutil.copytree(BIN, self.rt / Z / "bin", dirs_exist_ok=True)
        script = self.rt / Z / "bin" / "squad-close"

        def run(*a):
            return subprocess.run([str(script), "t", *a], env=self.env, cwd=self.root, text=True,
                                  encoding="utf-8", capture_output=True, timeout=30)
        r = run("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"kept {Z} (running)", r.stdout)
        self.assertTrue(script.exists())
        self.assertFalse((self.rt / X).exists())
        r = run()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn(f"kept {Z} (running)", r.stdout)
        self.assertEqual([p.name for p in (self.root / ".claude/squads/_done/t/_runtime").iterdir()], [Z])

    def test_a_failed_prune_only_warns_and_the_close_completes(self):
        bad = self.root / "badbin"
        shutil.copytree(BIN, bad)
        (bad / "squad-process").write_text("import sys\nprint(\"boom\", file=sys.stderr)\nsys.exit(7)\n", encoding="utf-8")
        r = subprocess.run([str(bad / "squad-close"), "t", "--scope", "sc1"], env=self.env, cwd=self.root, text=True,
                           encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning: runtime cleanup failed (exit 7)", r.stderr)
        self.assertTrue((self.squad / "scopes/_done/sc1").exists())

    def test_undeletable_runtime_is_reported_and_the_close_completes(self):
        if os.name == "nt" or os.geteuid() == 0:
            self.skipTest("needs permissions to deny")
        self.rt.chmod(0o555)
        try:
            r = self.close("--scope", "sc1")
        finally:
            self.rt.chmod(0o755)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"could not remove {X}", r.stdout)
        self.assertTrue((self.squad / "scopes/_done/sc1").exists())

    def test_a_squad_without_runtimes_prints_nothing_new(self):
        shutil.rmtree(self.rt)
        r = self.close("--scope", "sc1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("runtimes", r.stdout)
        self.assertNotIn("freed", r.stdout)


# the scoped-layout tests inherited from ScopedCloseTest are not re-run under the runtime fixture
for _name in [n for n in dir(ScopedCloseTest) if n.startswith("test_")]:
    setattr(RuntimePruneCloseTest, _name, None)
