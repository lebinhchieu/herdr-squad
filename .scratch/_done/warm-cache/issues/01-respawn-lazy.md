# 01: squad-respawn --lazy and squad-spawn without the first-prompt wait

Status: ready-for-agent
Duties: design notes = Tech Lead (tasks/design.md, the lazy contract C1-C5, binding); technical AC = Tech Lead (this file); business AC = ticket (spec stories); code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; suite and promote.md = Tech Lead; NO full suite (DECISION 0, Chieu): run the test files you touched, the `grep -rl` hits over tests/ for each touched path or changed string, and the SQ-10 three files tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py; quote the results in `## Behaviour`
Files: bin/squad-respawn, bin/squad-spawn, tests/test_squad_respawn.py, tests/test_squad_spawn.py
Ticket path (FILE-11): `.scratch/warm-cache/issues/01-respawn-lazy.md`; evidence next to it. Test harness: `squadtest.fake_herdr`, scratch squad (see `tests/test_squad_respawn.py`, `tests/test_squad_spawn.py` setUp). Depends on: nothing (contract C1-C3 in `tasks/design.md`). Spec stories 13, 27-29, 32; seam 2.

## Problem
A respawned session is sent the notes prompt at once, so a respawn nobody needs again still pays a cold cache write. The watchdog (ticket 03) needs a respawn that starts the session and sends nothing, and the hook (ticket 02) needs a marker to know the first message is the first one.

## AC
1. `squad-respawn <name> --lazy` starts the new session through `squad-spawn <role> <name> ... --lazy` with no `--prompt`; no `herdr agent prompt` call is made for the new agent. Everything else of a respawn is as today: name, role, scope or goal, worktree, `--title`, the model/effort of `roles/<name>.overrides`, roster row and session id, the `prev-$$` rename and the old pane closed last, the Team Lead refusal, the missing-notes refusal (and `--force`), `--dry-run` (prints the `--lazy` spawn line, writes nothing).
2. `squad-spawn --lazy`: records the roster session id as today, writes `<home>/roles/<name>.lazy` holding one line, the session id (contract C1). `--lazy` with `--prompt` or `--task`: exit 2, nothing started. With `--lazy` no "spawned without --prompt" warning and no first-prompt wait, no `send-keys Enter`, no "did not start on its first prompt" warning (test: fake herdr that stays `idle`, `SQUAD_SPAWN_START_WAIT` large, the spawn returns at once).
3. A spawn without `--lazy` removes `<home>/roles/<name>.lazy` (`rm -f`, beside the `.overrides` handling). A test: stale marker, plain spawn, marker gone.
4. The default `squad-respawn <name>` (no flag) still sends the `RESPAWN:` prompt, writes no marker, and its event record has no `lazy` key. Usage text of both scripts lists `--lazy`.
5. Event log (C3): the `respawn` record of a lazy respawn has `"lazy": true`; a plain one does not. `rule` is `respawn` in both. `grep -rn "usage-events" bin/` readers listed in `## Behaviour`, each one confirmed to ignore an unknown key (quote the line).
6. The marker is written after `squad-spawn` knows the session id and before anything can send a prompt; `--dry-run` of `squad-spawn --lazy` says "would write <path>" and writes nothing.
7. Technical: stays bash, uses only what the scripts already use (jq, no new dependency); Windows-safe like its neighbours (`tests/test_windows_safe.py`, `tests/test_utf8_helpers.py` green and quoted); the marker content has no CRLF.
8. SAFETY: other squads' agents are live (guardian-* in wpw). Check only with a fake herdr on PATH or a scratch squad in a mktemp -d dir. Never run the real herdr, squad-watchdog tick/run/ensure, squad-respawn or squad-spawn against this repo's squads or any live name.

## Not in this ticket
The hook (02), the watchdog (03), rule text and version (04). Do not touch `bin/squad-usage-hook`.

Rules for this ticket: CLAUDE.md surgical changes, no slop; test economy (one test per AC risk, no matrices, extend existing test files, existing tests keep passing, none newly skipped); ADR 0011 (no new shell-only dependency: the same helpers as the other tools).
