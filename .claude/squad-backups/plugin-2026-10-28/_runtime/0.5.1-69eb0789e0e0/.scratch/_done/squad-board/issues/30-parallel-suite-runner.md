Status: resolved
State: done (PASS at 59f1081; in squad/dev-board-19 at 927c5a7)
Task ID: BRD-30
Blocked by: none (71e99f0 only supplies the board tests)
Files touched: `tests/run_suite.py` (new), `tests/test_run_suite.py` (new, small); quick wins edit only the named slow tests in `tests/test_board_events.py`, `test_board_recorder.py`, `test_board_http.py`

# BRD-30: a parallel suite runner and quick wins on the slowest tests

**Done when `python3 tests/run_suite.py` runs the whole suite in about 2.5 min or less on this 16-core machine (now 384 s, 821 tests), exits non-zero on any failure, and `--receipt <dir> --tz` writes the two receipt files the process rule asks for.** Timebox: 45 minutes. PO: "don't waste time". Measurements: `/tmp/mgr-durations.txt` (top 30 tests are 138 s of the 384 s, from real timers).

## Part 1: `tests/run_suite.py` (stdlib only, Python 3.9-safe)

- Find test files with the same rule as `unittest discover -s tests` (`test_*.py`). Run **each file as its own subprocess** (`python3 -m unittest -q <module>` with `tests/` as cwd, same as discover), in a pool of 6 to 8 workers (`concurrent.futures.ThreadPoolExecutor` around `subprocess.run`; `--jobs N` overrides).
- **Browser files run serially in one extra stream**, alongside the pool: any file whose source contains `playwright` or `chrom` (case-insensitive) — today `test_board_page`, `sequence`, `follow`, `alerts`, `panel`. Detect by text, never by a hard-coded list, so a new browser file is serial without anyone remembering. Reason: their timing thresholds (IdleLoopTest fps bands, follow/pause waits) stay green only without 8 parallel Chromes. The extra stream runs the browser files one after another, each its own subprocess.
- Longest files first in the pool (sort by file size, descending) to cut the tail.
- Summary on stdout: per file `OK|FAIL <n> tests <seconds>`, a total line `Ran N tests in S s` and `OK` or `FAILED (failures=…, errors=…)`. A failing file's full output is printed after the summary. Exit 0 only if every file is OK. Count tests from each file's own `Ran N tests` line; a file whose output has no such line counts as FAIL.
- **The flock:** the runner takes `/tmp/squad-suite.lock` itself (`fcntl.flock` on that file, blocking), held until it exits, so `flock … python3 tests/run_suite.py` is not needed and two runners never overlap. Print one line "waiting for the suite lock" if it has to wait.
- **Isolation check (do this before trusting the pool):** the board tests start servers on port 0 and use `tempfile.mkdtemp`, so files should not collide; grep for any fixed port, fixed `/tmp/...` path or shared file and fix or put that file in the serial stream. Say what you found in `dev-evidence.md`.
- **`--receipt <dir>`:** writes `<dir>/suite-default.txt` with first line `sha <git rev-parse HEAD> clean=yes|no` (`clean=no` when `git status --porcelain` shows anything outside `evidence/`; untracked `__pycache__` does not count) and the whole summary after it, ending with `Ran N tests in S s` and `OK`. The `Ran N tests ... OK` tail must match the tail the QA check reads (`Ran N tests in …s` then `OK`).
- **`--tz`** (with `--receipt`): after the default run, runs only the time-handling files — `test_board_timeline`, `test_board_state`, `test_board_tokens`, `test_board_recorder` — plus any file named with `--also <file>` (repeatable), once with `TZ=America/New_York LC_ALL=C` in the environment of the subprocesses, and writes `<dir>/suite-tz.txt` in the same format. If those include a browser file they still run in the serial stream.
- No receipt option: it only prints and exits.

## Part 2: quick wins on the slowest tests (only where the behaviour under test is unchanged)

Take the 10 slowest *non-browser-fps* tests of `/tmp/mgr-durations.txt` and replace a real wait of the default by something that tests the same thing faster. Candidates, in order of saving:
1. `test_board_events.KeepaliveTest.test_default_interval_is_15_seconds` (15 s): assert the constant (`KEEPALIVE_S == 15` or whatever the name is) and test the keepalive behaviour through the existing env knob at 0.2 s. The test must still fail if the default is changed.
2. `test_board_page.ReconnectTest` x3 (about 8 s each): these are browser files and stay in place; shorten only if the page already has a knob for the backoff (a query/test hook); if it does not, **do not add one**, leave them.
3. `test_board_recorder.BackoffTest.test_a_quiet_subscription_is_not_an_outage` and `ReconnectTest.test_a_herdr_that_accepts_and_never_answers_is_an_outage_not_a_hang` (about 5.6 s each): use the existing env knobs for the timeouts.
4. `test_board_http.HerdrFailureTest.test_hanging_herdr_is_killed_after_about_five_seconds` (5 s): assert the constant, and test the kill with the knob if one exists.
5. `test_board_live.RefreshTest` (3 tests of about 3.5 s) and `test_board_events.QuietTest` (4.5 s): only if a knob already exists.

Rules: **no change to `bin/squad-board`** (BRD-28 and 19 are editing it; if a quick win needs a code knob, skip that test and say so). Every changed test still has to fail when the behaviour it covers is broken: for each, make the one-line break by hand (change the constant, or drop the guarded branch), see it fail, restore, and note it in `dev-evidence.md`. Stop after the timebox; list what is not done.

## Technical AC
1. `tests/test_run_suite.py` (fast, no real suite run): file discovery picks `test_*.py`; a file mentioning `playwright` is classified serial and one that does not is parallel (use a temp dir with two stub files); the receipt first line has the `sha <rev> clean=yes|no` shape; the exit code is non-zero when a stub test fails and zero when all pass; a stub file with no `Ran N tests` line counts as FAIL. Stub files are tiny `unittest` modules written in a temp dir (the runner takes a `--tests-dir`).
2. One real run: `python3 tests/run_suite.py --receipt evidence/BRD-30 --tz --also test_board_live` once. Evidence: wall time of the run (target about 2.5 min; if it is more, say which stream was the long one: pool tail or serial browser stream), the number of tests equal to the old `unittest discover` count (count it on the base first, about 821), the two receipt files, load average before and after.
3. Browser tests stay green in that run: no timing-threshold test fails because of the parallel pool. If one does, move its file to the serial stream, never loosen a threshold.
4. Two runs of the new runner in a row are both green (one is the AC 2 run).
5. Part 2: before/after seconds of each changed test, and the break-by-hand note per test.
6. Python 3.9-safe, no `.pyc` committed, nothing under `bin/` touched, one commit.
7. Close every browser and server you start; no `pkill` by pattern.

## After it passes
The suite-receipt AC wording in 19, 22 to 25, 28 and 29 changes to "`python3 tests/run_suite.py --receipt evidence/<ticket> --tz`" (tech-board does that; the runner writes both files). BRD-28 may run before this lands, with the current wording.

## Delivery
Branch `squad/dev-board-N` from `71e99f0` (stacked, Manager creates the worktree); reviewer qaw-board (diff plus one run of the runner; QA does not repeat the full old suite). It merges with the others in BRD-19's integration; quick-win edits in `test_board_recorder.py` may conflict with BRD-28's edits there: resolve by keeping both.

## Comments
- 2026-10-14 tech-board: written on the Manager's ask.
