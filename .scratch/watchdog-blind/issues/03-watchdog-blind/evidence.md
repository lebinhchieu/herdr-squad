## Behaviour
- Manager `working`, rest idle, goals not recorded, ticket waiting -> `start` event; a working Developer still holds the spell; a Manager bg token does not. `stop`/`all_blocked` still count every agent.
- Blind: tickets with no `Status:`/`State:` -> log `blind: 3 tickets, none with a status` once, sent to the Team Lead (route); new spell logs again; 0 tickets, one status, or goals recorded -> none.
- WSL `suspend_cmd()`: PATH, else `/mnt/c/.../powershell.exe`, else bare; `suspend()` failure names the path. Nothing suspended (subprocess patched).
- Run from `tests/`: `test_squad_watchdog` Ran 104 OK; `test_squad_log_message` 24, `test_squad_start` 49, `test_squad_spawn` 111, `test_squadtask` 15 OK; [SQ-10] `test_windows_safe` 14, `test_utf8_helpers` 14, `test_instructions` 16 OK.
- Version: `grep -rn '0\.10\.8' .claude-plugin tests` -> no hits.

## Review
AC trace (checks table: see `checks.md`)
- AC1 | tests/test_squad_watchdog.py::test_a_working_manager_does_not_hold_the_idle_spell_but_still_counts_for_stop_and_sleep, ::test_goals_all_blocked_or_done_with_a_working_manager_still_follow_the_all_agents_rule | `cd tests; python3 -m unittest -q test_squad_watchdog`
- AC2 | ::test_blind_is_logged_and_sent_once_per_spell_and_again_in_a_new_one, ::test_blind_needs_tickets_none_with_a_status_and_no_goals | same
- AC3 | ::test_wsl_suspend_cmd_takes_path_then_mnt_c_then_the_bare_name_and_a_failure_names_the_path | same
- AC4 | `git diff 205432a -- docs/adr/0028-watchdog-follows-goals-file.md bin/squad-watchdog` (docstring line 16) | read
- AC5 | `grep -rn '0\.10\.8' .claude-plugin tests` | none

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_watchdog manager tests, Ran 104 OK | | |
| AC2 | test_squad_watchdog blind tests | | |
| AC3 | test_squad_watchdog wsl test | | |
| AC4 | git diff ADR 0028 + docstring | | |
| AC5 | grep 0.10.8 in plugin.json, tests: none | | |
