"""squad-start: text in, scope or goal folder + brief + fresh Manager out."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-start"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
if [[ "$1 $2" == "agent get" ]]; then echo '{"error":{"code":"agent_not_found"}}'; exit 1; fi
[[ $1 == tab ]] && echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}'
exit 0
"""


class StartTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / ".claude" / "squads" / "t"
        (self.squad / "scopes").mkdir(parents=True)
        (self.squad / "goals").mkdir()
        (self.squad / "process.md").write_text("x")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def start(self, *args):
        return subprocess.run([str(SCRIPT), *args], env=self.env, text=True, capture_output=True, timeout=30)

    def herdr(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_lone_task_creates_the_scope_folder_brief_and_a_fresh_manager(self):
        r = self.start("Fix SEC-04: remove the committed default bypass key", "--touches", "wpapi")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["kind"], out["name"], out["manager"]), ("scope", "sec04", "t-mgr-sec04"))
        sc = self.squad / "scopes" / "sec04"
        brief = (sc / "scope.md").read_text()
        self.assertIn("Fix SEC-04: remove the committed default bypass key", brief)
        self.assertRegex(brief, r"(?m)^touches: wpapi$")
        self.assertRegex(brief, r"(?m)^goal:\s*$")
        for d in ("iterations", "tasks", "evidence", "roles"):
            self.assertTrue((sc / d).is_dir(), d)
        self.assertTrue((sc / "escalations.md").exists())
        h = self.herdr()
        self.assertIn("--label t-mgr-sec04", h)
        self.assertIn(f"SCOPE_DIR={sc}", h)
        self.assertIn("scope.md", next(l for l in h.splitlines() if l.startswith("agent prompt")))
        self.assertIn("| t-mgr-sec04 | manager | sec04 |", (sc / "roster.md").read_text())

    def test_model_flag_sets_the_managers_model_else_the_role_default_applies(self):
        self.assertEqual(self.start("Task one", "--name", "one", "--touches", "a", "--model", "sonnet", "--effort", "high").returncode, 0)
        self.assertRegex(self.herdr(), r"--model sonnet --effort high\b")
        self.log.unlink()
        self.assertEqual(self.start("Task two", "--name", "two", "--touches", "b").returncode, 0)
        self.assertRegex(self.herdr(), r"--model opus\b")

    def test_name_comes_from_a_ticket_id_else_a_short_slug_and_can_be_overridden(self):
        self.assertEqual(json.loads(self.start("Regroup the settings tabs", "--touches", "x").stdout)["name"], "regroup-settings")
        self.assertEqual(json.loads(self.start("Anything", "--name", "mine", "--touches", "y").stdout)["name"], "mine")

    def test_goal_prefix_creates_a_goal_folder_and_a_goal_manager(self):
        r = self.start("goal: Rebuild the settings page", "--name", "settings", "--touches", "wpfe")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["kind"], out["name"], out["manager"]), ("goal", "settings", "t-mgr-settings"))
        g = self.squad / "goals" / "settings"
        self.assertIn("Rebuild the settings page", (g / "goal.md").read_text())
        self.assertNotIn("goal:", (g / "goal.md").read_text().splitlines()[2])  # the prefix is not part of the brief
        for p in ("shared/decisions.md", "shared/summaries", "shared/contracts", "roles", "roster.md", "escalations.md"):
            self.assertTrue((g / p).exists(), p)
        self.assertIn(f"GOAL_DIR={g}", self.herdr())
        self.assertNotIn("SCOPE_DIR", self.herdr())
        self.assertIn("| t-mgr-settings | manager |", (g / "roster.md").read_text())

    def test_in_goal_creates_only_the_scope_folder_naming_its_goal(self):
        self.start("goal: Rebuild", "--name", "g1", "--touches", "wpfe")
        self.log.unlink()
        r = self.start("Tabs regroup", "--in-goal", "g1", "--name", "s1", "--touches", "wpfe/tabs", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex((self.squad / "scopes" / "s1" / "scope.md").read_text(), r"(?m)^goal: g1$")
        self.assertNotIn("agent start", self.herdr())  # the goal Manager runs it, no Manager of its own (only the board lookup runs)
        self.assertEqual(json.loads(r.stdout)["manager"], None)

    def test_in_goal_needs_an_existing_goal(self):
        self.assertNotEqual(self.start("x", "--in-goal", "nope", "--name", "s1").returncode, 0)

    def test_name_clash_with_a_scope_a_goal_or_an_archived_one_is_refused(self):
        self.start("one", "--name", "dup", "--touches", "a")
        self.log.unlink()
        for existing in ("scopes/dup", "goals/dup", "scopes/_done/dup", "goals/_done/dup"):
            with self.subTest(existing=existing):
                p = self.squad / existing
                p.mkdir(parents=True, exist_ok=True)
                kind = ["goal: two"] if existing.startswith("scopes") else ["two"]
                r = self.start(*kind, "--name", "dup", "--touches", "b")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("already", r.stderr)
                self.assertEqual(self.herdr(), "")

    def test_overlap_with_an_open_scope_warns_and_creates_nothing_until_yes(self):
        self.start("first", "--name", "one", "--touches", "wpfe/src/settings")
        self.log.unlink()
        r = self.start("second", "--name", "two", "--touches", "wpfe")
        self.assertEqual(r.returncode, 3)
        self.assertIn("one", r.stderr)
        self.assertFalse((self.squad / "scopes" / "two").exists())
        self.assertEqual(self.herdr(), "")
        r = self.start("second", "--name", "two", "--touches", "wpfe", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_disjoint_touches_and_archived_scopes_do_not_count_as_overlap(self):
        self.start("first", "--name", "one", "--touches", "wpapi")
        done = self.squad / "scopes" / "_done" / "old"
        done.mkdir(parents=True)
        (done / "scope.md").write_text("touches: wpfe\n")
        self.assertEqual(self.start("second", "--name", "two", "--touches", "wpfe").returncode, 0)

    def test_a_flat_squad_is_refused_so_it_is_not_converted_by_accident(self):
        (self.squad / "scopes").rmdir()
        (self.squad / "goals").rmdir()
        (self.squad / "roster.md").write_text("| Agent |\n|---|\n")
        r = self.start("x", "--name", "one")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("flat", r.stderr)

    def test_a_manager_name_over_32_characters_is_refused(self):
        r = self.start("x", "--name", "a" * 30)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--name", r.stderr)

    def test_failed_spawn_rolls_the_new_folder_back(self):
        self.env["HERDR_ENV"] = "0"
        r = self.start("x", "--name", "one", "--touches", "z")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.squad / "scopes" / "one").exists())

    def test_resume_starts_a_new_manager_for_an_existing_scope_without_touching_its_files(self):
        self.start("Fix it", "--name", "one", "--touches", "a")
        sc = self.squad / "scopes" / "one"
        (sc / "tasks" / "T-1.md").write_text("keep me")
        self.log.unlink()
        r = self.start("--resume", "one")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["manager"], "t-mgr-one")
        self.assertEqual((sc / "tasks" / "T-1.md").read_text(), "keep me")
        h = self.herdr()
        self.assertIn(f"SCOPE_DIR={sc}", h)
        prompt = next(l for l in h.splitlines() if l.startswith("agent prompt"))
        self.assertIn("RESPAWN", prompt)
        self.assertIn("roles/t-mgr-one.notes.md", prompt)

    def test_resume_a_goal_uses_goal_dir(self):
        self.start("goal: Rebuild", "--name", "g1", "--touches", "wpfe")
        self.log.unlink()
        r = self.start("--resume", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"GOAL_DIR={self.squad / 'goals' / 'g1'}", self.herdr())

    def test_resume_refuses_a_scope_that_belongs_to_a_goal_unknown_names_and_extra_text(self):
        self.start("goal: Rebuild", "--name", "g1", "--touches", "wpfe")
        self.start("Tabs", "--in-goal", "g1", "--name", "s1", "--touches", "wpfe/tabs", "--yes")
        r = self.start("--resume", "s1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("g1", r.stderr)
        self.assertNotEqual(self.start("--resume", "nope").returncode, 0)
        self.assertNotEqual(self.start("text", "--resume", "g1").returncode, 0)

    def test_dry_run_creates_nothing(self):
        r = self.start("x", "--name", "one", "--touches", "z", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.squad / "scopes" / "one").exists())
        self.assertEqual(self.herdr(), "")
        self.assertIn("would", r.stdout)


class WorkspaceRenameTest(unittest.TestCase):
    """squad-start names the caller's herdr workspace after the goal or lone scope; failures never stop the start."""

    def setUp(self):
        StartTest.setUp(self)
        self.env["HERDR_WORKSPACE_ID"] = "wK"

    tearDown = StartTest.tearDown
    start = StartTest.start
    herdr = StartTest.herdr

    def renames(self):
        return [l for l in self.herdr().splitlines() if l.startswith("workspace rename")]

    def fake(self, extra):
        f = Path(self.tmp.name) / "fakebin" / "herdr"
        f.write_text(FAKE_HERDR.replace("exit 0\n", "") + extra + "\nexit 0\n")

    def test_a_lone_scope_names_the_workspace_after_the_scope(self):
        self.assertEqual(self.start("Task one", "--name", "one", "--touches", "a").returncode, 0)
        self.assertEqual(self.renames(), ["workspace rename wK one"])

    def test_a_goal_names_the_workspace_after_the_goal(self):
        self.start("goal: Big", "--name", "g1", "--touches", "a")
        self.assertEqual(self.renames(), ["workspace rename wK g1"])

    def test_a_scope_in_a_goal_leaves_the_name_alone(self):
        self.start("goal: Big", "--name", "g1", "--touches", "a")
        self.log.unlink()
        self.start("Part", "--in-goal", "g1", "--name", "p1", "--touches", "b")
        self.assertEqual(self.renames(), [])

    def test_resume_renames_to_the_resumed_name(self):
        self.start("goal: Big", "--name", "g1", "--touches", "a")
        self.start("Task one", "--name", "one", "--touches", "b")
        self.log.unlink()
        self.start("--resume", "one")
        self.start("--resume", "g1")
        self.assertEqual(self.renames(), ["workspace rename wK one", "workspace rename wK g1"])

    def test_two_starts_in_a_row_each_rename(self):
        self.start("Task one", "--name", "one", "--touches", "a")
        self.start("Task two", "--name", "two", "--touches", "b")
        self.assertEqual(self.renames(), ["workspace rename wK one", "workspace rename wK two"])

    def test_dry_run_renames_nothing(self):
        self.start("x", "--name", "one", "--dry-run")
        self.start("x", "--name", "one", "--touches", "a")
        self.log.unlink()
        self.start("--resume", "one", "--dry-run")
        self.assertEqual(self.renames(), [])

    def test_without_a_workspace_id_nothing_is_run_and_nothing_is_said(self):
        del self.env["HERDR_WORKSPACE_ID"]
        r = self.start("x", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.renames(), [])
        self.assertNotIn("workspace", r.stderr)

    def test_outside_herdr_the_rename_is_never_reached(self):
        # spawn itself needs HERDR_ENV=1, so a start outside herdr dies before the rename; the guard is in name_workspace
        self.env["HERDR_ENV"] = "0"
        self.start("x", "--name", "one", "--touches", "a")
        self.assertEqual(self.renames(), [])

    def test_a_refusing_herdr_gives_one_warning_and_the_start_goes_on(self):
        self.fake('[[ "$1 $2" == "workspace rename" ]] && { echo "no such workspace" >&2; exit 1; }')
        r = self.start("Task one", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["manager"], "t-mgr-one")
        self.assertEqual(r.stderr.strip().splitlines().count("workspace not renamed: no such workspace"), 1)
        self.assertTrue((self.squad / "scopes" / "one" / "scope.md").exists())

    def test_a_failed_manager_start_does_not_rename(self):
        self.fake('[[ $1 == tab ]] && exit 1')
        r = self.start("x", "--name", "one", "--touches", "a")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.renames(), [])


BOARD_HERDR = r"""#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "tab list") echo '{"result":{"tabs":[]}}' ;;
  "tab create") echo '{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}' ;;
  "pane run") ;;
  "pane wait-output") [[ ${FAKE_BOARD:-up} == up ]] || exit 1 ;;
  "pane read") if [[ ${FAKE_BOARD:-up} == up ]]; then echo "squad-board: http://127.0.0.1:7420/?token=abc_DEF-1"; else echo "port busy"; fi ;;
  "agent get") echo '{"error":{"code":"agent_not_found"}}'; exit 1 ;;
esac
exit 0
"""


class BoardTest(unittest.TestCase):
    """squad-start also opens the board; a board that fails never stops the Manager."""

    def setUp(self):
        StartTest.setUp(self)
        (Path(self.tmp.name) / "fakebin" / "herdr").write_text(BOARD_HERDR)

    tearDown = StartTest.tearDown
    start = StartTest.start
    herdr = StartTest.herdr

    def test_the_url_is_in_the_json(self):
        r = self.start("Task one", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["board"], "http://127.0.0.1:7420/?token=abc_DEF-1")
        self.assertIn("--label board", self.herdr())

    def test_a_board_that_fails_leaves_the_manager_running(self):
        self.env["FAKE_BOARD"] = "down"
        r = self.start("Task one", "--name", "one", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertIsNone(out["board"])
        self.assertEqual(out["manager"], "t-mgr-one")
        self.assertIn("board not started:", r.stderr)
        self.assertIn("run /squad:squad-board", r.stderr)
        self.assertTrue((self.squad / "scopes" / "one" / "scope.md").exists())
        self.assertIn("--label t-mgr-one", self.herdr())

    def test_dry_run_starts_no_board(self):
        r = self.start("Task one", "--name", "one", "--touches", "a", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("board", self.herdr())

    def test_resume_opens_it_too(self):
        self.start("Task one", "--name", "one", "--touches", "a")
        r = self.start("--resume", "one")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["board"], "http://127.0.0.1:7420/?token=abc_DEF-1")

    def test_a_scope_in_a_goal_makes_the_idempotent_call_too(self):
        self.start("goal: Big", "--name", "g1", "--touches", "z")
        r = self.start("Part", "--in-goal", "g1", "--name", "p1", "--touches", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["board"], "http://127.0.0.1:7420/?token=abc_DEF-1")


if __name__ == "__main__":
    unittest.main()
