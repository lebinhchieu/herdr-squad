"""squad-merge-check: one verdict path per test (ticket 04 T5), read-only proof (T1), exit codes (T2), injection (T7)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from squadtest import BIN, GIT_ENV, clean_env, git

sys.path.insert(0, str(BIN))
sys.dont_write_bytecode = True
import squadtask  # noqa: E402

TOOL = BIN / "squad-merge-check"
BR = "squad/plugin/s1/dev"
ROSTER = """| Agent | Role | Scope | Owns | Status | Session |
| --- | --- | --- | --- | --- | --- |
| qaw | qa-whitebox | s1 | x | live | c |
| qab | qa-blackbox | s1 | x | live | c |
| dev | dev | s1 |  | live | f |
"""


class MergeCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo, self.sd = root / "repo", root / "squad"
        self.home = self.sd / "scopes" / "s1"
        self.home.mkdir(parents=True)
        (self.home / "scope.md").write_text("x\n", encoding="utf-8")
        (self.home / "roster.md").write_text(ROSTER, encoding="utf-8")
        self.repo.mkdir()
        g = self.g
        g("init", "-q", "-b", "main")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_a.py").write_text("uses libx\n", encoding="utf-8")
        (self.repo / "libx").write_text("1", encoding="utf-8")
        (self.repo / "other").write_text("1", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "base")
        g("checkout", "-q", "-b", BR)
        (self.repo / "libx").write_text("branch", encoding="utf-8")
        (self.repo / "t05.md").write_text("ticket", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "work")
        self.sha = g("rev-parse", "HEAD")
        g("checkout", "-q", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def g(self, *a):
        return git(*a, cwd=self.repo)

    def passed(self, sha=None, qab=True):
        sha = sha or self.sha
        squadtask.record(self.home, "05", "claim", by="dev", branch=BR)
        squadtask.record(self.home, "05", "handin", by="dev", sha=sha, branch=BR)
        squadtask.record(self.home, "05", "pass", by="qaw", slot="qaw", sha=sha)
        if qab:
            squadtask.record(self.home, "05", "pass", by="qab", slot="qab", sha=sha)

    def run_tool(self, *args):
        env = clean_env(SCOPE_DIR=str(self.home), **GIT_ENV)
        r = subprocess.run([sys.executable, str(TOOL), *args], cwd=self.repo, capture_output=True, text=True, env=env)
        return r.returncode, r.stdout, r.stderr

    def test_ok_main_moved_no_shared_file_and_read_only(self):  # AC4 ok, SQ-7 note, T1, T7 untracked warns
        self.passed()
        (self.repo / "other").write_text("2", encoding="utf-8")
        self.g("commit", "-q", "-am", "main moves")
        (self.repo / "stray.txt").write_text("x", encoding="utf-8")
        before = (self.g("rev-parse", "HEAD"), self.g("for-each-ref"), self.g("status", "--porcelain"))
        code, out, err = self.run_tool(BR)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(before, (self.g("rev-parse", "HEAD"), self.g("for-each-ref"), self.g("status", "--porcelain")))
        self.assertEqual(self.g("branch", "--show-current"), "main")
        self.assertIn("main-related: main moved, 1 files, none related", out)
        self.assertIn("warning: untracked file outside .claude/squads/: stray.txt", out)
        self.assertEqual(out.splitlines()[-1], "VERDICT: ok")

    def test_dirty_root_refuses(self):
        self.passed()
        (self.repo / "other").write_text("dirty", encoding="utf-8")
        code, out, _ = self.run_tool(BR)
        self.assertEqual(code, 1)
        self.assertIn("dirty: yes", out)
        self.assertIn("refuse: project root has uncommitted changes", out.splitlines()[-1])

    def test_sha_not_passed_refuses(self):
        self.passed(qab=False)  # one checker only
        code, out, _ = self.run_tool(BR)
        self.assertEqual(code, 1)
        self.assertIn("sha not passed by every checker", out.splitlines()[-1])
        code, out, _ = self.run_tool(self.sha[:9], "--base", "main")  # a sha no task knows
        self.assertEqual(code, 1)

    def test_main_moved_with_related_files_refuses(self):
        self.passed()
        (self.repo / "libx").write_text("main edit", encoding="utf-8")
        self.g("commit", "-q", "-am", "main touches libx")
        code, out, _ = self.run_tool(BR)
        self.assertEqual(code, 1)
        self.assertIn("main-related: shared files ['libx']", out)
        self.assertIn("a Developer merges main first", out.splitlines()[-1])

    def test_main_moved_shared_test_hit_only_refuses(self):  # SQ-7: no shared file, one test mentions both
        self.passed()
        (self.repo / "tests" / "test_a.py").write_text("uses libx and other\n", encoding="utf-8")
        self.g("commit", "-q", "-am", "test mentions other")
        (self.repo / "other").write_text("2", encoding="utf-8")
        self.g("commit", "-q", "-am", "main edits other")
        code, out, _ = self.run_tool(BR)
        self.assertEqual(code, 1, out)
        self.assertIn("shared test hits", out)

    def test_evidence_only_commit_after_pass_is_ok(self):  # MRG-2
        self.passed()
        self.g("checkout", "-q", BR)
        (self.repo / "t05").mkdir()
        (self.repo / "t05" / "evidence.md").write_text("e", encoding="utf-8")
        self.g("add", "-A")
        self.g("commit", "-q", "-m", "evidence")
        ev = self.g("rev-parse", "HEAD")
        self.g("checkout", "-q", "main")
        code, out, _ = self.run_tool(ev)
        self.assertEqual(code, 0, out)
        self.assertIn("evidence-only", out)
        # a code commit after the pass is not
        self.g("checkout", "-q", BR)
        (self.repo / "libx").write_text("later", encoding="utf-8")
        self.g("commit", "-q", "-am", "code")
        self.g("checkout", "-q", "main")
        self.assertEqual(self.run_tool(BR)[0], 1)

    def test_no_merge_base_refuses(self):  # fail closed (QAW follow-up)
        self.passed()
        self.g("checkout", "-q", "--orphan", "other")
        self.g("commit", "-q", "--allow-empty", "-m", "unrelated")
        self.g("checkout", "-q", "main")
        code, out, _ = self.run_tool(BR, "--base", "other")
        self.assertEqual(code, 1, out)
        self.assertIn("no merge base", out.splitlines()[-1])

    def test_usage_errors_and_no_injection(self):  # T2, T7
        for args in ([], ["--nope"], ["nosuchref"], ["x;touch pwned"], ["--base"]):
            code, out, err = self.run_tool(*args)
            self.assertEqual(code, 2, args)
            self.assertNotIn("Traceback", err)
        self.assertFalse((self.repo / "pwned").exists())
        self.assertFalse((self.repo / "y").exists())


if __name__ == "__main__":
    unittest.main()
