"""Team Lead permissions: exact settings allow set, and the squad-spawn / squad-retire dev-only gates."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
SETTINGS = ROOT / "templates" / "squad" / "settings" / "team-lead.json"
TL_ALLOW = {
    "SendMessage", "ListAgents", "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
    "Bash(git branch:*)", "Bash(echo:*)", "Bash(squad-respawn:*)",
    "Bash(squad-spawn dev:*)", "Bash(squad-retire:*)", "Bash(squad-process rule:*)", "Bash(squad-process who:*)", "Bash(herdr agent list:*)", "Bash(herdr agent get:*)",
    "Bash(herdr agent read:*)",
    "Bash(rm /tmp/tmp.*)", "Bash(rm -r /tmp/tmp.*)", "Bash(rm -rf /tmp/tmp.*)", "Bash(rmdir /tmp/tmp.*)",
}
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get") row=$(awk -v n="$3" '$3 == n' "$PANES"); [[ -n $row ]] || exit 1
    read -r pane tab _ <<<"$row"; echo "{\\"result\\":{\\"agent\\":{\\"pane_id\\":\\"$pane\\"}}}" ;;
  "pane close") awk -v p="$3" '$1 != p' "$PANES" > "$PANES.new"; mv "$PANES.new" "$PANES" ;;
esac
exit 0
"""
ROSTER = """| Agent | Role | Scope | Owns | Status | Session |
| --- | --- | --- | --- | --- | --- |
| mgr | manager | s | x | live | a |
| dev-1 | dev | s | x | live | b |
| tl | team-lead | s | x | live | c |
"""


class SettingsTest(unittest.TestCase):
    def test_allow_set_is_exact_and_denies_are_kept(self):
        cfg = json.loads(SETTINGS.read_text())["permissions"]
        self.assertEqual(set(cfg["allow"]), TL_ALLOW)
        self.assertEqual(len(cfg["allow"]), len(TL_ALLOW))
        for d in ("git push", "git merge", "git rebase", "git reset --hard", "git checkout main", "git checkout dev"):
            self.assertIn(f"Bash({d}:*)", cfg["deny"])
        self.assertTrue(any("Atlassian" in d or "atlassian" in d for d in cfg["deny"]))


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.squad = root / ".claude" / "squads" / "t"
        self.scope = self.squad / "scopes" / "s"
        self.scope.mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        (self.scope / "scope.md").write_text("team: ba, team-lead, tech-lead, qa-white, qa-black\n")
        (self.scope / "roster.md").write_text(ROSTER)
        fake = root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.panes = root / "panes"
        self.panes.write_text("p1 t1 mgr\np2 t2 dev-1\np3 t3 tl\np4 t4 ghost\n")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", HERDR_LOG=str(root / "herdr.log"), PANES=str(self.panes),
                        SQUAD_DIR=str(self.squad), SCOPE_DIR=str(self.scope), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def run_bin(self, role, *argv, prog="squad-spawn", **env):
        e = {**self.env, **({"SQUAD_ROLE": role} if role else {}), **env}
        return subprocess.run([str(BIN / prog), *argv], env=e, text=True, capture_output=True, timeout=20)

    def spawn(self, role, target, *args):
        return self.run_bin(role, target, "x", "--scope", "s", "--dry-run", *args)

    def alive(self):
        return [l.split()[2] for l in self.panes.read_text().splitlines()]

    def test_team_lead_cannot_spawn_another_role(self):
        for target in ("manager", "tech-lead", "team-lead", "qa-whitebox", "qa-blackbox", "ba", "designer", "token-coach"):
            with self.subTest(target=target):
                r = self.spawn("team-lead", target)
                self.assertEqual(r.returncode, 2)
                self.assertIn("a Team Lead may only spawn dev", r.stderr)
                self.assertEqual(r.stdout, "")

    def test_team_lead_may_respawn_itself_but_not_spawn_others_under_other_names(self):
        r = self.run_bin("team-lead", "team-lead", "tl", "--scope", "s", "--dry-run", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_bin("team-lead", "tl", "--dry-run", prog="squad-respawn", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad-spawn team-lead tl", r.stdout)
        for target in ("manager", "tech-lead", "team-lead"):
            with self.subTest(target=target):
                r = self.run_bin("team-lead", target, "other", "--scope", "s", "--dry-run", SQUAD_NAME="tl")
                self.assertEqual(r.returncode, 2)
        # own name does not unlock another role
        r = self.run_bin("team-lead", "manager", "tl", "--scope", "s", "--dry-run", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 2)

    def test_refusal_has_no_side_effect(self):
        self.spawn("team-lead", "ba")
        self.assertFalse((self.scope / "labels").exists())
        self.assertFalse((self.env["HERDR_LOG"] and Path(self.env["HERDR_LOG"]).exists()))

    def test_team_lead_can_dry_run_a_dev_with_the_role_model_and_effort(self):
        repo = Path(self.tmp.name) / "repo"
        r = self.spawn("team-lead", "dev", "--repo", str(repo), "--base", "abc123", "--title", "T5 gates")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--model sonnet --effort medium", r.stdout)
        self.assertIn("abc123", r.stdout)
        self.assertIn("T5 gates", r.stdout)

    def test_other_callers_spawn_any_role(self):
        for caller in ("manager", "dev", ""):
            for target in ("dev", "qa-whitebox", "team-lead"):
                with self.subTest(caller=caller, target=target):
                    self.assertEqual(self.spawn(caller, target).returncode, 0)

    def test_retire_refuses_non_dev_and_missing_row(self):
        for target in ("mgr", "tl", "ghost"):
            with self.subTest(target=target):
                r = self.run_bin("team-lead", target, "--no-notes", prog="squad-retire")
                self.assertEqual(r.returncode, 2)
                self.assertIn("may only retire dev", r.stderr)
                self.assertIn(target, self.alive())

    def test_retire_closes_a_dev(self):
        r = self.run_bin("team-lead", "dev-1", "--no-notes", prog="squad-retire")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.alive(), ["mgr", "tl", "ghost"])

    def test_retire_unchanged_for_manager_and_developer(self):
        for caller, target in (("manager", "tl"), ("dev", "ghost")):
            with self.subTest(caller=caller):
                r = self.run_bin(caller, target, "--no-notes", prog="squad-retire")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn(target, self.alive())


if __name__ == "__main__":
    unittest.main()
