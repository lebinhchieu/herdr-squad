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

<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_spawn` 115 OK (working_at_once) | cd tests; python3 -m unittest -q test_squad_spawn test_squad_respawn test_squad_start test_windows_safe test_utf8_helpers test_instructions (fc1babf: 241 OK; aa63f53: test_squad_spawn + SQ-10 files OK); read the agent_started diff | live: stub herdr, working at once / after 5 s -> no Enter, no warning (evidence/01/qa-b.md) PASS |
| AC2 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; Enter only for idle/done (aa63f53), one send-keys asserted in the log | live: working after Enter -> exactly one send-keys; done forever -> Enter then warning PASS |
| AC3 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; warning on stderr, exit 0, JSON status ready asserted | live: never -> one warning, exit 0, JSON same as base, ~30.7 s PASS |
| AC4 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; wait sits inside `if [[ -n $prompt ]]`; test_no_prompt_means_no_status_wait; blocked test added | live: no --prompt and --dry-run -> no wait, no Enter PASS |
| AC5 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; tests (a)(b)(c) + blocked test read | live: 160 tests OK (spawn, windows_safe, utf8, instructions) PASS |

## QA whitebox

### QA whitebox, task 01, sha fc1babf: FAIL (2 findings, one return)

Ran in a detached worktree from tests/: test_squad_spawn test_squad_respawn test_squad_start test_windows_safe test_utf8_helpers test_instructions -> Ran 241, OK. Read the diff of bin/squad-spawn, tests/squadtest.py, tests/test_squad_spawn.py. Live read-only check: `herdr agent get plugin-qaw-watchdog-blind | jq -r '.result.agent.agent_status // .agent_status // empty'` -> `working` (jq path right).

#### Findings
1. bin/squad-spawn (new `agent_started` / `send-keys` block, ~line 585-592): Enter is sent when the status is anything but `working`, including `blocked`. AC2 says resend only when it "stays idle/done". herdr statuses are idle, working, blocked, done, unknown (`herdr agent wait --help`). A freshly started Claude can sit `blocked` on a dialog (trust folder, permission); an Enter there accepts the default, which no message may do (MSG-10). Pass: resend only when the last status read is `idle` or `done`; `blocked`/`unknown`/unreadable: no Enter. Say in the warning case what was seen is optional. Add one test: status `blocked` -> zero `send-keys` in the log, spawn exit 0 (the warning is fine either way).
2. REV-4 / technical AC T1: the ticket has no `## Design notes` and no real `herdr agent get` sample of an idle/done agent and of a working agent. Pass: paste both (idle or done one from `herdr agent list | jq`, the working one as above) into the ticket's `## Design notes` with the jq output, and state there the choice for an unreadable status (no resend, no warning), which is accepted once finding 1 is fixed.

#### Follow-ups (not blocking)
- The commit also carries ticket drafts `02-ticket-state-reader.md` and `03-watchdog-blind-wsl.md`; the Developers of 02 and 03 committed `02-state-line.md` and `03-watchdog-blind.md`. Merge gives two files for ticket numbers 02 and 03 in .scratch/watchdog-blind/issues/. Team Lead decides which names stay before merge.
- The 4 new tests each wait about 1-2 s (SQUAD_SPAWN_START_WAIT=1); fine.

### Re-check aa63f53: PASS
Findings 1 and 2 fixed: Enter only for idle/done (bin/squad-spawn agent_started), test_a_blocked_agent_gets_no_enter added, `## Design notes` holds real idle and working samples. Ran test_squad_spawn + SQ-10 files: Ran 160, OK.

## QA blackbox

### QA blackbox, task 01 (first prompt starts the agent), sha aa63f53 (supersedes fc1babf)

Run: the real `bin/squad-spawn` of the dev-1 worktree (aa63f53) in a scratch squad /tmp/qab01/proj (git init, squad `s`, scope `sc`, copied settings/process.local.md), `herdr` replaced by a stub on PATH (logs every call; modes: working at once / working after Enter / never / `done` forever / `blocked` / working after 5 s). Spawn of `qa-whitebox qa-w-1 --scope sc --prompt "hello first"`. The stub also swallowed the watchdog start (`herdr pane run`), so no real watchdog or agent started. Never run against wpw. Base compared: main `bin/squad-spawn` (205432a).

| AC | live | What I did | What I saw | Result |
|---|---|---|---|---|
| 1 | live | mode `now` (working right after the prompt); default wait | 1 prompt call, 3 status polls, no `send-keys`, no warning, exit 0 | PASS |
| 1 | live | working only after 5 s (default wait) | no `send-keys`, no warning (the first wait covered it) | PASS |
| 2 | live | mode `after_resend` (working only after Enter) | exactly one `herdr agent send-keys qa-w-1 Enter`, then waits again; no warning; exit 0 | PASS |
| 2 | live | mode `done` forever | one Enter, then the warning (done is treated like idle) | PASS |
| 3 | live | mode `never`, default wait (env unset, or set empty) | one Enter, ~30.7 s total, stderr `warning: qa-w-1 did not start on its first prompt; send it a message` once, exit 0, stdout JSON identical to base's keys/values (name, role, scope, tab, pane, cwd, status `ready`) | PASS |
| 3b | live | mode `blocked` (new in aa63f53) | no Enter, no warning, no wait beyond the first polls; exit 0 | PASS (not in AC, sensible) |
| 4 | live | no `--prompt` | only the existing "spawned without --prompt" warning, no status polls beyond start (2), no send-keys | PASS |
| 4 | live | `--prompt hi --dry-run` | only `would run:` lines; no prompt, no wait | PASS |
| 5 | live | `cd tests; python3 -m unittest -q test_squad_spawn test_windows_safe test_utf8_helpers test_instructions` | Ran 160, OK | PASS |

Note: one early run (fc1babf, empty env wait) showed exit 2 and two warnings in 45 s; the dev committed aa63f53 into the same worktree while that run was reading `bin/squad-spawn`. I reran the same case on aa63f53 (empty env and unset): exit 0, one warning, 30.7 s. Treated as an edit-during-run artefact, not a defect.

Follow-ups (SQ-4, not blocking):
- Default wait budget is ~30 s in total (both waits), consistent with the AC "at most ~30 s".
- `SQUAD_SPAWN_START_WAIT` is an undocumented knob for tests; mention it in `squad-spawn --help` if it should be public.
