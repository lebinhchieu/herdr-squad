# 02 Goal-status line names the goals and has no bare type word

## Behaviour
With rows in `goals.md` and no open ticket, the Team Lead nudge (5 and 15 min) asks the Manager one line per open (not `blocked`) goal, naming its id: `goal <id> done` or `goal <id> blocked: <reason>`, with each id filled in (e.g. `goal G1 done` or `goal G1 blocked: <reason>`). The word `STATUS` is gone from the Team Lead text. Blocked goals stay only in the "Manager's" sentence. Ticket-open, blocked-only and no-goals texts are unchanged.

SQ-10 and targeted run (from `tests/`): `python3 -m unittest test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions test_squad_start test_squad_log_message test_squadtask` -> Ran 217 tests, OK (hits of `grep -rl "squad-watchdog\|team_lead_nudge" tests/`: watchdog, start, log_message, squadtask, plus the three SQ-10 files).

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_watchdog TeamLeadTest.test_goal_status_is_asked_of_the_team_lead_when_no_ticket_is_open (G1, G3 named with id, no STATUS, G2 absent from ask) |  |  |
| AC2 | TeamLeadTest.test_goal_status_is_not_asked_while_a_ticket_is_open_and_without_goals |  |  |
| AC3 | the two tests above (STATUS absent in ask, ticket-open, blocked-only, no-goals) |  |  |
| AC4 | 217-test run in Behaviour |  |  |
| AC5 | git diff b779afd --stat: bin/squad-watchdog, tests only; plugin.json untouched; docstrings updated |  |  |
| AC6 | - (QA blackbox live check) | - |  |

## Review
AC trace:
AC1 | TeamLeadTest.test_goal_status_is_asked_... | cd tests; python3 -m unittest test_squad_watchdog
AC2 | TeamLeadTest.test_goal_status_is_not_asked_... | same
AC3 | both tests | same
AC4 | 217 tests | see Behaviour
AC5 | git diff --stat b779afd | git diff --stat
AC6 | QA blackbox | squad-watchdog tick on scratch home
See `## Checks`.
