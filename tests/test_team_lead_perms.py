"""Team Lead permissions: exact settings allow set, and the squad-spawn / squad-retire role gates."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import winlaunch
from squadtest import BIN, ROOT, clean_env, fake_herdr

SETTINGS = ROOT / "templates" / "squad" / "settings" / "team-lead.json"
TL_ALLOW = {
    "SendMessage", "ListAgents", "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
    "Bash(git branch:*)", "Bash(echo:*)", "Bash(squad-respawn:*)",
    "Bash(squad-spawn dev:*)", "Bash(squad-spawn ba:*)", "Bash(squad-spawn tech-lead:*)", "Bash(squad-spawn qa-whitebox:*)",
    "Bash(squad-spawn qa-blackbox:*)", "Bash(squad-spawn designer:*)", "Bash(squad-spawn architect:*)", "Bash(squad-retire:*)", "Bash(squad-process rule:*)", "Bash(squad-process who:*)", "Bash(herdr agent list:*)", "Bash(herdr agent get:*)",
    "Bash(herdr agent read:*)",
    "Bash(rm /tmp/*)", "Bash(rm -r /tmp/*)", "Bash(rm -rf /tmp/*)", "Bash(rmdir /tmp/*)",
    "Read(//tmp/**)", "Edit(//tmp/**)", "Write(//tmp/**)", "Bash(squad-tmp:*)",
}
ROSTER = """| Agent | Role | Scope | Owns | Status | Session |
| --- | --- | --- | --- | --- | --- |
| mgr | Manager | s | x | live | a |
| dev-1 | dev | s | x | live | b |
| tl | team-lead | s | x | live | c |
| qaw | QA Whitebox | s | x | live | d |
| qab | qa-blackbox | s | x | live | e |
| coach | token-coach | s | x | live | f |
| tl2 | team-lead | s | x | live | g |
| ba-1 | ba | s | x | live | h |
"""


class SettingsTest(unittest.TestCase):
    def test_allow_set_is_exact_and_git_risks_ask(self):
        cfg = json.loads(SETTINGS.read_text())["permissions"]
        self.assertEqual(set(cfg["allow"]), TL_ALLOW)
        self.assertEqual(len(cfg["allow"]), len(TL_ALLOW))
        for d in ("git push", "git merge", "git rebase", "git reset --hard", "git checkout main", "git checkout dev", "git branch -D"):
            self.assertIn(f"Bash({d}:*)", cfg["ask"])
        self.assertFalse([d for d in cfg["deny"] if d.startswith("Bash(git")])


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.squad = root / ".claude" / "squads" / "t"
        self.scope = self.squad / "scopes" / "s"
        self.scope.mkdir(parents=True)
        (self.squad / "process.md").write_text("x")
        (self.scope / "scope.md").write_text("team: ba, team-lead, tech-lead, qa-white, qa-black, designer, architect\n")
        (self.scope / "roster.md").write_text(ROSTER)
        fake = root / "fakebin"
        fake.mkdir()
        fake_herdr(fake)
        self.panes = root / "panes"
        self.panes.write_text("p1 t1 mgr\np2 t2 dev-1\np3 t3 tl\np4 t4 ghost\np5 t5 qaw\np6 t6 qab\np7 t7 coach\np8 t8 tl2\np9 t9 ba-1\n")
        self.env = clean_env()
        self.env.update(HERDR_ENV="1", HERDR_LOG=str(root / "herdr.log"), PANES=str(self.panes),
                        SQUAD_DIR=str(self.squad), SCOPE_DIR=str(self.scope), PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def run_bin(self, role, *argv, prog="squad-spawn", **env):
        e = {**self.env, **({"SQUAD_ROLE": role} if role else {}), **env}
        return winlaunch.run_script(BIN / prog, [*argv], env=e, text=True, capture_output=True, timeout=20)

    def spawn(self, role, target, *args):
        return self.run_bin(role, target, "x", "--scope", "s", "--dry-run", *args)

    def alive(self):
        return [l.split()[2] for l in self.panes.read_text().splitlines()]

    def test_team_lead_spawns_every_pod_role(self):
        for target in ("dev", "ba", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "architect"):
            with self.subTest(target=target):
                self.assertEqual(self.spawn("team-lead", target).returncode, 0)

    def test_team_lead_cannot_spawn_the_three_never_roles(self):
        for target in ("manager", "token-coach", "team-lead"):
            with self.subTest(target=target):
                r = self.spawn("team-lead", target)
                self.assertEqual(r.returncode, 2)
                self.assertIn(f"a Team Lead may not spawn", r.stderr)
                self.assertIn(target, r.stderr)
                self.assertNotIn("may only", r.stderr)
                self.assertEqual(r.stdout, "")
                self.assertFalse((self.scope / "labels").exists())

    def test_team_lead_name_must_match_its_roster_row(self):
        r = self.run_bin("team-lead", "qa-whitebox", "mgr", "--scope", "s", "--dry-run")
        self.assertEqual(r.returncode, 2)
        self.assertIn("qa-whitebox", r.stderr)
        self.assertIn("manager", r.stderr)  # row written `Manager`: normalised
        self.assertFalse((self.scope / "labels").exists())
        self.assertFalse(Path(self.env["HERDR_LOG"]).exists())
        (self.squad / "goals" / "g").mkdir(parents=True)
        (self.squad / "goals" / "g" / "roster.md").write_text(ROSTER)
        r = self.run_bin("team-lead", "qa-whitebox", "mgr", "--goal", "g", "--dry-run")
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.scope / "labels").exists())
        self.assertFalse(Path(self.env["HERDR_LOG"]).exists())
        for name in ("qab", "qaw", "fresh-name"):  # row says qa-blackbox for qab: respawn case needs the same role
            role = "qa-blackbox" if name == "qab" else "qa-whitebox"
            with self.subTest(name=name):
                self.assertEqual(self.run_bin("team-lead", role, name, "--scope", "s", "--dry-run").returncode, 0)

    def test_team_lead_spawn_refuses_when_roster_is_missing(self):
        (self.scope / "roster.md").unlink()
        r = self.spawn("team-lead", "qa-whitebox")
        self.assertEqual(r.returncode, 2)
        self.assertIn("roster.md", r.stderr)
        self.assertFalse((self.scope / "labels").exists())

    def test_team_lead_role_not_on_team_is_refused_by_the_team_gate(self):
        (self.scope / "scope.md").write_text("team: team-lead, tech-lead\n")
        r = self.spawn("team-lead", "ba")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not on the team", r.stderr)
        self.assertFalse((self.scope / "labels").exists())

    def test_team_lead_may_respawn_itself_but_not_spawn_never_roles_under_other_names(self):
        r = self.run_bin("team-lead", "team-lead", "tl", "--scope", "s", "--dry-run", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_bin("team-lead", "tl", "--dry-run", prog="squad-respawn", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad-spawn team-lead tl", r.stdout)
        for target in ("manager", "token-coach", "team-lead"):
            with self.subTest(target=target):
                r = self.run_bin("team-lead", target, "other", "--scope", "s", "--dry-run", SQUAD_NAME="tl")
                self.assertEqual(r.returncode, 2)
        # own name does not unlock another role
        r = self.run_bin("team-lead", "manager", "tl", "--scope", "s", "--dry-run", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 2)

    def test_refusal_has_no_side_effect(self):
        self.spawn("team-lead", "manager")
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

    def test_retire_refuses_never_roles_and_missing_row(self):
        for target in ("mgr", "coach", "tl", "tl2", "ghost"):
            with self.subTest(target=target):
                r = self.run_bin("team-lead", target, "--no-notes", prog="squad-retire")
                self.assertEqual(r.returncode, 2)
                self.assertIn("may not retire", r.stderr)
                self.assertIn(target, self.alive())

    def test_retire_closes_every_pod_role(self):
        for target in ("dev-1", "ba-1", "qaw", "qab"):  # qaw's row is written `QA Whitebox`
            with self.subTest(target=target):
                r = self.run_bin("team-lead", target, "--no-notes", prog="squad-retire")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn(target, self.alive())

    def test_respawn_refuses_never_roles_without_event_or_rename(self):
        (self.scope / "roles").mkdir()
        for target in ("mgr", "coach", "tl2"):
            (self.scope / "roles" / f"{target}.notes.md").write_text("n\n")
        for target in ("mgr", "coach", "tl2"):
            with self.subTest(target=target):
                r = self.run_bin("team-lead", target, prog="squad-respawn", SQUAD_NAME="tl")
                self.assertEqual(r.returncode, 2)
                self.assertFalse((self.scope / "usage-events.jsonl").exists())
                self.assertNotIn("rename", Path(self.env["HERDR_LOG"]).read_text() if Path(self.env["HERDR_LOG"]).exists() else "")
        r = self.run_bin("team-lead", "qaw", "--dry-run", prog="squad-respawn", SQUAD_NAME="tl")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("squad-spawn qa-whitebox qaw", r.stdout)

    def test_retire_unchanged_for_manager_and_developer(self):
        for caller, target in (("manager", "tl"), ("dev", "ghost")):
            with self.subTest(caller=caller):
                r = self.run_bin(caller, target, "--no-notes", prog="squad-retire")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn(target, self.alive())


if __name__ == "__main__":
    unittest.main()
