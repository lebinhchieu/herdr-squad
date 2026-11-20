## Behaviour

`python3 -I $SCOPE_DIR/evidence/idle-demo.py <fresh dir>` (worktree's `bin/squad-watchdog tick`, stub herdr json, `--now` 08:00..08:20; "NOT sent" is the demo having no herdr agent). Cases: open goal, blocked with reason, all done -> stops, all done but a dev working -> silent, no file -> as before. Lines cut at 260 characters.

```

### A-open-goal: {'demo-mgr-s1': 'idle', 'demo-dev-s1': 'idle'}; goals: | G1 | Ship the report | in progress | | 2027-01-15 |

2027-01-15T08:00:00Z idle start: nobody works and goals are open (G1 Ship the report: in progress). Agents: demo-mgr-s1 idle, demo-dev-s1 idle
2027-01-15T08:05:00Z nudge 5 min to demo-mgr-s1: NOT sent (no herdr agent in the demo): WATCHDOG: nobody has worked for 5 minutes (since 08:00 UTC) and work is waiting. Open goals: G1 Ship the report: in progress. Agents: demo-mgr-s1 idle, demo-dev-s1 idle. Ch
2027-01-15T08:15:00Z nudge 15 min to demo-mgr-s1: NOT sent (no herdr agent in the demo): WATCHDOG: still nobody working after 15 minutes (since 08:00 UTC). This is the last reminder of this idle period. Open goals: G1 Ship the report: in progress. Agents: demo

status: last pass: 2027-01-15T08:20:00Z; idle since: 2027-01-15T08:00:00Z; open goals: 1; sleep-when-idle: off; wake-ups: on

### B-blocked-reason: {'demo-mgr-s1': 'idle', 'demo-dev-s1': 'idle'}; goals: | G1 | Fix the login | blocked | needs the prod key; inbox item i7 | 2027-01-15 |
| G2 | Old | done | | 2027-01-14 |

2027-01-15T08:00:00Z idle start: nobody works and goals are open (G1 Fix the login: blocked (needs the prod key; inbox item i7)). Agents: demo-mgr-s1 idle, demo-dev-s1 idle
2027-01-15T08:05:00Z nudge 5 min to demo-mgr-s1: NOT sent (no herdr agent in the demo): WATCHDOG: nobody has worked for 5 minutes (since 08:00 UTC) and work is waiting. Open goals: G1 Fix the login: blocked (needs the prod key; inbox item i7). Agents: demo-mgr
2027-01-15T08:15:00Z nudge 15 min to demo-mgr-s1: NOT sent (no herdr agent in the demo): WATCHDOG: still nobody working after 15 minutes (since 08:00 UTC). This is the last reminder of this idle period. Open goals: G1 Fix the login: blocked (needs the prod key

status: last pass: 2027-01-15T08:20:00Z; idle since: 2027-01-15T08:00:00Z; open goals: 1; sleep-when-idle: off; wake-ups: on

### C-all-done-stops: {'demo-mgr-s1': 'idle', 'demo-dev-s1': 'idle'}; goals: | G1 | Ship the report | done | | 2027-01-15 |

2027-01-15T08:00:00Z all goals done; watchdog stops
2027-01-15T08:05:00Z all goals done; watchdog stops

status: last pass: never; idle since: -; open goals: 0; sleep-when-idle: off; wake-ups: on

### D-all-done-but-working: {'demo-mgr-s1': 'idle', 'demo-dev-s1': 'working'}; goals: | G1 | Ship the report | done | | 2027-01-15 |

(no log line: silent)
status: last pass: 2027-01-15T08:20:00Z; idle since: -; open goals: 0; sleep-when-idle: off; wake-ups: on

### E-no-file: {'demo-mgr-s1': 'idle', 'demo-dev-s1': 'idle'}; goals: NO FILE
2027-01-15T08:00:00Z idle start: nobody works and work waits (03 building). Agents: demo-mgr-s1 idle, demo-dev-s1 idle
2027-01-15T08:05:00Z nudge 5 min to demo-mgr-s1: NOT sent (no herdr agent in the demo): WATCHDOG: nobody has worked for 5 minutes (since 08:00 UTC) and work is waiting. Waiting: 03 building. Agents: demo-mgr-s1 idle, demo-dev-s1 idle. Message the agent who own
2027-01-15T08:15:00Z nudge 15 min to demo-mgr-s1: NOT sent (no herdr agent in the demo): WATCHDOG: still nobody working after 15 minutes (since 08:00 UTC). This is the last reminder of this idle period. Waiting: 03 building. Agents: demo-mgr-s1 idle, demo-dev-

status: last pass: 2027-01-15T08:20:00Z; idle since: 2027-01-15T08:00:00Z; open goals: no goals file; sleep-when-idle: off; wake-ups: on
```

Design choices: with goals the spell depends on goals only (a waiting ticket no longer counts); an empty table counts as no file. Stop holds while the sleep-when-idle switch is on (else sleep, which needs a live watchdog, could never fire after all goals are done); it stops on the pass after the PC slept. The stop clears `beat` so `ensure` restarts at once. The "ignore this if you only wait for the PO" line is gone in both modes.

Tests (targeted, from `tests/`): `test_squad_watchdog` 71 OK (44 older + 27 in the new `GoalsTest`: 8 new, 19 inherited from `WatchdogTest`); `test_squad_start` + `test_windows_safe` + `test_utf8_helpers` + `test_instructions` 93 OK; `test_squad_log_message` + `test_squadtask` 40 OK.

## Review

AC trace: see `## Checks`.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_watchdog.GoalsTest.test_read_goals_is_tolerant_and_none_without_a_file`: OK |  |  |
| AC2 | `...GoalsTest.test_open_goal_and_idle_nudges_at_5_and_15_with_status_and_reason`: OK; demo cases A, B |  |  |
| AC3 | `...GoalsTest.test_all_goals_done_and_nobody_working_stops_and_run_returns` (real `run` returns), `...test_all_goals_done_but_an_agent_working_does_not_stop`; demo C, D |  |  |
| AC4 | `...GoalsTest.test_no_goals_file_or_an_empty_table_behaves_as_before`; the 44 older tests OK; demo E |  |  |
| AC5 | `...GoalsTest.test_ensure_starts_once_and_a_second_call_does_nothing`: OK; `ensure` loads squad-start and calls its `watchdog_alive` and `start_watchdog`; `test_squad_start` 49 OK |  |  |
| AC6 | `python3 -m unittest test_squad_watchdog.WakeTest`: OK (blocked wake, held, retry unchanged) |  |  |
| AC7 | `grep -n -e "goals.md" -e ensure bin/squad-watchdog README.md`: docstring and README; `...GoalsTest.test_status_shows_the_open_goal_count`: OK |  |  |
| AC8 | tests (a) to (e) are the five GoalsTest tests named in AC2, AC3, AC4, AC5 rows; no new test file |  |  |
| AC9 | `python3 -I $SCOPE_DIR/evidence/idle-demo.py <fresh dir>` output in `## Behaviour` |  |  |
| AC10 | `squad-evidence checks <evidence.md>`: exit 0; no backslash-pipe in any cell |  |  |
