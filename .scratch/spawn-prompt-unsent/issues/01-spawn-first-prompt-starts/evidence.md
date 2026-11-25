# Evidence: 01 squad-spawn: the first prompt starts the agent, and stdout says so

## Review

AC trace: AC1 test_prompt_waits_for_interactive_ready; AC2 test_first_prompt_idle_gets_two_enters_then_works (2 send-keys, started true, no warning); AC3 test_first_prompt_never_working_warns_and_marks_unsent (3 send-keys, one warning, exit 0, started false, marker `tl-1`); AC4 blocked / no-prompt tests assert started null, no marker; `--dry-run` exits before the new code (existing dry-run tests); AC5 env vars SQUAD_SPAWN_START_WAIT, SQUAD_SPAWN_READY_WAIT, SQUAD_SPAWN_POLL, tests use poll 0.05 and finish in under 2 s each, worst case 76 s in Design notes; AC6 Behaviour.

/mattpocock-skills:code-review since 4049f8e (Standards + Spec sub-agents). Findings and action:
- Wait lengths scale with SQUAD_SPAWN_POLL: documented in a code comment and Design notes (fixed).
- Ready wait blocks 20 s on a trust dialog: fixed, no wait while agent_status is blocked.
- Spec: Design notes empty: written. Review/Behaviour: this section and Behaviour. AC6/SQ-10 runs: in Behaviour.
- agent_field used once / start_wait repeats the pipeline; terse names rc, rdy: left, judgement calls, the loop is small.
- Empty marker when SQUAD_NAME unset: intended (ticket: "or empty"); ticket 02 falls back to Team Lead.
- Growing gaps not timed in a test: left, the counts 2..5 B are in the code and Design notes; a timing test would sleep.
- Silent ready-wait timeout: left, bounded as the ticket asks; started false/null is the trace.

## Behaviour

Run on the final sha, from tests/ (`python3 -m unittest <file>`):
- AC1-AC5: test_squad_spawn: Ran 123 tests ... OK (new: test_prompt_waits_for_interactive_ready, test_first_prompt_idle_gets_two_enters_then_works, test_first_prompt_never_working_warns_and_marks_unsent; blocked and no-prompt tests assert `started` null).
- AC6: test_squad_respawn OK (34); grep hits test_squad_start, test_squadtask, test_squad_watchdog, test_squadruntime, test_team_lead_perms, test_squad_manager_guard, test_squad_usage, test_session_lookup, test_old_language_inventory, test_rules_contract, test_templates, test_winlaunch, test_crlf_squad_files, test_squadsettings, test_team_models: all OK.
- SQ-10: test_windows_safe OK (14), test_utf8_helpers OK (14), test_instructions OK (16).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_prompt_waits_for_interactive_ready: OK | - | - |
| AC2 | test_first_prompt_idle_gets_two_enters_then_works: OK | - | - |
| AC3 | test_first_prompt_never_working_warns_and_marks_unsent: OK | - | - |
| AC4 | test_a_blocked_agent_gets_no_enter, test_no_prompt_means_no_status_wait: OK | - | - |
| AC5 | env vars in Design notes, worst case 76 s; tests under 2 s | - | - |
| AC6 | targeted suites listed in Behaviour: OK | - | - |
