# 01: squad-spawn: the first prompt starts the agent

Status: ready-for-agent
Duties: design notes = Developer (this file, ## Design notes); technical AC = QA whitebox with the Developer; business AC = this ticket; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; suite and promote.md = QA whitebox; no full suite without Chieu's yes
Files: bin/squad-spawn, tests/test_squad_spawn.py, tests/squadtest.py
Test harness: tests/test_squad_spawn.py (stub herdr)
Ticket path (commit by the first Developer task, FILE-11): `.scratch/watchdog-blind/issues/01-*.md`; evidence next to it.

Seen: the first prompt sits typed in the input box, never submitted; herdr says `idle`; a later SendMessage starts the agent (guardian dev-16 2026-11-17, dev-cvscope-27 2026-11-23, Claude Code 2.1.330). Cause: `bin/squad-spawn` line 576 runs `herdr agent prompt` once and never checks the agent went `working`.

## AC
1. After `herdr agent prompt`, `squad-spawn` waits (bounded, at most ~30 s, poll `herdr agent get`/list) until the agent's status is `working`.
2. If it stays `idle`/`done`, it resends Enter once (the herdr way to submit the typed input; see `herdr --help`; `bin/squadhomes.py:220` shows `--wait`), then waits again.
3. Still not `working`: one stderr line `warning: <name> did not start on its first prompt; send it a message` and exit status and stdout JSON unchanged (spawn still succeeds).
4. No prompt (`--prompt` empty) or `--dry-run`: no wait, no change.
5. Tests in `tests/test_squad_spawn.py` with stub herdr: (a) goes working at once: no resend; (b) goes working after resend; (c) never: warning printed. Existing tests stay green.

## Rules for this ticket
- Proof runs only in a scratch squad (temp dir, stub `claude` and herdr, as `tests/test_squad_start.py` / the named test file). Never run `squad-watchdog tick|run|ensure` or `squad-spawn` against `/home/chieule/workspace/wpw` (live guardian agents get messages).
- [SQ-10] Any `bin/` edit: also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`; quote the result in `## Behaviour`.
- CLAUDE.md: run `grep -rl` over `tests/` for each touched path or changed printed string and run every hit.
- [SQ-2] `## Review` starts with an AC trace; quote `squad-evidence checks` exit code in HANDIN.

## Technical AC (QA whitebox, agree with the Developer here; written before work, 2026-11-23)
T1. Status is read like the existing readiness loop (bin/squad-spawn ~line 540): `herdr agent get "$name" | jq -r '.result.agent.agent_status // .agent_status // empty'`. REV-4: before trusting it, the Developer pastes in `## Design notes` one real `herdr agent get` sample of an idle/done agent and one of a working agent (read-only, any live agent but never a wpw one is not required: `herdr agent list` output of this machine is fine). Resend uses `herdr agent send-keys "$name" Enter` (verified in `herdr agent send-keys --help`).
T2. Bounded and fast under test: total wait and poll interval are env-tunable (e.g. `SQUAD_SPAWN_START_WAIT`, default ~30 s) and the tests set them to well under 1 s. No test sleeps 30 s. `herdr agent get` failing (non-zero, junk, no field) counts as "not working": no crash, no hang, loop still ends at the bound.
T3. Enter is sent at most once per spawn; the wait runs after the `agent prompt` line and before the final JSON; stdout stays exactly the one JSON line (the warning goes to stderr only); exit status unchanged. `set -e` safety: a failing `herdr agent get`/`send-keys` inside the new code never aborts the spawn (`|| true`).
T4. No prompt or `--dry-run`: zero extra herdr calls (test asserts the herdr log has no `agent get` / `send-keys` beyond the existing ones).
T5. Shared stub: `tests/squadtest.py` `_FAKE_HERDR` `agent get` prints no `agent_status` today, so every existing test that spawns with a prompt would wait the full bound and warn. Fix inside the ticket: the stub reports a status (default `working`, overridable by env such as `AGENT_STATUS_SEQ`), and `tests/squadtest.py` is added to `Files:`. Evidence: `grep -rl 'squad-spawn\|fake_herdr' tests/` hits all run, each timed, no new slowness, no stderr warning in them.
T6. Tests (a)(b)(c) assert on the herdr log (send-keys count 0 / 1 / 1) and on stderr text, not on timing. (c) also asserts exit 0 and the JSON line unchanged.
T7. `squad-respawn` calls `squad-spawn` with a prompt: confirm by reading the code that a respawn still works and show one targeted test hit (grep -rl squad-respawn tests/).
T8. SQ-10 three files and the `grep -rl` hits run and quoted; no new skips.

## Design notes (Developer)
Real `herdr agent get <name>` (read-only, fields cut to the ones used; herdr on this machine 2026-11-23):
- idle: `{"result":{"agent":{"name":"guardian-mgr-consolidated","agent_status":"idle","agent":"claude","pane_id":"w4T:p77"}}}`
  same agent from `herdr agent list | jq -c '.result.agents[]|select(.name=="guardian-mgr-consolidated")|{name,agent_status}'` -> `{"name":"guardian-mgr-consolidated","agent_status":"idle"}`
- working: `{"result":{"agent":{"name":"plugin-qab-watchdog-blind","agent_status":"working","agent":"claude","pane_id":"w6M:p6"}}}`
- The field is `.result.agent.agent_status`; statuses seen: idle, working, done (also blocked, unknown).
Choices: poll `agent get` every 0.5 s, SQUAD_SPAWN_START_WAIT s per phase (default 15, about 30 s in all). `working`: started. `idle`/`done`: keep waiting, then one `agent send-keys <name> Enter`, wait again, then the warning. `blocked` (a trust/permission dialog), `unknown`, or an unreadable status (get fails, no field): no resend, no warning, the spawn goes on; Enter must never answer a dialog.
