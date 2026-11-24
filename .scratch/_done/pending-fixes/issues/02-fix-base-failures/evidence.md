# 02 Fix the tests that fail on main

## Review

AC trace:
- AC1 | the 6 named tests, `python3 -m unittest discover -s tests -p <file>.py` (list, demo, panels, no_bare_bash, po_inbox_mod) | all OK on this branch; no skip added, no test deleted (13/13, 13/13, 58/58, 6/6, 3/3 tests)
- AC2 | `test_squadboard_list.py`, `test_squadboard_panels.py` under `python3 /tmp/clk/run_moved.py <file>` (clock +400 days: time.time, datetime.now) | OK, OK; demo is relative to its own `now` (see below)
- AC3 | cause of the other two: see Causes
- AC4 | `grep -rl` hits of every touched file, run: grid, tasks, page, active, agents, files, board_fixtures, inbox, hooks_json | OK

## Causes
- Squadboard fixtures (test defect, one demo code defect). `last_active` is the newest of message ts, file mtime and branch commit time; `copy_fixture` shifted message ts to the fixture clock but left file mtimes and git commit dates at the real time of the copy, so once the real date passed 2026-11-04 `last_active` read today (T04_AC1). Fix in `tests/board_fixtures.py`: pin mtimes (now - 30 d) and commit dates (`pin_clock=True`).
  The panels tests (T12, T14) measured on the real clock: T12 inbox age came from the server clock (`srv.clock` now fixed in `payloads12`); T14 file times came from real mtimes of the files and folders the test writes (now pinned to the page clock's day in `payloads14`).
- Demo T37_AC11 was a real code defect in `bin/squadboard_demo.py`: it made E1/E2 "25 minutes old" by matching stamps that start `2026-11-03`, but `copy_fixture(now=today)` had already shifted them, so after 4 Nov the match missed and E1 read "17 d ago". It now matches by the unshifted day. The demo itself passes `pin_clock=False` (its files and commits stay live, as a demo wants).
- `test_no_bare_bash` (stale test, real hazard): `tests/test_herdr_bg.py` launched `[shutil.which("bash"), script]`, which on Windows resolves the WSL launcher, and its skip check used a `("bash", BASH)` pair the scanner reads as an argv. Converted: `BASH = winlaunch.bash()`, the check uses a dict. No allowlist entry added, `TESTS_TO_CONVERT` stays empty. Skip behaviour of that file is unchanged (it skipped before too, when bash or jq is missing).
- `test_plugin_test_passes` (stale test helper, no code defect in `hooks/po-inbox/`): by hand, `claude plugin test .` gave 639 pass, 8 fail, all 8 band row counts (`rowsOfTree` 2, expected 1). The engine (Claude Code 2.1.330) now draws the harness's own `ENGINE` stub (`boot`'s `ui.render`, `part.plugin=test`) beside the mod's part, and the helper counted it as a row. Fix: `rowsOfTree` skips `part.plugin === 'test'` (`testkit.ts`); one test picks the `squad` part of the wrapper (`list.test.ts`). After: 647 pass, 0 fail, rc 0. No skip added, no test removed.

## Behaviour
- T2 clock moved +400 days (`/tmp/clk/run_moved.py`, patches time.time and datetime.now/utcnow in the process): list 13 OK; panels 58 OK. Real clock: list 13 OK, demo 13 OK, panels 58 OK, no_bare_bash 6 OK, herdr_bg 6 OK, po_inbox_mod 3 OK.
- Demo with a moved clock was not run (the demo launches child processes; its data is relative to its own `now` by design).
- SQ-10 (bin/ changed): test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK.
- Also: test_hooks_json OK (references herdr-bg).
- `claude plugin test .` direct: `647 pass, 0 fail` rc 0.

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | the 6 named tests, unittest per file: all OK | - | - |
| AC2 | run_moved.py +400 d on list and panels: OK | - | - |
| AC3 | causes named in ## Causes | - | - |
| AC4 | grep -rl hits run: all OK | - | - |
