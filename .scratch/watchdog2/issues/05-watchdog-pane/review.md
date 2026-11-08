## Review
AC trace
AC1 | tests/test_squad_start.py WatchdogTabTest.test_a_tab_is_made_in_the_workspace_and_runs_only_the_watchdog | `cd tests; python3 -m unittest test_squad_start`
AC2 | WatchdogTabTest.test_off_starts_nothing_and_a_live_watchdog_gets_no_second_one; run guard unchanged (git diff) | same
AC3 | same tab test (`--no-focus`, `exec`); failing run closes the tab | same
AC4 | WatchdogTabTest.test_a_failing_tab_or_run_falls_back..., test_outside_herdr..., test_off... | same
AC5 | WatchdogTabTest.test_windows_types_a_powershell_command_that_exits | same
AC6 | grep sleep-when-done bin tests -> none; tests/test_squad_watchdog.py status test | `python3 -m unittest test_squad_watchdog`
AC7 | test_squad_watchdog.py test_with_no_ticket_at_all_the_log_does_not_say_open_tickets | same
AC8 | all of the above | 273 tests OK
