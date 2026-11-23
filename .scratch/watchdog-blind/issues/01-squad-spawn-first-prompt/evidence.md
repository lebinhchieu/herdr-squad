# Evidence: 01 squad-spawn: the first prompt starts the agent

## Review

AC trace (Dev) | see `## Checks`
AC1 | test_squad_spawn::test_first_prompt_working_at_once_sends_no_enter | cd tests; python3 -m unittest test_squad_spawn
AC2 | test_first_prompt_idle_gets_one_enter_then_works | same
AC3 | test_first_prompt_never_working_warns_and_still_succeeds (exit 0, JSON status ready, stderr line) | same
AC4 | test_no_prompt_means_no_status_wait; the wait sits inside `if [[ -n $prompt ]]`, after the `--dry-run` exit | same
AC5 | the three tests above (a)(b)(c); the 111 earlier tests unchanged | same

## Behaviour
Code: `bin/squad-spawn` after `herdr agent prompt`: poll `herdr agent get` every 0.5 s for `working` (SQUAD_SPAWN_START_WAIT seconds, default 15); not working: one `herdr agent send-keys <name> Enter`, poll again; still not: stderr `warning: <name> did not start on its first prompt; send it a message`. Exit status and stdout JSON unchanged. A status that cannot be read (get fails, no field) counts as unknown: no resend, no warning.
Stub: `tests/squadtest.py` fake herdr `agent get` prints `agent_status` (env AGENT_STATUS, default `working`; AGENT_STATUS_AFTER_KEYS once `agent send-keys` is logged; with AGENT_STATUS set a started agent is up).
Run from `tests/`, all OK: test_squad_spawn 115 (111 + 4 new, 28 s), crlf_squad_files 6, squad_close 79, squad_label 14, squad_respawn 33, squad_retire 4, squadruntime 74, squadsettings 25, squad_start 49, squadupgrade 45, squad_watchdog 89, team_lead_perms 14, team_models 19.
SQ-10: test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK.
`git diff --name-only 205432a`: bin/squad-spawn, tests/squadtest.py, tests/test_squad_spawn.py (plus the .scratch ticket files).
Respawn: `squad-respawn` runs `squad-spawn` with a prompt; test_squad_respawn 33 OK.
Not run: the full suite.
## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_spawn` 115 OK (working_at_once) |  |  |
| AC2 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
| AC3 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
| AC4 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
| AC5 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
