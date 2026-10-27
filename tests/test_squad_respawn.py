"""squad-respawn: same name, role, scope and worktree; new session id in roster.md; old pane closed last."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
_DEV = json.loads((BIN.parent / "templates/squad/settings/dev.json").read_text(encoding="utf-8"))
DEV = (_DEV["model"], _DEV["effortLevel"])
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get")
    if grep -q "^agent rename $3 " "$HERDR_LOG"; then echo '{"error":{"code":"agent_not_found"}}'; exit 1; fi
    echo '{"result":{"agent":{"pane_id":"p-old"}}}' ;;
  "tab create") echo '{"result":{"root_pane":{"pane_id":"p-new"},"tab":{"tab_id":"t-new"}}}' ;;
esac
exit 0
"""


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


class RespawnTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.squad = self.root / ".claude" / "squads" / "t"
        self.squad.mkdir(parents=True)
        (self.squad / "process.md").write_text("x", encoding="utf-8")
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| manager | Manager | all | x | live | |\n| dev-1 | Dev | settings | task 1 | live | old-sid |\n", encoding="utf-8")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8")
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def respawn(self, *args):
        return subprocess.run([str(BIN / "squad-respawn"), "dev-1", *args], env=self.env,
                              text=True, encoding="utf-8", capture_output=True, timeout=20)

    def test_dev_keeps_worktree_and_branch_and_roster_gets_new_session(self):
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "t" / "dev-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/t/dev-1", cwd=repo)
        (wt / "wip.txt").write_text("uncommitted", encoding="utf-8")

        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)

        log = self.log.read_text(encoding="utf-8").splitlines()
        self.assertIn(f"tab create --cwd {wt} --label 🤖 Dev --no-focus", " ".join(log))
        self.assertTrue(any(re.fullmatch(r"agent rename dev-1 prev-\d+", l) for l in log))
        self.assertEqual(log[-1], "pane close p-old")  # old pane goes last
        start = next(l for l in log if l.startswith("agent start dev-1"))
        self.assertIn("--agent squad:dev", start)
        self.assertIn(f"--model {DEV[0]} --effort {DEV[1]}", start)  # from settings/dev.json
        sid = re.search(r"--session-id (\S+)", start).group(1)
        self.assertIn(f"| dev-1 | Dev | settings | task 1 | live | {sid} |", (self.squad / "roster.md").read_text(encoding="utf-8"))
        prompt = next(l for l in log if l.startswith("agent prompt"))
        self.assertIn("roles/dev-1.notes.md", prompt)

        self.assertEqual((wt / "wip.txt").read_text(encoding="utf-8"), "uncommitted")
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=wt, text=True, encoding="utf-8", capture_output=True).stdout.strip()
        self.assertEqual(branch, "squad/t/dev-1")
        self.assertFalse(any("worktree add" in l for l in log))

    def test_agent_without_worktree_respawns_in_project_dir(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"tab create --cwd {self.root} --label 🤖 Dev", self.log.read_text(encoding="utf-8"))

    def test_manager_row_as_written_by_squad_spawn_respawns_with_role_and_notes(self):
        # squad-start spawns manager-t; squad-spawn --set-session adds this row (empty scope, empty Owns).
        with (self.squad / "roster.md").open("a", encoding="utf-8") as f:
            f.write("| manager-t | manager |  |  | live | old-sid |\n")
        r = subprocess.run([str(BIN / "squad-respawn"), "manager-t"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log.read_text(encoding="utf-8").splitlines()
        start = next(l for l in log if l.startswith("agent start manager-t"))
        self.assertIn("--agent squad:manager", start)
        sid = re.search(r"--session-id (\S+)", start).group(1)
        self.assertIn(f"| manager-t | manager |  |  | live | {sid} |", (self.squad / "roster.md").read_text(encoding="utf-8"))
        self.assertIn(f"tab create --cwd {self.root} --label 🦀 Manager", " ".join(log))
        self.assertIn("SQUAD_SCOPE=", " ".join(log))
        self.assertNotIn("SQUAD_SCOPE=old-sid", " ".join(log))  # an empty scope must not shift the columns
        self.assertEqual(log[-1], "pane close p-old")
        prompt = next(l for l in log if l.startswith("agent prompt"))
        self.assertIn("roles/manager-t.notes.md", prompt)

    def dry_prompt(self, agent, role):
        with (self.squad / "roster.md").open("a", encoding="utf-8") as f:
            f.write(f"| {agent} | {role} |  |  | live | old-sid |\n")
        r = subprocess.run([str(BIN / "squad-respawn"), agent, "--dry-run"], env=self.env,
                           text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_legacy_prompt_names_the_notes_and_neither_process_md_nor_show(self):
        for agent, role in (("d2", "Dev"), ("w1", "QA whitebox"), ("b1", "QA blackbox"), ("ux", "Designer"),
                            ("m1", "Manager"), ("t1", "Tech Lead"), ("l1", "Team Lead")):
            out = self.dry_prompt(agent, role)
            self.assertIn(f"Read your notes $SQUAD_DIR/roles/{agent}.notes.md and continue from them.", out)
            self.assertNotIn("process.md", out)
            self.assertNotIn("show", out)

    def test_respawn_never_names_squad_process_show(self):
        self.assertNotIn("squad-process show", (BIN / "squad-respawn").read_text(encoding="utf-8"))
        self.assertNotIn("squad-process show", (BIN / "squad-spawn").read_text(encoding="utf-8"))

    def test_respawn_of_a_legacy_agent_reproduces_the_rules_attachment(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        rules = self.squad / "roles" / "dev-1.rules.md"
        start = next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent start dev-1"))
        self.assertIn(f"--append-system-prompt-file {rules}", start)
        self.assertNotIn("--plugin-dir", start)
        self.assertTrue(rules.read_text(encoding="utf-8").startswith("# Your process rules"))
        self.assertEqual(r.stderr.count("legacy squad: plugin rules attached"), 1)

    def test_respawn_brings_back_the_title_and_the_number(self):
        init = subprocess.run([str(BIN / "squad-label"), "--init", "--home", str(self.squad), "--agent", "dev-1",
                               "--role", "dev", "--title", "plan"], env=self.env, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(init.returncode, 0, init.stderr)
        self.log.write_text("", encoding="utf-8")
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--label 🤖 Dev · plan --no-focus", self.log.read_text(encoding="utf-8"))

    def test_an_agent_with_no_stored_entry_respawns_with_a_label_without_title(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(" · ", next(l for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("tab create")))

    def test_every_rename_argument_is_a_valid_herdr_name_even_for_a_32_character_agent(self):
        name = "squad-board-dev-squad-tabs-2xxxxx"[:32]
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            f"| {name} | Dev | settings | task | live | old-sid |\n", encoding="utf-8")
        r = subprocess.run([str(BIN / "squad-respawn"), name], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        renames = [l.split()[2:] for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent rename")]
        self.assertTrue(renames)
        for arg in (a for pair in renames for a in pair):
            self.assertRegex(arg, r"^[a-z][a-z0-9_-]{0,31}$")

    def test_a_failing_spawn_renames_the_old_agent_back(self):
        stub = self.root / "plugin"
        (stub / "bin").mkdir(parents=True)
        for f in ("squad-respawn", "squad-usage", "squad-label", "squadlabel.py", "squadio.py", "squadtranscript.py"):
            shutil.copy(BIN / f, stub / "bin" / f)
        (stub / "bin" / "squad-spawn").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (stub / "bin" / "squad-spawn").chmod(0o755)
        r = subprocess.run([str(stub / "bin" / "squad-respawn"), "dev-1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 1)
        renames = [l.split() for l in self.log.read_text(encoding="utf-8").splitlines() if l.startswith("agent rename")]
        self.assertEqual(renames[1][2:], [renames[0][3], "dev-1"])
        self.assertNotIn("pane close", self.log.read_text(encoding="utf-8"))

    def test_warns_when_notes_are_over_100_lines(self):
        (self.squad / "roles").mkdir()
        (self.squad / "roles" / "dev-1.notes.md").write_text("line\n" * 101, encoding="utf-8")
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("101 lines", r.stderr)

    def test_no_warning_for_short_notes(self):
        (self.squad / "roles").mkdir()
        (self.squad / "roles" / "dev-1.notes.md").write_text("line\n" * 30, encoding="utf-8")
        self.assertNotIn("lines", self.respawn().stderr)

    def scoped(self):
        """Turn the test squad into a per-scope squad with scope sc1 and goal g1."""
        head = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
        sc, g = self.squad / "scopes" / "sc1", self.squad / "goals" / "g1"
        sc.mkdir(parents=True)
        g.mkdir(parents=True)
        (sc / "scope.md").write_text("# Scope\n\ngoal:\nteam: ba\n", encoding="utf-8")
        (sc / "roster.md").write_text(head + "| t-dev-sc1-1 | dev | sc1 | task 1 | live | old-sid |\n", encoding="utf-8")
        (g / "roster.md").write_text(head + "| t-mgr-g1 | manager |  |  | live | old-g |\n", encoding="utf-8")
        self.env.update(SCOPE_DIR=str(sc))
        return sc, g

    def test_scope_agent_respawns_in_its_scope_worktree_with_scope_env(self):
        sc, _ = self.scoped()
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "t" / "sc1" / "t-dev-sc1-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/t/sc1/t-dev-sc1-1", cwd=repo)
        r = subprocess.run([str(BIN / "squad-respawn"), "t-dev-sc1-1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log.read_text(encoding="utf-8").splitlines()
        self.assertIn(f"tab create --cwd {wt} --label 🤖 Dev --no-focus", " ".join(log))
        self.assertIn(f"SCOPE_DIR={sc}", " ".join(log))
        self.assertFalse(any("worktree add" in l for l in log))
        sid = re.search(r"--session-id (\S+)", next(l for l in log if l.startswith("agent start"))).group(1)
        self.assertIn(f"| t-dev-sc1-1 | dev | sc1 | task 1 | live | {sid} |", (sc / "roster.md").read_text(encoding="utf-8"))
        self.assertIn("SCOPE_DIR/roles/t-dev-sc1-1.notes.md", next(l for l in log if l.startswith("agent prompt")))

    def test_goal_manager_respawns_with_goal_env(self):
        _, g = self.scoped()
        self.env.pop("SCOPE_DIR")
        self.env.update(GOAL_DIR=str(g))
        r = subprocess.run([str(BIN / "squad-respawn"), "t-mgr-g1"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = " ".join(self.log.read_text(encoding="utf-8").splitlines())
        self.assertIn(f"GOAL_DIR={g}", log)
        self.assertNotIn("SCOPE_DIR", log)
        self.assertIn("| t-mgr-g1 | manager |", (g / "roster.md").read_text(encoding="utf-8"))

    def test_flat_squad_finds_the_oldest_worktree_layout(self):
        # squad-board's early layout: .worktrees/<agent>, branch squad/<agent>
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "dev-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/dev-1", cwd=repo)
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log.read_text(encoding="utf-8")
        self.assertIn(f"tab create --cwd {wt} --label 🤖 Dev", log)
        self.assertNotIn("worktree add", log)

    def test_unknown_agent_fails(self):
        r = subprocess.run([str(BIN / "squad-respawn"), "ghost"], env=self.env, text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertNotEqual(r.returncode, 0)


class RespawnPinnedTest(RespawnTest):
    """D7: a scope pinned below 0.6.0 is respawned by the pin's own squad-respawn (its scope.md still says `size:`)."""

    def pinned(self, version="0.5.2", stub=True):
        sc, _ = self.scoped()
        (self.squad / "process.local.md").write_text("", encoding="utf-8")
        sha = "b" * 40
        rt = self.squad / "_runtime" / f"{version}-{sha[:12]}"
        (rt / ".claude-plugin").mkdir(parents=True)
        (rt / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "squad", "version": version}), encoding="utf-8")
        self.record = self.root / "stub.log"
        if stub:
            (rt / "bin").mkdir()
            (rt / "bin" / "squad-respawn").write_text(
                f'#!/usr/bin/env bash\necho "squad-respawn $* SCOPE_DIR=$SCOPE_DIR" >> "{self.record}"\n', encoding="utf-8")
            (rt / "bin" / "squad-respawn").chmod(0o755)
        (sc / "scope.md").write_text(f"# Scope\n\ngoal:\nsize: L\nqa-b: yes\nplugin: {version} {sha}\n", encoding="utf-8", newline="")
        return sc

    def run_respawn(self, *args, env=None):
        return subprocess.run([str(BIN / "squad-respawn"), "t-dev-sc1-1", *args], env=env or self.env, text=True,
                              encoding="utf-8", capture_output=True, timeout=20)

    def calls(self):
        return self.record.read_text(encoding="utf-8").splitlines() if self.record.exists() else []

    def test_pin_0_5_2_hands_off_from_the_po_shell_and_from_an_agent_session(self):
        sc = self.pinned()
        before = (sc / "scope.md").read_bytes()
        for env in (self.env, dict(self.env, SQUAD_NAME="t-dev-sc1-1", SQUAD_ROLE="dev")):
            self.assertEqual(self.run_respawn(env=env).returncode, 0)
        self.assertEqual(self.calls(), [f"squad-respawn t-dev-sc1-1 SCOPE_DIR={sc}"] * 2)
        self.assertFalse(self.log.exists())  # the new engine made no herdr call of its own
        self.assertEqual((sc / "scope.md").read_bytes(), before)

    def test_the_hand_off_passes_the_dry_run_flag(self):
        self.pinned()
        r = self.run_respawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would hand off to the pinned runtime", r.stdout)
        self.assertEqual(self.calls(), [])

    def test_a_runtime_without_squad_respawn_refuses_with_a_warning_and_renames_nothing(self):
        self.pinned(stub=False)
        r = self.run_respawn()
        self.assertEqual(r.returncode, 1)
        self.assertIn("warning:", r.stderr)
        self.assertIn("no bin/squad-respawn", r.stderr)
        self.assertFalse(self.log.exists())

    def test_pin_0_6_0_does_not_hand_off(self):
        sc = self.pinned("0.6.0")
        (sc / "scope.md").write_text("# Scope\n\ngoal:\nteam: ba\nplugin: 0.6.0 " + "b" * 40 + "\n", encoding="utf-8")
        r = self.run_respawn("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("hand off", r.stdout)
        self.assertEqual(self.calls(), [])

    def test_a_runtime_that_is_this_script_is_not_handed_to_again(self):
        self.pinned(stub=False)
        rt = next((self.squad / "_runtime").iterdir())
        (rt / "bin").mkdir()
        (rt / "bin" / "squad-respawn").symlink_to(BIN / "squad-respawn")
        r = self.run_respawn("--dry-run")
        self.assertNotIn("hand off", r.stdout)  # no exec loop: the guard falls through to the normal path


for _n in dir(RespawnTest):  # reuse the fixture only: the inherited tests run once, in RespawnTest
    if _n.startswith("test_") and _n not in RespawnPinnedTest.__dict__:
        setattr(RespawnPinnedTest, _n, None)


if __name__ == "__main__":
    unittest.main()
