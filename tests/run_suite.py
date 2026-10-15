#!/usr/bin/env python3
"""Run the whole suite, one subprocess per test file, in parallel. Same files as `unittest discover -s tests`.

Files that drive a browser (source mentions playwright or chrom) run one after another in a few
streams (--browser-streams) beside the pool: their timing thresholds only hold without many
Chromes at once, so these are never in the pool.
The browser files (and their retries) hold /tmp/squad-suite.lock, so two runners never drive Chromium at once; the pool of other files never waits for it.

    python3 tests/run_suite.py [--jobs N] [--receipt DIR [--tz | --if-changed BASE] [--also test_x]...]
"""
import argparse
import concurrent.futures
import contextlib
import fcntl
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

LOCK = os.environ.get("SQUAD_SUITE_LOCK", "/tmp/squad-suite.lock")  # the override is for test_run_suite only
TZ_FILES = ("test_board_timeline", "test_board_state", "test_board_tokens", "test_board_recorder")
AGENT_ENV = ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE")  # an agent's own squad folders; tests must never see them
# Non-test sources the board tests load, transitively (squad-board imports squadlabel and serves the html); a path ending
# in "/" is a whole folder. test_run_suite pins that every bin/<name>, local module and html they reach is listed.
BOARD_SOURCES = ("bin/squad-board", "bin/squad-board.html", "bin/squadlabel.py", "tests/board_fixture.py",
                 "tests/fake_herdr.py", "tests/fixtures/")
TZ_WATCH = BOARD_SOURCES  # the four time files
BROWSER_WATCH = BOARD_SOURCES + ("tests/run_suite.py",)  # the browser files; a browser test file itself is found by discover
TZ_ENV = {"TZ": "America/New_York", "LC_ALL": "C"}
RAN_RE = re.compile(r"^Ran (\d+) tests? in ", re.M)


def discover(tests_dir):
    """(parallel, serial) lists of test file paths; serial = browser files, in name order."""
    files = sorted(Path(tests_dir).glob("test_*.py"))
    serial, pool = [], []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace").lower()
        (serial if ("playwright" in text or "chrom" in text) else pool).append(f)
    pool.sort(key=lambda f: f.stat().st_size, reverse=True)
    return pool, serial


def run_file(path, env_extra=None):
    """Run one file; returns (name, ok, n_tests, seconds, output)."""
    env = {k: v for k, v in os.environ.items() if k not in AGENT_ENV}
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # the repo has had .pyc files committed
    env.update(env_extra or {})
    started = time.monotonic()
    done = subprocess.run([sys.executable, "-m", "unittest", "-q", path.stem], cwd=str(path.parent),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seconds = time.monotonic() - started
    out = done.stdout.decode("utf-8", "replace")
    ran = RAN_RE.search(out)
    ok = done.returncode == 0 and ran is not None
    return path.stem, ok, int(ran.group(1)) if ran else 0, seconds, out


def split_streams(serial, count):
    """Browser files over `count` streams, biggest first onto the stream with the least work so far."""
    streams = [[] for _ in range(max(1, min(count, len(serial))))]
    load = [0] * len(streams)
    for path in sorted(serial, key=lambda f: f.stat().st_size, reverse=True):
        i = load.index(min(load))
        streams[i].append(path)
        load[i] += path.stat().st_size
    return streams


@contextlib.contextmanager
def browser_lock():
    """Hold the suite flock: only one runner at a time may drive Chromium, or the timing thresholds flake."""
    with open(LOCK, "a") as lockfile:
        try:
            fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("waiting for the suite lock", flush=True)
            fcntl.flock(lockfile, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lockfile, fcntl.LOCK_UN)


def run_all(pool, serial, jobs, env_extra=None, browser_streams=1, retries=0):
    """Pool and browser phase at the same time; results in a list, in finishing order.
    The pool never waits for the lock; the browser phase holds it from its first file to its last retry."""
    results = []
    lock = threading.Lock()

    def one(path):
        r = run_file(path, env_extra)
        with lock:
            results.append(r)

    def stream(paths):
        for path in paths:
            one(path)

    def browser_phase():
        with browser_lock():
            streams = split_streams(serial, browser_streams)
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(streams)) as ex:
                for f in [ex.submit(stream, paths) for paths in streams]:
                    f.result()
            # A browser file that failed under the load of the other streams runs again alone, on a quiet
            # machine. The summary names it, so a flake is visible; a real failure fails again and stays red.
            for path in serial:
                for _ in range(retries):
                    with lock:
                        first = next(r for r in results if r[0] == path.stem)
                    if first[1]:
                        break
                    again = run_file(path, env_extra)
                    if again[1]:
                        again = (again[0] + " (passed on retry; first run failed)",) + again[1:]
                        again = again[:4] + (again[4] + "\n--- first run, which failed ---\n" + first[4],)
                    with lock:
                        results.remove(first)
                        results.append(again)

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs + 1) as ex:
        futures = [ex.submit(browser_phase)] if serial else []
        futures += [ex.submit(one, p) for p in pool]
        for f in futures:
            f.result()
    return results


def summary(results, wall):
    """File list, then the output of failed and retried files, then the totals: the text always ends
    with `Ran N tests in S s` and `OK` (or `FAILED ...`), which is what the receipt readers look at."""
    lines = []
    for name, ok, n, secs, _ in sorted(results):
        lines.append("%-4s %4d tests %7.1fs  %s" % ("OK" if ok else "FAIL", n, secs, name))
    text = "\n".join(lines) + "\n"
    for name, ok, _, _, out in sorted(results):
        if not ok or "(passed on retry" in name:
            text += "\n===== %s =====\n%s" % (name, out or "(no output)\n")
    total = sum(r[2] for r in results)
    bad = [r for r in results if not r[1]]
    text += "\n" + "-" * 70 + "\nRan %d tests in %.3fs\n\n" % (total, wall)
    text += ("OK" if not bad else "FAILED (files=%d: %s)" % (len(bad), ", ".join(r[0] for r in bad))) + "\n"
    return text, not bad


def changed_files(repo, base):
    """`git diff --name-only BASE` (committed and uncommitted) plus new files; None when git cannot say."""
    def git(*args):
        return subprocess.run(["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              check=True).stdout.decode().splitlines()
    try:
        return git("diff", "--name-only", base) + git("ls-files", "--others", "--exclude-standard")
    except (subprocess.CalledProcessError, OSError):
        return None


def touches(changed, files, watch):
    """Whether a changed path is one of `files` or is in `watch` (a trailing "/" means the whole folder)."""
    return any(c in files or any(c == w or (w.endswith("/") and c.startswith(w)) for w in watch) for c in changed)


def git_head_line(repo):
    def git(*args):
        return subprocess.run(["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, check=False).stdout.decode().strip()
    dirty = [ln for ln in git("status", "--porcelain", "--untracked-files=all").splitlines()
             if not ln[3:].startswith("evidence/") and "__pycache__" not in ln]
    return "sha %s clean=%s" % (git("rev-parse", "HEAD"), "no" if dirty else "yes")


def execute(tests_dir, only, jobs, browser_streams, retries, env_extra=None, skip_browser=False):
    pool, serial = discover(tests_dir)
    if skip_browser:
        serial = []
    if only is not None:
        pool = [f for f in pool if f.stem in only]
        serial = [f for f in serial if f.stem in only]
    started = time.monotonic()
    results = run_all(pool, serial, jobs, env_extra, browser_streams, retries)
    return summary(results, time.monotonic() - started)


def main(argv=None):
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tests-dir", default=str(here))
    ap.add_argument("--jobs", type=int, default=7)
    ap.add_argument("--browser-streams", type=int, default=2, help="browser files run one after another in this many streams")
    ap.add_argument("--retries", type=int, default=1, help="reruns of a failed browser file, alone, at the end")
    ap.add_argument("--receipt", metavar="DIR")
    ap.add_argument("--tz", action="store_true", help="with --receipt: also the time files under TZ=America/New_York")
    ap.add_argument("--if-changed", metavar="BASE", help="with --receipt, instead of --tz: skip the browser files and the "
                    "time pass unless `git diff BASE` (or a new file) touches what they load; the receipt names each skip")
    ap.add_argument("--repo", default=str(here.parent), help="the git repo for the receipt's sha line and --if-changed")
    ap.add_argument("--also", action="append", default=[], metavar="FILE", help="extra file for the --tz run")
    args = ap.parse_args(argv)
    if args.tz and not args.receipt:
        ap.error("--tz needs --receipt")
    if args.if_changed and (not args.receipt or args.tz):
        ap.error("--if-changed needs --receipt and excludes --tz")

    only = set(TZ_FILES) | {Path(a).stem for a in args.also}
    repo = Path(args.repo)
    tests_dir_name = Path(args.tests_dir).resolve().name
    skip_browser = skip_tz = False
    notes = ""
    if args.if_changed:
        changed = changed_files(repo, args.if_changed)
        if changed is None:
            notes = "note: git diff %s failed, nothing skipped\n" % args.if_changed
        else:
            browser_tests = {"%s/%s.py" % (tests_dir_name, f.stem) for f in discover(args.tests_dir)[1]}
            skip_browser = not touches(changed, browser_tests, BROWSER_WATCH)
            skip_tz = not touches(changed, {"%s/%s.py" % (tests_dir_name, n) for n in only}, TZ_WATCH)
    # The full --tz run must not skip the claude-dependent mod test: without `claude` it fails.
    text, ok = execute(args.tests_dir, None, args.jobs, args.browser_streams, args.retries,
                       {"SQUAD_REQUIRE_CLAUDE": "1"} if args.tz else None, skip_browser=skip_browser)
    text += notes
    if skip_browser:
        text += "skipped browser files: no browser test or watched source changed since %s\n" % args.if_changed
    print(text, end="")
    outputs = {"suite-default.txt": text}
    if skip_tz:
        outputs["suite-tz.txt"] = "skipped: no time file or watched source changed since %s\n" % args.if_changed
    elif args.tz or args.if_changed:
        print("\n--- TZ=America/New_York LC_ALL=C: %s ---" % ", ".join(sorted(only)), flush=True)
        tz_text, tz_ok = execute(args.tests_dir, only, args.jobs, args.browser_streams, args.retries, TZ_ENV)
        print(tz_text, end="")
        outputs["suite-tz.txt"] = tz_text
        ok = ok and tz_ok
    if args.receipt:
        out_dir = Path(args.receipt)
        out_dir.mkdir(parents=True, exist_ok=True)
        head = git_head_line(repo)
        for name, body in outputs.items():
            (out_dir / name).write_text(head + "\n" + body, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
