# 10 squad-usage finds an agent's earlier sessions

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/02-designer-row-blank.md`, Token Coach proposal 2; absorbs followups 08)
Blocked by: none
Aim: Usage table shows an agent after a lazy respawn
Estimate: 1.5h
Depends on: none

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/10.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Build 10 first, then 11 in the same worktree (same file).
Files: `bin/squad-usage`, `bin/squadtranscript.py`, `tests/test_squad_usage.py`, `tests/test_squadtranscript.py`; optional `bin/squad-respawn` and `tests/test_squad_respawn.py` (only if adding `session` to its record is cheap)

## Problem
After a lazy respawn the roster holds a session with no transcript, so `squad-usage` prints `<agent>: no transcript` and the footer "roster session not found", although the agent's earlier session exists on disk (designer `plugin-ux-po-clarity`, spawn session 21895534). Also `peak ctx` shows the last session's peak only, so a 331k session followed by a 61k one reads 61k.

## Change
- `agent_paths(name, sid)`: when the roster session has no transcript, take the `spawn` event sessions of `name` from `<squad dir>/usage-events.jsonl` (newest first); the first with a transcript anchors `agent_sessions` (same project dir). The footer note appears only when no anchor is found. Respawn events carry no session id, so only `spawn` events are used.
- The table gets `max peak` (largest session peak) beside `peak ctx`. `--help` says what `1st act`, `peak ctx` and `max peak` count.
- Optional: `squad-respawn` adds the new `session` to its record so a later respawn is covered too.
- No parser reads the table (`grep -rl 'peak ctx'` hits only `bin/squad-usage` and its test), so columns may be added.

## AC
- AC1: fixture roster with an unfound session and a `spawn` event whose session has a transcript: `--sessions NAME` lists that session and the table row is not "no transcript" (base: "no transcript").
- AC2: fixture agent with session peaks 331k then 61k: `peak ctx` 61k and `max peak` 331k.
- AC3: `python3 bin/squad-usage --help | grep -c 'max peak'` is at least 1 and `grep -c '1st act'` is at least 1 (base: 0 and 0; `peak ctx` 1).
- AC4 (real data, not a test): `SCOPE_DIR=<po-clarity scope> python3 bin/squad-usage --sessions plugin-ux-po-clarity` prints at least one session row.
- AC5: the followups 08 `wontfix` edit is made by 12's first commit, not here.

## Comments
