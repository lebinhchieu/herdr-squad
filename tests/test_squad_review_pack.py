"""squad-review-pack (ticket 05 T1-T7): writes only two files, blind pack has no code, hunk cap, errors, determinism."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from squadtest import BIN, clean_env, git

TOOL = BIN / "squad-review-pack"
TICKET = """# 07: a fake task
Status: ready-for-agent

## Business AC
1. `squad-review-pack 07` writes a pack. Behaviour is checked by `squad-merge-check main`.

## Technical AC
T1. MARKER_TECH_AC runs `python3 tests/secret_runner.py` and `python3 -m unittest test_fake`.
"""


class ReviewPack(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo, self.scope = root / "repo", root / "scope"
        (self.scope / "tasks").mkdir(parents=True)
        (self.scope / "scope.md").write_text("tickets: feat\n", encoding="utf-8")
        self.repo.mkdir()
        self.g("init", "-q", "-b", "main")
        iss = self.repo / ".scratch" / "feat" / "issues"
        iss.mkdir(parents=True)
        (iss / "07-fake.md").write_text(TICKET, encoding="utf-8")
        self.g("add", "-A")
        self.g("commit", "-q", "-m", "base")
        self.g("checkout", "-q", "-b", "work")
        (self.repo / "src_marker_file.py").write_text("\n".join("MARKER_DIFF_%d" % i for i in range(30)) + "\n", encoding="utf-8")
        self.g("add", "-A")
        self.g("commit", "-q", "-m", "work")

    def tearDown(self):
        self.tmp.cleanup()

    def g(self, *a):
        return git(*a, cwd=self.repo)

    def run_tool(self, *args, scope=True):
        a = list(args) + (["--scope", str(self.scope)] if scope else [])
        r = subprocess.run([sys.executable, str(TOOL), *a], cwd=self.repo, capture_output=True, text=True, env=clean_env())
        return r.returncode, r.stdout, r.stderr

    def files(self):
        return sorted(str(p.relative_to(self.tmp.name)) for p in Path(self.tmp.name).rglob("*") if ".git" not in p.parts and p.is_file())

    def test_pack_has_every_section_and_writes_only_two_files(self):  # AC1, T1
        before = self.files()
        code, out, err = self.run_tool("07")
        self.assertEqual((code, err), (0, ""), out)
        new = [f for f in self.files() if f not in before]
        self.assertEqual(new, ["scope/evidence/07/pack-blackbox.md", "scope/evidence/07/pack.md"])
        pack = (self.scope / "evidence/07/pack.md").read_text(encoding="utf-8")
        for h in ("## Acceptance criteria", "### Technical AC", "## Diff stat", "## Hunks", "## Test commands", "## Evidence path"):
            self.assertIn(h, pack)
        self.assertIn("MARKER_TECH_AC", pack)
        self.assertIn("MARKER_DIFF_3", pack)
        self.assertIn("python3 -m unittest test_fake", pack)
        self.assertIn(".scratch/feat/issues/07-fake/evidence.md", pack)
        self.assertIn("sha: " + self.g("rev-parse", "HEAD"), pack)

    def test_blackbox_pack_is_blind(self):  # AC2, T4
        self.run_tool("07")
        pack = (self.scope / "evidence/07/pack.md").read_text(encoding="utf-8")
        blind = (self.scope / "evidence/07/pack-blackbox.md").read_text(encoding="utf-8")
        for m in ("MARKER_TECH_AC", "MARKER_DIFF_3", "src_marker_file.py", "secret_runner", "python3 -m unittest"):
            self.assertNotIn(m, blind)
        self.assertIn("MARKER_DIFF_3", pack)
        self.assertIn("## Evidence path", blind)
        self.assertIn("`squad-merge-check main`", blind)
        for line in blind.splitlines():
            self.assertFalse(line.startswith(("diff --git", "@@", "+++", "---")), line)

    def test_hunk_cap_note_and_deterministic(self):  # T3, T7
        self.run_tool("07", "--max-lines", "10")
        pack = (self.scope / "evidence/07/pack.md").read_text(encoding="utf-8")
        body = pack.split("````diff\n")[1].split("\n````")[0]
        self.assertEqual(len(body.splitlines()), 10)
        self.assertIn("capped: showing 10 of ", pack)
        first = [(self.scope / "evidence/07" / n).read_bytes() for n in ("pack.md", "pack-blackbox.md")]
        self.run_tool("07", "--max-lines", "10")
        self.assertEqual(first, [(self.scope / "evidence/07" / n).read_bytes() for n in ("pack.md", "pack-blackbox.md")])
        self.run_tool("07")
        self.assertNotIn("capped:", (self.scope / "evidence/07/pack.md").read_text(encoding="utf-8"))

    def test_errors_exit_2_and_leave_nothing(self):  # AC3, T1, T2
        before = self.files()
        for args, scope in ((["99"], True), (["../x"], True), (["1/../.."], True), ([], True), (["07", "--sha", "-x"], True),
                            (["07", "--sha", "nosuch"], True), (["07", "--base", "nosuch"], True), (["07"], False)):
            code, out, err = self.run_tool(*args, scope=scope)
            self.assertEqual(code, 2, (args, out, err))
            self.assertNotIn("Traceback", err)
        self.assertEqual(self.files(), before)

    def test_draft_in_scope_tasks_is_the_fallback(self):  # T5
        self.g("rm", "-q", "-r", ".scratch")
        self.g("commit", "-q", "-m", "drop tickets")
        (self.scope / "tasks" / "07-fake.md").write_text(TICKET, encoding="utf-8")
        (self.scope / "tasks" / "07-design-notes.md").write_text("# notes\nno AC here\n", encoding="utf-8")  # sorts first
        code, out, err = self.run_tool("07", "--base", "main")
        self.assertEqual(code, 0, err)
        pack = (self.scope / "evidence/07/pack.md").read_text(encoding="utf-8")
        self.assertIn("ticket not committed yet", pack)
        self.assertIn("MARKER_TECH_AC", pack)

    def test_ticket_without_technical_ac(self):  # T6 shape
        (self.repo / ".scratch/feat/issues/07-fake.md").write_text("# 07: x\n\n## Business AC\n1. do it\n", encoding="utf-8")
        self.g("commit", "-q", "-am", "no tech")
        self.assertEqual(self.run_tool("07")[0], 0)
        self.assertIn("(none yet)", (self.scope / "evidence/07/pack.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
