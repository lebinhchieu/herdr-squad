# 01 Blocked goals get no idle nudge

## Review
AC trace:
- AC1 | tests/test_squad_watchdog.py::GoalsTest::test_all_blocked_goals_get_no_nudge_one_log_line_and_the_watchdog_keeps_running | `cd tests && python3 -m unittest test_squad_watchdog`
- AC2 | ...::test_mixed_goals_nudge_names_only_the_in_progress_ones | same
- AC3 | ...::test_goal_turning_blocked_stops_the_nudges_and_back_to_in_progress_starts_a_fresh_spell | same
- AC4 | existing tests (blocked-pane wake, stop, no-goals-file, team lead routing) | same
- AC5 | tests/test_squad_watchdog.py, 88 tests OK | same
- AC6 | `git diff main -- bin/squad-watchdog docs/adr/0028-watchdog-follows-goals-file.md` | docstring "Goals:" and ADR Decision line 2
- AC7 | see Behaviour | below
- AC8 | QA blackbox live check | `squad-watchdog tick --now` on scratch home

## Behaviour
Blocked goals no longer count as idle work: `waiting()` uses `active_goals` (`in progress` only). All open goals blocked: one `open goals are all blocked` log line per spell, no nudge, no stop. Mixed: nudge text lists only in-progress goals. blocked -> in progress starts a fresh spell.

SQ-10 / AC7 results (python3 -m unittest, from tests/):
- test_squad_watchdog: 88 OK
- test_windows_safe: 14 OK
- test_utf8_helpers: 14 OK
- test_instructions: 16 OK
- grep -rl "squad-watchdog" tests/ hits: test_squad_start, test_squad_log_message, test_squadtask: 49 OK, 24 OK, 15 OK

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_all_blocked_goals_get_no_nudge_one_log_line_and_the_watchdog_keeps_running OK |  |  |
| AC2 | test_mixed_goals_nudge_names_only_the_in_progress_ones OK |  |  |
| AC3 | test_goal_turning_blocked_stops_the_nudges_and_back_to_in_progress_starts_a_fresh_spell OK |  |  |
| AC4 | existing watchdog tests OK |  |  |
| AC5 | 88 OK |  |  |
| AC6 | git diff main (docstring, ADR) |  |  |
| AC7 | quoted in Behaviour |  |  |
| AC8 | none: live check is QA blackbox (unit tests cover tick via decide) |  |  |
