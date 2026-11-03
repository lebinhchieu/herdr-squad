"""squadboard_git: worktree list, branch refs, last commit time; a missing git is None, never an error."""
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import squadboard_git as g  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "GIT_AUTHOR_DATE": "2023-11-14T22:13:20Z",
       "GIT_COMMITTER_DATE": "2023-11-14T22:13:20Z"}


def run(repo, *a):
    subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True, env=ENV)


# Recorded from this repo (git worktree list --porcelain / for-each-ref), one normal and one detached HEAD.
PORCELAIN = (
    "worktree /home/u/squad\nHEAD 67d3543eecb12a8f0683bfe0f5896cc867d78ed3\nbranch refs/heads/main\n\n"
    "worktree /home/u/.herdr/worktrees/x\nHEAD 08328ee0000000000000000000000000000000aa\ndetached\n")
REFS = ("squad/board/dashboard/board-dev-found-3\t2ee80ccd87618b999d898b284f85621079f5ca71\t1793729207\n"
        "squad/x/empty\t\t\n")


class Parsers(unittest.TestCase):
    def test_T17_TA5_porcelain_detached(self):
        rows = g.parse_worktrees(PORCELAIN)
        self.assertEqual([r["branch"] for r in rows], ["main", ""])
        self.assertEqual(rows[1]["path"], "/home/u/.herdr/worktrees/x")

    def test_T17_TA5_refs(self):
        rows = g.parse_refs(REFS)
        self.assertEqual(rows[0]["ts"], 1793729207.0)
        self.assertEqual((rows[1]["sha"], rows[1]["ts"]), ("", None))  # no commits: kept, time unknown


class GitHelpers(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.td.name, "r")
        os.mkdir(self.repo)
        run(self.repo, "init", "-b", "main")
        run(self.repo, "commit", "--allow-empty", "-m", "one")
        run(self.repo, "branch", "squad/s/a/dev")
        run(self.repo, "checkout", "-b", "squad/s/a/ahead")
        run(self.repo, "commit", "--allow-empty", "-m", "two")
        run(self.repo, "checkout", "main")

    def tearDown(self):
        self.td.cleanup()

    def test_worktrees(self):
        rows = g.worktrees(self.repo)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["branch"], "main")
        self.assertEqual(len(rows[0]["head"]), 40)

    def test_branch_refs_prefix_and_merged(self):
        rows = g.branch_refs(self.repo, "squad/s/a/")
        self.assertEqual({r["branch"] for r in rows}, {"squad/s/a/dev", "squad/s/a/ahead"})
        self.assertEqual(rows[0]["ts"], 1_700_000_000)
        merged = g.branch_refs(self.repo, "squad/s/a/", merged_into="main")
        self.assertEqual([r["branch"] for r in merged], ["squad/s/a/dev"])
        self.assertEqual(g.branch_refs(self.repo, "nope/"), [])

    def test_last_commit_time(self):
        self.assertEqual(g.last_commit_time(self.repo), 1_700_000_000)
        self.assertIsNone(g.last_commit_time(self.repo, "no-such-ref"))

    def test_T17_TA6_unknown_not_exception(self):
        empty = tempfile.mkdtemp(dir=self.td.name)
        with mock.patch.dict(os.environ, {"PATH": empty}):  # missing git
            self.assertIsNone(g.worktrees(self.repo))
            self.assertIsNone(g.branch_refs(self.repo))
            self.assertIsNone(g.last_commit_time(self.repo))
        with mock.patch.object(g.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired("git", 1)):  # timeout
            self.assertIsNone(g.worktrees(self.repo))

    def test_not_a_repo_is_unknown(self):
        self.assertIsNone(g.worktrees(self.td.name))


if __name__ == "__main__":
    unittest.main()
