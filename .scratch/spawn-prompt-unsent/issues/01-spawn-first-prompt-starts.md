# 01: squad-spawn: the first prompt starts the agent, and stdout says so

Status: ready-for-agent
Duties: design notes = Developer (## Design notes); technical AC = Developer; business AC = this ticket; code check = Developer's `## Review`, confirmed by the Manager; behaviour check = Manager confirming `## Behaviour`; hand in to the Team Lead; passed = `squad-evidence check` exits 0 (no QA); suite and promote.md = Developer; no full suite without Chieu's yes
Aim: Spawn waits for a ready input, retries Enter, says started
Estimate: 1h 30m
Depends on: none
Files: bin/squad-spawn, tests/test_squad_spawn.py, tests/squadtest.py
Test harness: tests/test_squad_spawn.py (stub herdr in tests/squadtest.py: AGENT_STATUS, AGENT_STATUS_AFTER_KEYS)
Ticket path (commit by this task, FILE-11): `.scratch/spawn-prompt-unsent/issues/01-spawn-first-prompt-starts.md`; also commit `tasks/02.md` as `issues/02-watchdog-wakes-spawner.md`.

## Problem
```diagram today (bin/squad-spawn ~line 611)
pane agent == claude            [ok]
▼
herdr agent prompt (typed)      [ok]
▼
wait 15 s for working, 1 Enter
▼
wait 15 s, warning on stderr    [fail]
```
guardian-dev-cvlock-11c (2026-11-25) sat `idle` with the whole prompt typed; a later Enter started it. Earlier: 2026-11-17, 2026-11-23. The current design comes from `.scratch/_done/watchdog-blind/issues/01-squad-spawn-first-prompt.md` (one Enter, ~30 s, stderr only); spawners pipe output through `tail`/`grep` and miss the stderr line.

## Change
1. Root cause first (Developer verifies, design notes): squad-spawn sends the prompt once the pane shows `agent == claude`, not once Claude Code takes input. `herdr agent get <name>` has `.result.agent.interactive_ready` (true on a ready session, null on another; seen 2026-11-25). If it is a reliable signal, wait for it (bounded) before `herdr agent prompt`. If not, say why in the design notes and keep only step 2.
2. Enter retry with backoff: still `idle`/`done` after the prompt -> Enter, then later Enters, until `working`; total bounded so a spawn ends in at most ~100 s (the spawner's Bash call times out at 120 s). Same rule as today: `blocked`, unknown or unreadable status gets no Enter and no warning.
3. stdout JSON line gets `"started": true|false|null` (null = no prompt, or status unreadable/blocked). Keys and `status` unchanged; stderr warning kept.
4. `started: false` also writes the marker `roles/<name>.unsent` (in the agent's home, holding the spawner's name `$SQUAD_NAME` or empty), removed by a later spawn of that name. Ticket 02 reads it.

## AC
1. A stub agent that becomes `interactive_ready` late gets its prompt only after it (or design notes show why the signal is not used).
2. Idle after the prompt: Enter retried at most 3 times, with growing gaps; working after the 2nd Enter -> exactly 2 `send-keys` in the herdr log, no warning, `"started": true`.
3. Never working: 3 `send-keys`, stderr warning once, exit 0, JSON `"started": false`, marker file written with the spawner name.
4. `blocked` status or no `--prompt` or `--dry-run`: no Enter, no marker, `"started"` null (or no wait for no prompt).
5. All waits env-tunable (`SQUAD_SPAWN_START_WAIT` and any new one); no test sleeps more than ~2 s; the default worst case is printed in design notes and is under 100 s.
6. Existing tests stay green; `grep -rl 'squad-spawn\|status.*ready' tests/` hits run, plus `tests/test_squad_respawn.py`.

## Rules for this ticket
- Verify: run the `/mattpocock-skills:code-review` skill on your diff against the task base (Chieu's ask; no QA on this team). `## Review` starts with an AC trace, then that review's findings and what you did with each. `## Behaviour` holds the test output per AC.
- Proof only in a scratch squad with stub herdr; never run `squad-spawn` or the watchdog against `/home/chieule/workspace/wpw`.
- [SQ-10] `bin/` edit: also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`; quote in `## Behaviour`.
- CLAUDE.md: `grep -rl` over `tests/` for each changed printed string and run every hit.

## Team Lead notes
- Base 4049f8e dry-run (SQ-15): tests/test_squad_spawn.py 122 OK; tests/test_squad_watchdog.py 114 OK (run `cd tests && python3 -m unittest test_squad_watchdog`; the file has no runner). No base failures.
- Read this ticket and its `Files:` (at most 4 more) before the first Edit or Write (SQ-27). No Edit, Write or STATUS by turn 15: send `STATUS NN: still reading <what>, <n> more turns` to the Team Lead.
- Developer retires only after the Team Lead's `squad-evidence check` exit 0 (SQ-20).

## Design notes (Developer)

- Root cause: the pane shows `agent == claude` before Claude Code takes input, and squad-spawn typed the prompt then. `herdr agent get` `.result.agent.interactive_ready` is `true` once input is taken (seen in the real fixtures `tests/fixtures/ca/agent-list*.json`, true on named idle, working and blocked agents). Used as a bounded gate: wait while the key is present and not true (not while `blocked`); an absent key (older herdr) or unreadable get: no wait. Signal not trusted alone, so step 2 stays.
- Waits (all counts of `SQUAD_SPAWN_POLL`-second polls, default 0.5 s): ready wait `SQUAD_SPAWN_READY_WAIT` default 20 s; after the prompt gaps B, 1.5B, 2B, 2.5B with an Enter after each of the first three, B = `SQUAD_SPAWN_START_WAIT` default 8. Default worst case: 20 + 56 = 76 s, under 100 s. `SQUAD_SPAWN_START_WAIT` changed meaning: it was 15 s per wait (30 s total), it is now the base gap; a changed `SQUAD_SPAWN_POLL` scales every wait (tests only).
- `started`: true on `working`; false after the last wait with idle/done (warning once, marker `roles/<name>.unsent` holding `$SQUAD_NAME`, possibly empty); null for no prompt or blocked/unreadable status. `--dry-run` exits before all of this. Any spawn removes the old marker.

## Comments
