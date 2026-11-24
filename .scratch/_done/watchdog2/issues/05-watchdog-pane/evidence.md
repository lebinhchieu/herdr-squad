# Evidence 05: the watchdog runs in its own herdr tab

## Behaviour
- Inside herdr, `squad-start` opens one tab labelled `watchdog` (no focus, the Manager's workspace) and types `exec python3 .../squad-watchdog run --home <home> --manager <name>` into it. Test: `WatchdogTabTest.test_a_tab_is_made_in_the_workspace_and_runs_only_the_watchdog`.
- Windows: the pane gets `& '<python>' '<script>' run ...; exit` (`test_windows_types_a_powershell_command_that_exits`).
- herdr failure (exit, timeout, missing): one stderr warning, half-made tab closed, detached process starts (`test_a_failing_tab_or_run_...`, and the end-to-end `StartTest` watchdog test with a herdr whose `pane run` fails).
- `SQUAD_WATCHDOG=off` or a fresh heartbeat: no tab, no process (`test_off_starts_nothing_...`).
- Name `sleep-when-idle` everywhere; no tickets logs `sleep pc: team idle; ...`.

## Sources
- T4: `tests/fixtures/herdr/tab-create.json` is a real `herdr tab create --no-focus --workspace w4G` capture of 2026-11-08 (`.result.tab.tab_id`, `.result.root_pane.pane_id`); its tab was closed at once.
- Run: in `tests/`, `python3 -m unittest test_squad_watchdog test_squad_start` and every hit of grep for `squad-start`, `squad-watchdog`, `sleep-when`: 273 tests OK.
