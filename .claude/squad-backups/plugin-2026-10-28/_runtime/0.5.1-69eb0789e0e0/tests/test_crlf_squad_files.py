"""Ticket 17: roles write squad files with LF, and every helper reads a CRLF roster.md/scope.md like the LF one."""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rulesview import composed
from test_squad_close import FAKE_HERDR, git

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
# The exact call the two instructions name; the test below runs it, so the text cannot drift from what works.
CALL = 'open(path, "w", encoding="utf-8", newline="\\n")'
ROSTER = ("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
          "| manager-t | manager |  |  | live | s0 |\n| t-dev-s-1 | dev | s | task 1 | live | s2 |\n"
          "| t-qa-s | qa-whitebox | s | qa | live | s3 |\n")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SCOPE = "# Scope s\n\ngoal: g1\ndesign: yes\nqa: full\n"


def bullet(rel, label):
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return next(l for l in lines if l.startswith(label))


class InstructionWordingTest(unittest.TestCase):
    """The roster/LF wording moved from the Manager and Team Lead cards to FILE-4 and FILE-5* (ticket 06)."""
    FILES = (("manager", "small script that keeps the rest"), ("team-lead", "small script that keeps the rest"))

    def test_roster_bullet_names_the_lf_write_and_the_cr_check(self):
        for role, kept in self.FILES:
            with self.subTest(role=role):
                b = composed(role, "M")
                for needle in ('newline="\\n"', 'encoding="utf-8"', "$'\\r'", "small script"):
                    self.assertIn(needle, b)
                self.assertIn(kept, b)
                self.assertIn("never `command > file`", b)

    def test_the_named_call_writes_no_cr_and_changes_only_the_edited_line(self):
        for role, _ in self.FILES:
            with self.subTest(role=role):
                self.assertIn(CALL, composed(role, "M"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.md"
            path.write_bytes(ROSTER.encode("utf-8"))
            code = ("import sys\npath = sys.argv[1]\n"
                    "text = open(path, encoding='utf-8', newline='').read().replace('| task 1 |', '| task 2 |')\n"
                    f"f = {CALL}\nf.write(text)\nf.close()\n")
            r = subprocess.run([sys.executable, "-I", "-c", code, str(path)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = path.read_bytes()
            self.assertEqual(data.count(b"\r"), 0)
            self.assertEqual(data.decode("utf-8"), ROSTER.replace("| task 1 |", "| task 2 |"))


class CrlfReadersTest(unittest.TestCase):
    """Scaffolding reused: FAKE_HERDR and git() from test_squad_close.py; the scoped-squad layout of
    test_squad_usage.py (scopes/<s>/roster.md, SQUAD_DIR/SCOPE_DIR env); the herdr stub style of test_squad_retire.py.
    squad-respawn is not run (it needs a live herdr session and a Claude launch); squad-label reads neither file."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        fake = root / "fakebin"
        fake.mkdir()
        (fake / "herdr").write_text(FAKE_HERDR, encoding="utf-8", newline="\n")
        (fake / "herdr").chmod(0o755)
        self.base_env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        self.base_env.update(HERDR_ENV="1", HERDR_LOG=str(root / "herdr.log"), PATH=f"{fake}:{os.environ['PATH']}")
        self.runs = {}
        for variant in ("lf", "crlf"):
            repo = root / variant
            repo.mkdir()
            git("init", "-q", "-b", "main", cwd=repo)
            git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
            squad = repo / ".claude" / "squads" / "t"
            scope = squad / "scopes" / "s"
            (squad / "goals" / "g1").mkdir(parents=True)
            scope.mkdir(parents=True)
            nl = "\n" if variant == "lf" else "\r\n"
            (squad / "process.md").write_text("x", encoding="utf-8", newline="\n")
            for p, text in ((squad / "roster.md", ROSTER), (scope / "roster.md", ROSTER), (scope / "scope.md", SCOPE)):
                p.write_text(text, encoding="utf-8", newline=nl)
            self.runs[variant] = (repo, squad, scope)

    def tearDown(self):
        self.tmp.cleanup()

    def both(self, argv, role=None):
        out = {}
        for variant, (repo, squad, scope) in self.runs.items():
            env = dict(self.base_env, SQUAD_DIR=str(squad), SCOPE_DIR=str(scope))
            if role:
                env["SQUAD_ROLE"] = role
            r = subprocess.run([str(BIN / argv[0]), *argv[1:]], env=env, cwd=repo, text=True, encoding="utf-8",
                               capture_output=True, timeout=30)
            norm = lambda s: UUID.sub("<uuid>", s.replace(str(repo), "<repo>"))  # squad-spawn mints a session id per run
            out[variant] = (norm(r.stdout), norm(r.stderr), r.returncode)
        lf, crlf = out["lf"], out["crlf"]
        self.assertEqual(crlf, lf, argv)
        for stream in crlf[:2]:
            self.assertNotIn("\r", stream, argv)
        return lf

    def test_usage_get(self):
        out, _, rc = self.both(["squad-usage", "--get", "t-dev-s-1"])
        self.assertEqual((out.split("\t")[0], rc), ("dev", 0))

    def test_usage_table(self):
        out, _, rc = self.both(["squad-usage"])
        self.assertEqual(rc, 0)
        self.assertIn("t-dev-s-1", out)

    def test_close_scope_dry_run(self):
        out, _, rc = self.both(["squad-close", "t", "--scope", "s", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("t-dev-s-1", out)

    def test_close_goal_dry_run_reads_goal_line_of_scope_md(self):
        # The goal: grep of squad-close: a CRLF "goal: g1" line must still count as an open scope.
        out, err, rc = self.both(["squad-close", "t", "--goal", "g1", "--dry-run"])
        self.assertEqual(rc, 1)
        self.assertIn("still has open scopes: s", err)

    def test_spawn_dry_run_reads_goal_and_design(self):
        for role in ("designer", "dev"):
            with self.subTest(role=role):
                out, _, rc = self.both(["squad-spawn", role, "x", "--scope", "s", "--dry-run"])
                self.assertEqual(rc, 0)
                self.assertIn("goals/g1", out)  # the goal: line resolved, with no CR in the path

    def test_retire_team_lead_branch(self):
        for name, rc in (("t-dev-s-1", 0), ("t-qa-s", 2)):
            with self.subTest(name=name):
                *_, got = self.both(["squad-retire", name, "--no-notes"], role="team-lead")
                self.assertEqual(got, rc)


if __name__ == "__main__":
    unittest.main()
