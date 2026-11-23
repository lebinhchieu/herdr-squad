
sha: 5773a20
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
| AC1 | test_squad_watchdog manager tests, Ran 104 OK | cd tests; python3 -m unittest -q test_squad_watchdog test_squad_log_message test_squad_start test_squad_spawn test_squadtask test_windows_safe test_utf8_helpers test_instructions (5773a20, detached worktree) -> Ran 347 OK; read decide() diff: team_working excludes role manager and its bg_busy; working kept for all_blocked/stop | live: base vs 5773a20 scratch tick; Manager-only working -> idle start + nudges; sleep still counts Manager (evidence/03/qa-b.md) PASS |
| AC2 | test_squad_watchdog blind tests | same run; read tick() blind branch and decide() blind_logged flag | live: blind logged+sent once over 5 ticks; Manager route when TL absent; no blind with goals PASS |
| AC3 | test_squad_watchdog wsl test | same run; ls -l /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe exists; read suspend_cmd/suspend diff | live: bwrap sandbox, PATH stub / /mnt/c stub / neither -> failure log names path; nothing suspended PASS |
| AC4 | git diff ADR 0028 + docstring | git diff da9c43a 5773a20 -- docs/adr/0028-watchdog-follows-goals-file.md bin/squad-watchdog (docstring) | live: ADR 0028 amendment line and --help idle line read PASS |
| AC5 | grep 0.10.8 in plugin.json, tests: none | grep -rn 0\.10\.8 .claude-plugin tests -> none (only changelog history and .scratch hit) | live: grep 0.10.8 plugin.json and tests/ rc=1; version 0.10.9; 161 tests OK PASS |

## QA whitebox

### QA whitebox, task 03, sha 5773a20: PASS

Ran from tests/ in a detached worktree: test_squad_watchdog test_squad_log_message test_squad_start test_squad_spawn test_squadtask test_windows_safe test_utf8_helpers test_instructions -> Ran 347, OK. Read the diff of bin/squad-watchdog, ADR 0028, plugin.json. powershell.exe exists at the /mnt/c path on this host. Version grep: no 0.10.8 in plugin.json or tests.

#### Follow-ups (not blocking)
- Blind flag `blind_logged` clears when the blind condition ends, not when the idle spell ends: a scope blind for days logs once (AC says "a later spell may log again"). Fine for AC; revisit if Chieu wants a repeat.
- While the target pane is blocked, tick() logs `blind: N ...` plus `blind held` every pass (bin/squad-watchdog ~540-547: log before the is_blocked check). The nudge branch logs only the held line. Move the first log after the check.
- Blind goes to the Team Lead in a scope home (route(), same as nudges); ticket text says Manager. Developer's note explains it; accepted.
- changelog.md has no 0.10.9 entry (not in Files:).

## QA blackbox

### QA blackbox, task 03 (watchdog), sha 5773a20 (base 02 passed da9c43a)

Run: `squad-watchdog tick --now <UTC>` from the 5773a20 worktree vs `bin/` of main (205432a), in scratch squads under /tmp/qab03 (own repo dir with `.scratch/scr/issues`, roster, scope.md; stub `herdr` on PATH answering `agent list` from a fixture and logging every call; SQUAD_DIR/SCOPE_DIR/GOAL_DIR set to the scratch home). Never run against wpw. Sleep proofs: SQUAD_WATCHDOG_SLEEP_CMD=touch marker, or a `bwrap` sandbox with /mnt/c hidden and a stub powershell.exe (nothing suspended). Scripts: /tmp/qab03/{scen,sl,wsl}.sh.

| AC | live/shot | What I did | What I saw | Result |
|---|---|---|---|---|
| 1 | live | Roster Manager+Team Lead+Dev, tickets 01 `Status: ready`, 02 `State: building`; herdr list: Manager `working`, others `idle`; ticks 10:00, 10:06, 10:16 | base: no log, no nudge (Manager holds the spell). 5773a20: `idle start: nobody works and work waits (01 ready, 02 building)`, 5 min and 15 min nudges to the Team Lead. | PASS |
| 1 | live | Same with goals.md (1 goal `in progress`), only Manager working | base: no start; 5773a20: `idle start: nobody works and goals are open`, nudge at 10:06 | PASS |
| 1 | live | Dev `working`, Manager idle | no idle start (a non-Manager worker still holds the spell) | PASS |
| 1 | live | sleep-when-idle on, only Manager working, 7 min | no `sleep pc`, marker not created (Manager still counts for machine_working). Control, all idle: `sleep pc: team idle with open tickets`, marker created, switch off | PASS |
| 2 | live | 3 tickets with no Status/State line, no goals file, herdr all idle, ticks 10:00 10:01 10:06 10:16 10:17 | one log `blind: 3 tickets, none with a status` and one `herdr agent prompt scr-tl blind: ...` at 10:00 only (same route as nudges); Team Lead absent from herdr list -> `route: blind -> scr-mgr (team lead absent)` and sent to the Manager. Base: nothing. | PASS |
| 2 | live | blind tickets, goals.md with a row | no blind line (old goal path used) | PASS |
| 2 | live | blind, then ticket 01 gets `Status: ready` | blind_logged reset; normal `idle start` logged next | PASS |
| 3 | live | WSL host (this one). Sandbox hides /mnt/c; (a) stub powershell.exe on PATH, (b) stub only at /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe, (c) neither | (a) PATH stub called, (b) /mnt/c stub called, with the SetSuspendState command; (c) log `suspend failed ([Errno 2] No such file or directory: 'powershell.exe'; not on PATH and not at /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe)`. Nothing suspended. | PASS |
| 4 | live | read ADR 0028 tail and `squad-watchdog --help` | ADR line `Amended by watchdog-blind 03: the Manager is not counted as working for the idle test ...; all_blocked, stop and sleep still count every agent.` Help text reads "Idle = nobody in the roster, the Manager not counted, is working" | PASS |
| 5 | live | `grep -rn '0\.10\.8' .claude-plugin/plugin.json` ; `grep -rln '0\.10\.8' tests/` | rc=1 both (no hit); version `0.10.9` | PASS |
| tests | live | `cd tests; python3 -m unittest -q test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions test_squadtickets` | Ran 161, OK | PASS |

Follow-ups (not AC failures, SQ-4):
1. Blind is logged once per blindness, not per idle spell. After the first log it is not logged again while the same tickets stay status-less, even after a worker ran and the pod went idle again (blind_logged only resets when a ticket gets a status). AC2 says a later spell "may" log again, so this passes; if the PO wants a re-log per idle spell, it is a small change.
2. Blind is also logged and sent when a Developer is working (pod not idle). Harmless, but it fires on the first tick, not "per idle spell".
3. The blind message goes to the Team Lead (scope-home nudge route), the Manager only when the Team Lead is absent. AC says "to the Manager (same route as nudges)": read as the nudge route.
