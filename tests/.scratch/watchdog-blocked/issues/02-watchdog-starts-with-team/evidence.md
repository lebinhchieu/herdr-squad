# 02 Watchdog starts when the team is spawned

## Review
AC trace:
- AC1 | tests/test_squad_start.py::test_squad_start_starts_no_watchdog_for_a_scope_a_goal_an_in_goal_scope_or_a_resume | `cd tests && python3 -m unittest test_squad_start`
- AC2 | tests/test_squad_spawn.py::SpawnWatchdogTest::test_first_non_manager_spawn_starts_the_homes_watchdog_once_and_a_manager_none | `python3 -m unittest test_squad_spawn.SpawnWatchdogTest`
- AC3 | SpawnWatchdogTest::test_a_scope_in_a_goal_also_starts_the_goals_watchdog | same
- AC4 | tests/test_squad_watchdog.py::test_sleep_on_starts_the_homes_watchdog_unless_it_runs | `python3 -m unittest test_squad_watchdog`
- AC5 | `git grep -n "squad-watchdog ensure" templates/` no hit; docstring and README text | diff
- AC6 | SpawnWatchdogTest::test_a_failing_watchdog_start_warns_and_never_fails_the_spawn | same as AC2
- AC7 | the four tests above (extended files, none new, none skipped) | above
- AC8 | `grep -rn "0\.10\.3" .claude-plugin/` no hit; plugin.json 0.10.4; changelog v23 | grep
- AC9 | see Behaviour | below
- AC10 | QA blackbox live check | scratch squad

## Behaviour
`squad-start` no longer calls `start_watchdog`. `squad-spawn` runs `squad-watchdog ensure --home <home>` after a non-Manager spawn (and for the goal home of a scope with `goal:`); failure warns on stderr, stdout stays one JSON line. `squad-watchdog sleep on` runs `ensure` too. START-19b no longer names `ensure`.

AC9 results (python3 -m unittest, from tests/): test_squad_watchdog 89 OK; test_squad_spawn 111 OK; test_squad_start 49 OK; test_squad_log_message 24 OK; test_squadtask 15 OK; test_squad_respawn 33 OK; test_windows_safe 14 OK; test_utf8_helpers 14 OK; test_instructions 16 OK. `grep -rl "squad-watchdog\|start_watchdog\|START-19b" tests/` = log_message, squadtask, start, watchdog, spawn: all run. `squad-process lint` exit 0.

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_start new test OK |  |  |
| AC2 | SpawnWatchdogTest first-spawn test OK |  |  |
| AC3 | SpawnWatchdogTest goal test OK |  |  |
| AC4 | test_sleep_on_starts_the_homes_watchdog_unless_it_runs OK |  |  |
| AC5 | git grep "squad-watchdog ensure" templates/: no hit |  |  |
| AC6 | SpawnWatchdogTest failure test OK |  |  |
| AC7 | 4 tests, no new file |  |  |
| AC8 | grep 0.10.3 .claude-plugin/: no hit |  |  |
| AC9 | quoted in Behaviour; lint exit 0 |  |  |
| AC10 | none: live check is QA blackbox's |  |  |
