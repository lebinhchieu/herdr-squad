"""BRD-30: tests/run_suite.py on stub test files in a temp dir (never the real suite)."""
import os
import re
import time
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
                              env=dict({k: v for k, v in os.environ.items() if k != "SQUAD_REQUIRE_CLAUDE"},
                                         SQUAD_SUITE_LOCK=str(self.dir / "lock")))

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

    def test_a_browser_file_that_fails_once_is_rerun_alone_and_named_but_a_real_failure_stays_red(self):
        flaky = ("import os, unittest\n# playwright\nMARK = %r\nclass T(unittest.TestCase):\n"
                 "    def test_a(self):\n        first = not os.path.exists(MARK)\n        open(MARK, 'w').close()\n"
                 "        self.assertFalse(first, 'first try')\n") % str(self.dir / "mark")
        self.stub("test_flaky.py", flaky)
        done = self.run_runner()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("test_flaky (passed on retry; first run failed)", done.stdout)
        self.assertIn("first try", done.stdout)  # the first failure is printed, not hidden
        self.assertRegex(done.stdout, r"Ran 1 tests in \d+\.\d+s\n\nOK\n$")  # and the tail is still the OK tail
        self.stub("test_hard.py", FAIL + "# playwright\n")
        done = self.run_runner("--retries", "2")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED (files=1: test_hard)", done.stdout)

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

    def test_tz_run_requires_claude_for_the_mod_test_and_a_plain_run_does_not(self):  # PI-07 AC7
        self.stub("test_env.py", "import os, unittest\nclass T(unittest.TestCase):\n"
                  "    def test_a(self): self.assertEqual(os.environ.get('SQUAD_REQUIRE_CLAUDE'), '1')\n")
        out = self.dir / "r"
        done = self.run_runner("--receipt", str(out / "tz"), "--tz")
        self.assertEqual(done.returncode, 0, done.stdout)
        done = self.run_runner("--receipt", str(out / "plain"))
        self.assertEqual(done.returncode, 1, done.stdout)

    def test_tz_run_takes_only_the_time_files_and_the_also_file_under_new_york_time(self):
        probe = ("import os, unittest\nclass T(unittest.TestCase):\n"
                 "    def test_a(self): self.assertEqual((os.environ['TZ'], os.environ['LC_ALL']), ('America/New_York', 'C'))\n")
        self.stub("test_time_probe.py", probe)
        self.stub("test_extra.py", probe)
        self.stub("test_other.py", FAIL)  # would fail the run if the tz pass picked it up
        out = self.dir / "receipt"
        done = self.run_runner("--receipt", str(out), "--tz", "--also", "test_time_probe", "--also", "test_extra")
        self.assertEqual(done.returncode, 1)  # the default run fails on the probes and on test_other
        tz = (out / "suite-tz.txt").read_text()
        self.assertRegex(tz.splitlines()[0], r"^sha [0-9a-f]{40} clean=(yes|no)$")
        self.assertIn("test_time_probe", tz)
        self.assertIn("test_extra", tz)
        self.assertNotIn("test_other", tz)
        self.assertRegex(tz, r"Ran 2 tests in \d+\.\d+s\n\nOK\n")

    def test_tz_run_with_no_time_files_and_no_also_skips_the_time_pass_and_says_so(self):  # RB-01 AC7
        self.stub("test_plain.py", "import os, unittest\nclass T(unittest.TestCase):\n"
                  "    def test_a(self): self.assertEqual(os.environ.get('SQUAD_REQUIRE_CLAUDE'), '1')\n")
        out = self.dir / "receipt"
        done = self.run_runner("--receipt", str(out), "--tz")
        self.assertEqual(done.returncode, 0, done.stdout)  # the default run still sets SQUAD_REQUIRE_CLAUDE under --tz
        line = "skipped: no time files (TZ_FILES is empty and no --also given)"
        tz = (out / "suite-tz.txt").read_text().splitlines()
        self.assertRegex(tz[0], r"^sha [0-9a-f]{40} clean=(yes|no)$")
        self.assertEqual(tz[1:], [line])
        self.assertIn(line, done.stdout)
        self.assertNotIn("TZ=America/New_York", done.stdout)

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


class AgentEnvTest(unittest.TestCase):
    """RP-08: a test run never sees or writes the agent's own squad folders."""

    def agent_env(self, tmp):
        return dict(os.environ, **{n: str(tmp) for n in run_suite.AGENT_ENV})

    def test_child_env_drops_the_six_agent_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_env.py").write_text(
                "import os, unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n"
                "        self.assertEqual([n for n in %r if n in os.environ], [])\n" % (run_suite.AGENT_ENV,))
            old = os.environ.copy()
            os.environ.update(self.agent_env(tmp))
            try:
                ok = run_suite.run_file(Path(tmp) / "test_env.py")[1]
            finally:
                os.environ.clear()
                os.environ.update(old)
            self.assertTrue(ok)
        self.assertEqual(set(run_suite.AGENT_ENV), {"SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE"})

    def test_squad_usage_leaves_a_live_roster_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            roster = Path(tmp) / "roster.md"
            roster.write_text("| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n| dev-1 | dev | s | x | live | s1 |\n")
            before = roster.read_bytes()
            r = subprocess.run([sys.executable, "-m", "unittest", "-q", "test_squad_usage"], cwd=str(Path(__file__).parent),
                               env=self.agent_env(tmp), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(roster.read_bytes(), before)


STAMP = ("import os, time, unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n"
         "        with open(%r, 'a') as f: f.write('start %%.3f\\n' %% time.time())\n"
         "        time.sleep(%s)\n"
         "        with open(%r, 'a') as f: f.write('end %%.3f\\n' %% time.time())\n")


class LockScopeTest(unittest.TestCase):
    """RP-09 (a): the flock covers the browser files only; the pool never waits for it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.lock = self.root / "lock"

    def runner_dir(self, name, secs=1.5):
        d = self.root / name
        d.mkdir()
        for kind, extra in (("pool", ""), ("browser", "# playwright\n")):
            stamp = self.root / ("%s-%s.stamps" % (name, kind))
            (d / ("test_%s.py" % kind)).write_text(STAMP % (str(stamp), secs, str(stamp)) + extra)
        return d

    def start(self, d, *args):
        return subprocess.Popen([sys.executable, str(RUNNER), "--tests-dir", str(d)] + list(args),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                                env=dict(os.environ, SQUAD_SUITE_LOCK=str(self.lock)))

    def span(self, name, kind):
        lines = (self.root / ("%s-%s.stamps" % (name, kind))).read_text().split()
        return float(lines[1]), float(lines[3])

    def test_two_runners_overlap_in_the_pool_and_never_in_the_browser_phase(self):
        a, b = self.runner_dir("a"), self.runner_dir("b")
        pa, pb = self.start(a), self.start(b)
        outs = [pa.communicate(timeout=60)[0], pb.communicate(timeout=60)[0]]
        self.assertEqual((pa.returncode, pb.returncode), (0, 0), outs)
        (a0, a1), (b0, b1) = self.span("a", "pool"), self.span("b", "pool")
        self.assertLess(max(a0, b0), min(a1, b1), "the pool phases should overlap")
        (a0, a1), (b0, b1) = self.span("a", "browser"), self.span("b", "browser")
        self.assertGreaterEqual(max(a0, b0), min(a1, b1), "the browser phases must not overlap")
        self.assertEqual(sum("waiting for the suite lock" in o for o in outs), 1, outs)
        for o in outs:
            self.assertRegex(o, r"Ran 2 tests in \d+\.\d+s\n\nOK\n$")

    def test_a_runner_whose_lock_is_held_finishes_its_pool_first_and_says_it_waits(self):
        import fcntl
        d = self.runner_dir("c", secs=0.2)
        with open(self.lock, "a") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            p = self.start(d)
            pool_stamps = self.root / "c-pool.stamps"
            for _ in range(100):
                if pool_stamps.exists() and "end" in pool_stamps.read_text():
                    break
                time.sleep(0.1)
            self.assertIn("end", pool_stamps.read_text(), "the pool must finish while the lock is held")
            self.assertIsNone(p.poll(), "the runner still waits for its browser file")
            self.assertFalse((self.root / "c-browser.stamps").exists())
        out = p.communicate(timeout=30)[0]
        self.assertEqual(p.returncode, 0, out)
        self.assertIn("waiting for the suite lock", out)
        self.assertTrue((self.root / "c-browser.stamps").exists())


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          universal_newlines=True, check=True).stdout.strip()


class IfChangedTest(unittest.TestCase):
    """RP-09 (b)+(e): the browser files and the time pass run only when the diff since BASE can affect them."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        for d in ("tests", "bin", "docs"):
            (self.repo / d).mkdir()
        (self.repo / "tests" / "test_time_probe.py").write_text(PASS)  # a time file
        (self.repo / "tests" / "test_browser.py").write_text(PASS + "# playwright\n")
        (self.repo / "tests" / "test_other.py").write_text(PASS)
        for f in ("bin/squadlabel.py", "bin/elsewhere", "docs/a.md", "tests/run_suite.py"):
            (self.repo / f).write_text("x\n")
        git(self.repo, "init", "-q")
        self.commit_all("base")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.out = self.repo / "receipt"
        self.lock = self.repo / "lock"

    def commit_all(self, msg):
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)

    def commit(self, rel, text="y\n"):
        (self.repo / rel).write_text(text)
        self.commit_all(rel)

    def run_runner(self, *args, base=None):
        return subprocess.run([sys.executable, str(RUNNER), "--tests-dir", str(self.repo / "tests"), "--repo", str(self.repo),
                               "--receipt", str(self.out), "--if-changed", base or self.base,
                               "--also", "test_time_probe"] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                              env=dict(os.environ, SQUAD_SUITE_LOCK=str(self.lock)))

    def check(self, browser, tz, **kw):
        """Run once; assert which phases ran. The pool (test_other) always runs."""
        done = self.run_runner(**kw)
        self.assertEqual(done.returncode, 0, done.stdout)
        default = (self.out / "suite-default.txt").read_text()
        tzt = (self.out / "suite-tz.txt").read_text()
        self.assertIn("test_other", default)
        self.assertEqual("test_browser" in default, browser, default)
        self.assertEqual("skipped browser files: no browser test or watched source changed since " + self.base in default,
                         not browser, default)
        self.assertRegex(tzt.splitlines()[0], r"^sha [0-9a-f]{40} clean=(yes|no)$")
        self.assertEqual("skipped: no time file or watched source changed since " + self.base in tzt, not tz, tzt)
        self.assertEqual("test_time_probe" in tzt, tz, tzt)
        self.assertNotIn("waiting for the suite lock", done.stdout)
        return done

    def test_neither_phase_runs_when_the_diff_holds_no_test_or_watched_source(self):
        self.check(False, False)
        self.commit("docs/a.md")
        self.commit("bin/elsewhere")
        self.commit("tests/test_other.py", PASS + "# edit\n")
        self.check(False, False)

    def test_the_flock_is_never_taken_when_the_browser_phase_is_skipped(self):
        import fcntl
        with open(self.lock, "a") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            self.check(False, False)  # would hang on the held lock if the runner asked for it

    def test_browser_phase_runs_for_a_browser_test_run_suite_and_an_uncommitted_change_not_for_a_bin_file(self):
        self.commit("tests/test_browser.py", PASS + "# playwright edit\n")
        self.check(True, False)
        git(self.repo, "reset", "-q", "--hard", self.base)
        self.commit("bin/squadlabel.py")
        self.check(False, False)
        git(self.repo, "reset", "-q", "--hard", self.base)
        self.commit("tests/run_suite.py")
        self.check(True, False)
        git(self.repo, "reset", "-q", "--hard", self.base)
        (self.repo / "tests" / "run_suite.py").write_text("dirty\n")
        self.check(True, False)

    def test_time_pass_runs_for_the_also_file_only_not_for_a_new_fixture(self):
        self.commit("tests/test_time_probe.py", PASS + "# edit\n")
        self.check(False, True)
        git(self.repo, "reset", "-q", "--hard", self.base)
        (self.repo / "tests" / "fixtures").mkdir()
        (self.repo / "tests" / "fixtures" / "new.json").write_text("{}")
        self.check(False, False)

    def test_a_bad_base_runs_everything_and_says_so(self):
        done = self.run_runner(base="no-such-ref")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("note: git diff no-such-ref failed, nothing skipped", done.stdout)
        self.assertIn("test_browser", done.stdout)
        self.assertIn("TZ=America/New_York", done.stdout)

    def test_flag_needs_receipt_and_excludes_tz(self):
        done = subprocess.run([sys.executable, str(RUNNER), "--tests-dir", str(self.repo / "tests"),
                               "--if-changed", self.base], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn("--if-changed needs --receipt", done.stdout)
        done = self.run_runner("--tz")
        self.assertEqual(done.returncode, 2)
        self.assertIn("excludes --tz", done.stdout)


class ClaudeMdTest(unittest.TestCase):
    """RP-09 (f): the `## Running tests` section of CLAUDE.md names only flags the runner has."""

    def section(self):
        text = (Path(run_suite.__file__).resolve().parent.parent / "CLAUDE.md").read_text()
        m = re.search(r"^## Running tests\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m, "CLAUDE.md has no '## Running tests' section")
        return m.group(1).strip("\n")

    def test_section_is_short_and_every_flag_it_names_is_in_the_runner(self):
        section = self.section()
        self.assertLessEqual(len(section.splitlines()) + 1, 10)
        help_text = subprocess.run([sys.executable, str(RUNNER), "--help"], stdout=subprocess.PIPE,
                                   universal_newlines=True).stdout
        flags = set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", section))
        self.assertTrue({"--receipt", "--if-changed", "--tz"} <= flags, flags)
        for flag in flags:
            self.assertIn(flag, help_text, "%s is in CLAUDE.md but not in run_suite.py" % flag)

    def test_pgrep_and_pkill_appear_only_as_never(self):
        for line in self.section().splitlines():
            for word in ("pgrep -f", "pkill -f"):
                if word in line:
                    self.assertRegex(line, r"[Nn]ever [^.]*" + word)
