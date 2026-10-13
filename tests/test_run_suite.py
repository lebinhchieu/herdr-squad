"""BRD-30: tests/run_suite.py on stub test files in a temp dir (never the real suite)."""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import run_suite

PASS = "import unittest\nclass T(unittest.TestCase):\n    def test_a(self): pass\n    def test_b(self): pass\n"
FAIL = "import unittest\nclass T(unittest.TestCase):\n    def test_a(self): self.fail('boom')\n"
NO_RAN = "import sys\nsys.exit(0)\n"
RUNNER = Path(run_suite.__file__)


class RunSuiteTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def stub(self, name, body):
        (self.dir / name).write_text(body)

    def run_runner(self, *args):
        return subprocess.run([sys.executable, str(RUNNER), "--tests-dir", str(self.dir)] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                              env=dict(os.environ, SQUAD_SUITE_LOCK=str(self.dir / "lock")))

    def test_discovery_takes_test_files_and_splits_browser_files_off_by_text(self):
        self.stub("test_plain.py", PASS)
        self.stub("test_browser.py", PASS + "# opens Playwright\n")
        self.stub("test_chrome.py", PASS + "# headless Chromium\n")
        self.stub("helper.py", PASS)
        pool, serial = run_suite.discover(self.dir)
        self.assertEqual([f.name for f in pool], ["test_plain.py"])
        self.assertEqual([f.name for f in serial], ["test_browser.py", "test_chrome.py"])

    def test_browser_files_are_shared_out_over_the_streams_by_size(self):
        self.stub("test_a.py", PASS + "# playwright\n" * 40)
        self.stub("test_b.py", PASS + "# playwright\n" * 30)
        self.stub("test_c.py", PASS + "# playwright\n" * 20)
        self.stub("test_d.py", PASS + "# playwright\n")
        _, serial = run_suite.discover(self.dir)
        names = lambda streams: [[f.name for f in st] for st in streams]
        self.assertEqual(names(run_suite.split_streams(serial, 2)), [["test_a.py", "test_d.py"], ["test_b.py", "test_c.py"]])
        self.assertEqual(len(run_suite.split_streams(serial, 9)), 4)  # never an empty stream
        self.assertEqual(names(run_suite.split_streams(serial, 1)), [["test_a.py", "test_b.py", "test_c.py", "test_d.py"]])

    def test_pool_runs_the_biggest_file_first(self):
        self.stub("test_small.py", PASS)
        self.stub("test_big.py", PASS + "# padding\n" * 50)
        pool, _ = run_suite.discover(self.dir)
        self.assertEqual([f.name for f in pool], ["test_big.py", "test_small.py"])

    def test_all_green_exits_zero_and_counts_tests_of_both_streams(self):
        self.stub("test_plain.py", PASS)
        self.stub("test_browser.py", PASS + "# playwright\n")
        done = self.run_runner()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertRegex(done.stdout, r"Ran 4 tests in \d+\.\d+s\n\nOK\n")

    def test_a_failing_file_exits_nonzero_and_prints_its_output(self):
        self.stub("test_plain.py", PASS)
        self.stub("test_bad.py", FAIL)
        done = self.run_runner()
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED (files=1: test_bad)", done.stdout)
        self.assertIn("===== test_bad =====", done.stdout)
        self.assertIn("boom", done.stdout)

    def test_a_file_with_no_ran_line_counts_as_fail(self):
        self.stub("test_silent.py", NO_RAN)
        done = self.run_runner()
        self.assertEqual(done.returncode, 1)
        self.assertRegex(done.stdout, r"FAIL\s+0 tests .*test_silent")

    def test_receipt_first_line_has_the_sha_shape_and_the_tail_is_the_qa_tail(self):
        self.stub("test_plain.py", PASS)
        out = self.dir / "receipt"
        done = self.run_runner("--receipt", str(out))
        self.assertEqual(done.returncode, 0, done.stdout)
        lines = (out / "suite-default.txt").read_text().splitlines()
        self.assertRegex(lines[0], r"^sha [0-9a-f]{40} clean=(yes|no)$")
        self.assertRegex(lines[-3], r"^Ran 2 tests in \d+\.\d+s$")
        self.assertEqual(lines[-1], "OK")
        self.assertFalse((out / "suite-tz.txt").exists())

    def test_tz_run_takes_only_the_time_files_and_the_also_file_under_new_york_time(self):
        probe = ("import os, unittest\nclass T(unittest.TestCase):\n"
                 "    def test_a(self): self.assertEqual((os.environ['TZ'], os.environ['LC_ALL']), ('America/New_York', 'C'))\n")
        self.stub("test_board_state.py", probe)
        self.stub("test_extra.py", probe)
        self.stub("test_other.py", FAIL)  # would fail the run if the tz pass picked it up
        out = self.dir / "receipt"
        done = self.run_runner("--receipt", str(out), "--tz", "--also", "test_extra")
        self.assertEqual(done.returncode, 1)  # the default run fails on the probes and on test_other
        tz = (out / "suite-tz.txt").read_text()
        self.assertRegex(tz.splitlines()[0], r"^sha [0-9a-f]{40} clean=(yes|no)$")
        self.assertIn("test_board_state", tz)
        self.assertIn("test_extra", tz)
        self.assertNotIn("test_other", tz)
        self.assertRegex(tz, r"Ran 2 tests in \d+\.\d+s\n\nOK\n")

    def test_dirty_check_ignores_evidence_and_pycache(self):
        repo = self.dir / "repo"
        (repo / "evidence").mkdir(parents=True)
        (repo / "tests").mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(repo)] + list(a), check=True,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        git("init", "-q")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "x")
        (repo / "evidence" / "r.txt").write_text("x")
        (repo / "tests" / "__pycache__").mkdir()
        (repo / "tests" / "__pycache__" / "a.pyc").write_text("x")
        self.assertRegex(run_suite.git_head_line(repo), r"^sha [0-9a-f]{40} clean=yes$")
        (repo / "stray.txt").write_text("x")
        self.assertTrue(run_suite.git_head_line(repo).endswith("clean=no"))
        self.assertTrue(re.match(r"sha ", run_suite.git_head_line(repo)))


if __name__ == "__main__":
    unittest.main()
