# 06 Watchdog wakes the Team Lead

## Review

AC trace (all run from `tests/`: `python3 -m unittest <module>`)

- AC1 | test_squad_watchdog.TeamLeadTest.test_ac1_the_nudge_goes_to_the_team_lead_with_its_own_wording | unittest
- AC2 | test_squad_watchdog.TeamLeadTest.test_ac2_absent_then_blocked_team_lead_falls_back_to_the_manager_and_a_blocked_manager_holds | unittest
- AC3 | test_squad_watchdog.TeamLeadTest.test_ac3_a_blocked_developer_wakes_the_team_lead_and_a_blocked_team_lead_the_manager | unittest
- AC4 | test_squad_watchdog.TeamLeadTest.test_ac4_a_goal_home_nudges_the_goal_manager_and_wakes_no_scope_pane | unittest
- AC5 | test_squad_start.StartTest.test_a_scope_a_goal_and_an_in_goal_scope_start_a_watchdog_and_a_dry_run_or_off_does_not | unittest
- AC6 | sample below | `herdr agent list`
- AC7 | test_squad_watchdog (all other rows unchanged, none rewritten) | unittest
- AC8 | test_windows_safe, test_utf8_helpers, test_instructions | unittest
- AC9 | test_squad_watchdog, test_squad_start, test_squad_log_message, test_squadtask (the `grep -rl` hits) | unittest; live check below

## Behaviour

Targeted run: `cd tests && python3 -m unittest test_squad_watchdog test_squad_start test_squad_log_message test_squadtask test_windows_safe test_utf8_helpers test_instructions` -> Ran 216 tests, OK (SQ-10 files included).

Live check, scratch scope `plug/scopes/demo`, stub `herdr`, `squad-watchdog tick --herdr-json`: 5 min nudge -> `plug-tl-demo`; Team Lead then `blocked` -> a `route:` line and the 15 min nudge -> `plug-mgr-demo`:

```
08:05:00Z nudge 5 min to plug-tl-demo: sent: WATCHDOG: nobody has worked for 5 minutes ... Message the Developer who owns a ticket, spawn one within your cap, or `ASK` the Manager.
08:15:00Z route: 15 min idle -> plug-mgr-demo (team lead blocked)
08:15:00Z nudge 15 min to plug-mgr-demo: sent: WATCHDOG: still nobody working after 15 minutes ...
```

AC6 sample source: a real `herdr agent list` on this machine, 2026-11-21 (fields `agent_status` `idle` and `done`, name in `terminal_title_stripped`):
`guardian-qab-cvscope idle`, `guardian-tl-cvscope done`, `guardian-qaw-cvscope idle`. Team Lead name `plugin-tl-tl-always` is from this squad's roster.md (`<squad>-tl-<scope>`). No retired agent was in the live list; retired is the roster `Status` column, handled as before.
