# Evidence: 02 watchdog wakes the spawner of an agent that never started

## Review

AC trace: AC1 test_ac1_idle_agent_after_2_minutes_tells_the_spawner_once_and_never_sends_enter (1 min: none; 2 and 5 min: exactly one prompt to `t-tl-s1` naming the agent and `herdr agent send-keys t-dev-s1 Enter`; marker kept); AC2 test_ac2_working_gone_or_retired_... (working, gone, retired: marker removed, no message; blocked: marker kept, no message); AC3 test_ac3_a_missing_spawner_... (spawner absent: Team Lead; Team Lead absent too: Manager); AC4 plugin.json 0.11.3, `grep -rn '0\.11\.2' .claude-plugin/` prints nothing, changelog v34; AC5 Behaviour; AC6 promote.md.

/mattpocock-skills:code-review since aeceb05 (Spec sub-agent; Standards checked against CLAUDE.md test economy). Findings and action:
- Goal home does not scan scope homes' roles/: left on purpose. A scope's own watchdog handles its markers (the docstring: scope panes are woken by their own scope watchdogs), and squad-spawn writes the marker into the agent's own home.
- Duplicate send if the marker is rewritten (new mtime): intended, a new spawn is a new marker.
- Failed send retries each pass: same as wakes; left.
- Held-when-target-blocked log line is not in the ticket: kept, same pattern as wakes, nothing is sent into a blocked pane.
- promote.md, Design notes, Review, Behaviour: written.
- Missing-spawner test initially failed: fallback counted roster rows that were gone as present; fixed (only live or herdr-listed names are targets).

## Behaviour

Run on the final sha, from tests/ (`python3 -m unittest <files>`), 401 tests together: OK.
- AC1-AC3: test_squad_watchdog: Ran 117 tests OK (3 new in UnsentMarkerTest).
- AC4: `grep -rn '0\.11\.2' .claude-plugin/` prints nothing; plugin.json `"version": "0.11.3"`.
- AC5: grep hits of `squad-watchdog` in tests/: test_squad_start, test_squad_watchdog, test_squad_log_message, test_squadtickets, test_squadtask, test_squad_spawn: all OK.
- SQ-10: test_windows_safe, test_utf8_helpers, test_instructions OK.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_ac1_idle_agent_after_2_minutes_tells_the_spawner_once_and_never_sends_enter: OK | - | - |
| AC2 | test_ac2_working_gone_or_retired_removes_the_marker_...: OK | - | - |
| AC3 | test_ac3_a_missing_spawner_falls_back_to_the_team_lead_then_the_manager: OK | - | - |
| AC4 | grep 0.11.2 .claude-plugin/: empty | - | - |
| AC5 | six `squad-watchdog` hit files: OK | - | - |
| AC6 | promote.md | - | - |
