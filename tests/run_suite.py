#!/usr/bin/env python3
"""Run the whole suite, one subprocess per test file, in parallel. Same files as `unittest discover -s tests`.

Files that drive a browser (source mentions playwright or chrom) run one after another in a few
streams (--browser-streams) beside the pool: their timing thresholds only hold without many
Chromes at once, so these are never in the pool.
Takes /tmp/squad-suite.lock for the whole run, so two runners never overlap.

    python3 tests/run_suite.py [--jobs N] [--receipt DIR [--tz] [--also test_x]...]
"""
import argparse
import concurrent.futures
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
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")  # the repo has had .pyc files committed
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


def run_all(pool, serial, jobs, env_extra=None, browser_streams=1, retries=0):
    """Pool and browser streams at the same time; results in a list, in finishing order."""
    results = []
    lock = threading.Lock()

    def one(path):
        r = run_file(path, env_extra)
        with lock:
            results.append(r)

    def stream(paths):
        for path in paths:
            one(path)

    streams = split_streams(serial, browser_streams) if serial else []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs + len(streams)) as ex:
        futures = [ex.submit(stream, paths) for paths in streams]
        futures += [ex.submit(one, p) for p in pool]
        for f in futures:
            f.result()
    # A browser file that failed under the load of the other streams runs again alone, on a quiet
    # machine. The summary names it, so a flake is visible; a real failure fails again and stays red.
    for path in serial:
        for _ in range(retries):
            first = next(r for r in results if r[0] == path.stem)
            if first[1]:
                break
            again = run_file(path, env_extra)
            results.remove(first)
            if again[1]:
                again = (again[0] + " (passed on retry; first run failed)",) + again[1:]
                again = again[:4] + (again[4] + "\n--- first run, which failed ---\n" + first[4],)
            results.append(again)
    return results


def summary(results, wall):
    lines = []
    for name, ok, n, secs, _ in sorted(results):
        lines.append("%-4s %4d tests %7.1fs  %s" % ("OK" if ok else "FAIL", n, secs, name))
    total = sum(r[2] for r in results)
    bad = [r for r in results if not r[1]]
    lines += ["", "-" * 70, "Ran %d tests in %.3fs" % (total, wall), ""]
    lines.append("OK" if not bad else "FAILED (files=%d: %s)" % (len(bad), ", ".join(r[0] for r in bad)))
    text = "\n".join(lines) + "\n"
    for name, ok, _, _, out in sorted(results):
        if not ok or "(passed on retry" in name:
            text += "\n===== %s =====\n%s" % (name, out or "(no output)\n")
    return text, not bad


def git_head_line(repo):
    def git(*args):
        return subprocess.run(["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, check=False).stdout.decode().strip()
    dirty = [ln for ln in git("status", "--porcelain", "--untracked-files=all").splitlines()
             if not ln[3:].startswith("evidence/") and "__pycache__" not in ln]
    return "sha %s clean=%s" % (git("rev-parse", "HEAD"), "no" if dirty else "yes")


def execute(tests_dir, only, jobs, browser_streams, retries, env_extra=None):
    pool, serial = discover(tests_dir)
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
    ap.add_argument("--also", action="append", default=[], metavar="FILE", help="extra file for the --tz run")
    args = ap.parse_args(argv)
    if args.tz and not args.receipt:
        ap.error("--tz needs --receipt")

    lockfile = open(LOCK, "a")
    try:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("waiting for the suite lock", flush=True)
        fcntl.flock(lockfile, fcntl.LOCK_EX)

    text, ok = execute(args.tests_dir, None, args.jobs, args.browser_streams, args.retries)
    print(text, end="")
    outputs = {"suite-default.txt": text}
    if args.tz:
        only = set(TZ_FILES) | {Path(a).stem for a in args.also}
        print("\n--- TZ=America/New_York LC_ALL=C: %s ---" % ", ".join(sorted(only)), flush=True)
        tz_text, tz_ok = execute(args.tests_dir, only, args.jobs, args.browser_streams, args.retries, TZ_ENV)
        print(tz_text, end="")
        outputs["suite-tz.txt"] = tz_text
        ok = ok and tz_ok
    if args.receipt:
        out_dir = Path(args.receipt)
        out_dir.mkdir(parents=True, exist_ok=True)
        head = git_head_line(Path(__file__).resolve().parent.parent)
        for name, body in outputs.items():
            (out_dir / name).write_text(head + "\n" + body, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
