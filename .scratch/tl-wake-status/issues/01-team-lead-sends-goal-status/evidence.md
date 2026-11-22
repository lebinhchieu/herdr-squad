# 01 Team Lead sends the Manager the goal status

## Behaviour
With rows in `goals.md`, the Team Lead nudge (5 and 15 min) now names every open goal (blocked ones in the existing "Manager's" sentence, the rest as "Open goals: ..."). When no ticket is open it also asks for one line to the Manager: each goal is done when all its tickets passed, else blocked with the reason; the Manager updates `goals.md`, the Team Lead never edits it. With an open ticket the goal-status ask is left out; no goals -> old wording.

SQ-10 and targeted run (from `tests/`): `python3 -m unittest test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions test_squad_start test_squad_log_message test_squadtask` -> Ran 217 tests, OK.

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_watchdog TeamLeadTest.test_goal_status_is_asked_of_the_team_lead_when_no_ticket_is_open | | |
| AC2 | TeamLeadTest.test_goal_status_is_not_asked_while_a_ticket_is_open_and_without_goals | | |
| AC3 | same AC1 test (G2 blocked named as the Manager's) | | |
| AC4 | existing watchdog rows pass unchanged (85 OK) | | |
| AC5 | the two tests above | | |
| AC6 | docstring "Who is told"; ADR 0028 Consequences line | | |
| AC7 | the 217-test run above | | |
| AC8 | plugin.json 0.10.3; changelog v22 | | |
| AC9 | - (QA blackbox live check) | | |

## Review
AC trace:
AC1 | tests/test_squad_watchdog.py TeamLeadTest.test_goal_status_is_asked_... | cd tests; python3 -m unittest test_squad_watchdog
AC2 | TeamLeadTest.test_goal_status_is_not_asked_... | same
AC3 | AC1 test | same
AC4 | existing rows | same
AC5 | both tests | same
AC6 | grep -n "one-line" bin/squad-watchdog; grep -n "reports goal status" docs/adr/0028-*.md | grep -c .
AC7 | 217 tests | see Behaviour
AC8 | grep -rn '0\.10\.2' .claude-plugin/ (no hit) | grep
AC9 | QA blackbox
See `## Checks`.
