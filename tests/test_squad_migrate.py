"""squad-migrate: flat squad -> per-scope, and scope -> goal. Temp folders only."""
import datetime
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-migrate"
HEAD = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
ROWS = ["| mgr | Manager | all | the run | live | s0 |",
        "| dev-1 | dev | board | task | live | s1 |",
        "| qa-1 | qa-whitebox | board | checks | dead | s2 |"]
ROSTER = "# Roster\n\n**Intro line with | a pipe.**\n\n" + HEAD + "\n".join(ROWS) + "\n\nTrailing note kept.\n"
GOAL = "# Goal\n\n**Build the thing, as specced.**\n\n## In scope\n- all of it\n"
SCOPES = ("# Scopes\n\n| Scope | Size | Signals |\n|---|---|---|\n"
          "| board | **S + QA whitebox** (exception, see process.md) | ten tasks |\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squads = self.root / ".claude" / "squads"
        self.squad = self.squads / "t"
        self.squad.mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(SQUAD_DIR=str(self.squad), PYTHONDONTWRITEBYTECODE="1")
        self.backup = self.root / ".claude" / "squad-backups" / f"t-{datetime.date.today()}"

    def tearDown(self):
        self.tmp.cleanup()

    def migrate(self, *args):
        return subprocess.run([str(SCRIPT), "t", *args], env=self.env, cwd=self.root, text=True,
                              capture_output=True, timeout=30)

    def tree(self, base=None):
        base = base or self.squad
        return sorted(str(p.relative_to(base)) for p in base.rglob("*"))

    def make_flat(self):
        s = self.squad
        for f, text in (("process.md", "process"), ("project.md", "project"), ("process-log.md", "log"),
                        ("roster.md", ROSTER), ("goal.md", GOAL), ("scopes.md", SCOPES),
                        ("escalations.md", "esc"), ("messages.jsonl", '{"a":1}\n'),
                        ("activity.jsonl", "act"), ("usage-events.jsonl", "use")):
            (s / f).write_text(text)
        for d in ("iterations", "roles", "evidence/x", "contracts", "work", "settings"):
            (s / d).mkdir(parents=True)
        (s / "iterations" / "1.md").write_text("iter")
        (s / "evidence" / "x" / "proof.md").write_text("proof")
        (s / "settings" / "dev.json").write_text("{}")


class ToPerScopeTest(Base):
    def test_moves_everything_and_writes_scope_md(self):
        self.make_flat()
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertEqual(r.returncode, 0, r.stderr)
        sc = self.squad / "scopes" / "board"
        for f in ("roster.md", "escalations.md", "messages.jsonl", "activity.jsonl", "usage-events.jsonl"):
            self.assertTrue((sc / f).is_file(), f)
            self.assertFalse((self.squad / f).exists(), f)
        for d in ("iterations", "roles", "evidence", "contracts", "work"):
            self.assertTrue((sc / d).is_dir(), d)
        self.assertEqual((sc / "evidence" / "x" / "proof.md").read_text(), "proof")
        self.assertEqual((sc / "iterations" / "1.md").read_text(), "iter")
        self.assertEqual((sc / "roster.md").read_text(), ROSTER)       # moved untouched
        self.assertEqual((sc / "legacy" / "goal.md").read_text(), GOAL)
        self.assertEqual((sc / "legacy" / "scopes.md").read_text(), SCOPES)
        for kept in ("process.md", "project.md", "process-log.md", "settings"):
            self.assertTrue((self.squad / kept).exists(), kept)
        self.assertFalse((self.squad / "goal.md").exists())
        scope_md = (sc / "scope.md").read_text()
        self.assertIn("# Scope: board", scope_md)
        self.assertIn("**Build the thing, as specced.**", scope_md)
        self.assertIn("size: S + QA whitebox\n", scope_md)
        self.assertIn("goal:", scope_md)
        self.assertNotIn("{{", scope_md)
        self.assertIn("checked", r.stdout)
        self.assertIn("all there", r.stdout)
        self.assertNotIn("PROBLEM", r.stdout)

    def test_backup_is_a_full_copy_of_the_old_layout(self):
        self.make_flat()
        before = self.tree()
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.tree(self.backup), before)
        self.assertEqual((self.backup / "roster.md").read_text(), ROSTER)
        self.assertEqual(sorted(p.name for p in self.squads.iterdir()), ["t"])  # auto-detect sees one squad
        self.assertNotIn("WARNING", r.stdout)

    def test_dry_run_prints_every_move_and_changes_nothing(self):
        self.make_flat()
        before = self.tree()
        r = self.migrate("--to", "per-scope", "--scope", "board", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.tree(), before)
        self.assertFalse(self.backup.exists())
        self.assertIn(f"would copy {self.squad} -> {self.backup}", r.stdout)
        for f in ("roster.md", "escalations.md", "messages.jsonl", "activity.jsonl", "usage-events.jsonl", "iterations", "roles",
                  "evidence", "contracts", "work"):
            self.assertIn(f"would move   {f} -> scopes/board/{f}", r.stdout)
        self.assertIn("would move   goal.md -> scopes/board/legacy/goal.md", r.stdout)
        self.assertIn("would move   scopes.md -> scopes/board/legacy/scopes.md", r.stdout)
        self.assertIn("would write  scopes/board/scope.md", r.stdout)
        self.assertIn("would copy", r.stdout)

    def test_refuses_when_the_scope_exists_and_changes_nothing(self):
        self.make_flat()
        (self.squad / "scopes" / "board").mkdir(parents=True)
        before = self.tree()
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already exists", r.stderr)
        self.assertEqual(self.tree(), before)
        self.assertFalse(self.backup.exists())

    def test_an_existing_backup_is_never_overwritten(self):
        self.make_flat()
        self.backup.mkdir(parents=True)
        (self.backup / "keep").write_text("old backup")
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.backup / "keep").read_text(), "old backup")
        self.assertEqual((self.backup.parent / f"t-{datetime.date.today()}-2" / "roster.md").read_text(), ROSTER)

    def test_no_backup_flag_makes_none(self):
        self.make_flat()
        r = self.migrate("--to", "per-scope", "--scope", "board", "--no-backup")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([p.name for p in self.squads.iterdir()], ["t"])

    def test_refuses_a_squad_that_is_already_per_scope(self):
        (self.squad / "process.md").write_text("p")
        (self.squad / "scopes" / "a").mkdir(parents=True)
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already per-scope", r.stderr)

    def test_a_per_scope_squad_with_root_logs_is_not_touched(self):
        (self.squad / "process.md").write_text("p")
        (self.squad / "scopes" / "a").mkdir(parents=True)
        for f in ("messages.jsonl", "activity.jsonl", "usage-events.jsonl"):
            (self.squad / f).write_text("{}\n")
        before = self.tree()
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.tree(), before)

    def test_no_size_row_and_no_bold_line_still_give_a_valid_scope_md(self):
        self.make_flat()
        (self.squad / "scopes.md").unlink()
        (self.squad / "goal.md").write_text("# Goal\n\nplain words\n")
        r = self.migrate("--to", "per-scope", "--scope", "board")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = (self.squad / "scopes" / "board" / "scope.md").read_text()
        self.assertIn("size:\n", text)
        self.assertIn("Migrated from the flat layout", text)
        self.assertFalse((self.squad / "scopes" / "board" / "legacy" / "scopes.md").exists())

    def test_missing_folders_are_created_empty_and_tasks_move_when_present(self):
        (self.squad / "process.md").write_text("p")
        (self.squad / "roster.md").write_text(ROSTER)
        (self.squad / "tasks").mkdir()
        (self.squad / "tasks" / "T1.md").write_text("t")
        r = self.migrate("--to", "per-scope", "--scope", "lone")
        self.assertEqual(r.returncode, 0, r.stderr)
        sc = self.squad / "scopes" / "lone"
        for d in ("iterations", "roles", "evidence", "contracts", "work"):
            self.assertTrue((sc / d).is_dir(), d)
        self.assertEqual((sc / "tasks" / "T1.md").read_text(), "t")

    def test_bad_arguments(self):
        self.make_flat()
        self.assertEqual(self.migrate("--to", "per-scope").returncode, 2)
        self.assertEqual(self.migrate("--scope", "board").returncode, 2)
        self.assertEqual(self.migrate("--to", "per-scope", "--scope", "Bad Name").returncode, 2)
        self.assertEqual(self.migrate("--to", "per-scope", "--scope", "a", "--scope-to-goal", "a", "--goal", "g").returncode, 2)


class ScopeToGoalTest(Base):
    def setUp(self):
        super().setUp()
        self.make_flat()
        r = self.migrate("--to", "per-scope", "--scope", "board", "--no-backup")
        assert r.returncode == 0, r.stderr
        self.scope = self.squad / "scopes" / "board"
        (self.scope / "scope.md").write_text("# Scope: board\n\n**Build it.**\n\ngoal:\ntouches: bin, tests\nsize: S\n")

    def test_makes_the_goal_and_moves_the_manager_row(self):
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq")
        self.assertEqual(r.returncode, 0, r.stderr)
        g = self.squad / "goals" / "sq"
        for f in ("goal.md", "roster.md", "escalations.md", "shared/decisions.md"):
            self.assertTrue((g / f).is_file(), f)
        self.assertTrue((g / "shared" / "summaries").is_dir())
        goal_md = (g / "goal.md").read_text()
        self.assertIn("# Goal: sq", goal_md)
        self.assertIn("**Build it.**", goal_md)
        self.assertIn("touches: bin, tests", goal_md)
        self.assertIn("| board | none | open |", goal_md)
        self.assertNotIn("{{", goal_md)
        self.assertIn("goal: sq\n", (self.scope / "scope.md").read_text())
        self.assertIn("touches: bin, tests", (self.scope / "scope.md").read_text())

        goal_roster = (g / "roster.md").read_text()
        self.assertIn(ROWS[0], goal_roster)
        self.assertNotIn(ROWS[1], goal_roster)
        scope_roster = (self.scope / "roster.md").read_text()
        self.assertNotIn(ROWS[0], scope_roster)
        self.assertEqual(scope_roster, ROSTER.replace(ROWS[0] + "\n", ""))  # every other line, byte for byte
        self.assertIn("all there", r.stdout)
        self.assertIn("Manager rows moved to the goal roster: 1", r.stdout)

    def test_squad_close_scope_would_now_leave_the_manager(self):
        self.migrate("--scope-to-goal", "board", "--goal", "sq")
        roles = [cells.split("|")[2].strip().lower() for cells in (self.scope / "roster.md").read_text().splitlines()
                 if cells.startswith("| ") and "Role" not in cells and "---" not in cells]
        self.assertNotIn("manager", roles)

    def test_dry_run_changes_nothing(self):
        before = self.tree()
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.tree(), before)
        self.assertEqual((self.scope / "roster.md").read_text(), ROSTER)
        self.assertIn("would write  goals/sq/roster.md", r.stdout)
        self.assertIn("would write  scopes/board/roster.md", r.stdout)
        self.assertIn("would write  scopes/board/scope.md", r.stdout)
        self.assertFalse(self.backup.exists())

    def test_backup_made_before_changes(self):
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.backup / "scopes" / "board" / "roster.md").read_text(), ROSTER)
        self.assertFalse((self.backup / "goals").exists())

    def test_refuses_when_the_goal_exists(self):
        (self.squad / "goals" / "sq").mkdir(parents=True)
        before = self.tree()
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already exists", r.stderr)
        self.assertEqual(self.tree(), before)
        self.assertEqual((self.scope / "roster.md").read_text(), ROSTER)

    def test_refuses_a_goal_name_that_is_a_scope_and_a_scope_already_in_a_goal(self):
        r = self.migrate("--scope-to-goal", "board", "--goal", "board")
        self.assertNotEqual(r.returncode, 0)
        (self.scope / "scope.md").write_text("# Scope\n\ngoal: other\n")
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already belongs", r.stderr)

    def test_scope_without_a_manager_row_warns_and_leaves_the_roster(self):
        (self.scope / "roster.md").write_text(HEAD + ROWS[1] + "\n")
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING: no Manager row", r.stdout)
        self.assertEqual((self.scope / "roster.md").read_text(), HEAD + ROWS[1] + "\n")

    def test_scope_md_without_a_goal_line_gets_one(self):
        (self.scope / "scope.md").write_text("# Scope: board\n\n**Build it.**\n\ntouches: bin\n")
        r = self.migrate("--scope-to-goal", "board", "--goal", "sq")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("goal: sq\ntouches: bin", (self.scope / "scope.md").read_text())

    def test_missing_scope(self):
        r = self.migrate("--scope-to-goal", "nope", "--goal", "sq")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no scope nope", r.stderr)


if __name__ == "__main__":
    unittest.main()
