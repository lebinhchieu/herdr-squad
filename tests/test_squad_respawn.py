"""squad-respawn: same name, role, scope and worktree; new session id in roster.md; old tab closed last."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
FAKE_HERDR = """#!/usr/bin/env bash
echo "$@" >> "$HERDR_LOG"
case "$1 $2" in
  "agent get") echo '{"result":{"agent":{"tab_id":"t-old"}}}' ;;
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
        (self.squad / "process.md").write_text("x")
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| manager | Manager | all | x | live | |\n| dev-1 | Dev | settings | task 1 | live | old-sid |\n")
        fake = self.root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR)
        (fake / "herdr").chmod(0o755)
        self.log = self.root / "herdr.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD")}
        self.env.update(HERDR_ENV="1", SQUAD_DIR=str(self.squad), HERDR_LOG=str(self.log),
                        PATH=f"{fake}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def respawn(self, *args):
        return subprocess.run([str(BIN / "squad-respawn"), "dev-1", *args], env=self.env,
                              text=True, capture_output=True, timeout=20)

    def test_dev_keeps_worktree_and_branch_and_roster_gets_new_session(self):
        repo = self.root / "code"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        wt = self.root / ".worktrees" / "t" / "dev-1"
        git("worktree", "add", "-q", str(wt), "-b", "squad/t/dev-1", cwd=repo)
        (wt / "wip.txt").write_text("uncommitted")

        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)

        log = self.log.read_text().splitlines()
        self.assertIn(f"tab create --cwd {wt} --label dev-1 --no-focus", " ".join(log))
        self.assertTrue(any(l.startswith("agent rename dev-1 dev-1-prev") for l in log))
        self.assertEqual(log[-1], "tab close t-old")  # old tab goes last
        start = next(l for l in log if l.startswith("agent start dev-1"))
        self.assertIn("--agent squad:dev", start)
        self.assertIn("--model sonnet --effort medium", start)  # the role's defaults
        sid = re.search(r"--session-id (\S+)", start).group(1)
        self.assertIn(f"| dev-1 | Dev | settings | task 1 | live | {sid} |", (self.squad / "roster.md").read_text())
        prompt = next(l for l in log if l.startswith("agent prompt"))
        self.assertIn("roles/dev-1.notes.md", prompt)

        self.assertEqual((wt / "wip.txt").read_text(), "uncommitted")
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=wt, text=True, capture_output=True).stdout.strip()
        self.assertEqual(branch, "squad/t/dev-1")
        self.assertFalse(any("worktree add" in l for l in log))

    def test_agent_without_worktree_respawns_in_project_dir(self):
        r = self.respawn()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"tab create --cwd {self.root} --label dev-1", self.log.read_text())

    def test_unknown_agent_fails(self):
        r = subprocess.run([str(BIN / "squad-respawn"), "ghost"], env=self.env, text=True, capture_output=True, timeout=20)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
