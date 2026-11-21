# 01 Fix the overrides-file test

## Review
Cause: a code defect, not a stale test. `bin/squad-spawn:503` runs `start_err=$(herdr agent start ... 2>&1) || {`. When `agent start` exits 1 with no output (the test's fake herdr does this), `start_err` is empty, the `agent_pane_busy` branch is skipped, and `if [[ -n $start_err ]]` (the only exit) is false. The script falls through, rewrites `roles/dev-1.overrides` (line ~545) and exits 0. Proof by run: base run (evidence/base/test_squad_spawn.txt) fails at test line 475 with `0 == 0`; with the one-line fix the same test passes. Fix: when the failure has no output, set `start_err` to a message, so the existing branch prints it, emits `not_ready` and exits 1 before the overrides file is touched. The test is unchanged.

AC trace
- AC1 | tests/test_squad_spawn.py (107 tests OK, 0 skipped) | `python3 -m unittest discover -s tests -p test_squad_spawn.py`
- AC2 | this Review (cause named, test kept) | read
- AC3 | test_squad_start 49, test_squad_log_message 24, test_team_models 19, test_promotion_0_6_0 3, test_squadupgrade 31, test_ca_win 9, all OK | same command per file
- T2 | test_a_failed_agent_start_leaves_the_old_overrides_file asserts non-zero exit and `effort=low\n` | in test_squad_spawn

## Behaviour
A failed `agent start` with silent output now exits 1 with "herdr agent start failed with no output" and keeps the old overrides file. SQ-10 (bin/ changed): test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK.

Note: the ticket's literal AC1 command `python3 -m unittest tests.test_squad_spawn` fails with ModuleNotFoundError (winlaunch) on base and on the fix, because tests/ is not a package. Run it as `cd tests && python3 -m unittest test_squad_spawn`, or with discover as above.
