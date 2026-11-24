# 11 squad-usage shows the start size and first-act turn

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/03-developer-first-act.md`, Token Coach proposal 3)
Blocked by: 10
Aim: Usage shows how many turns pass before the first edit
Estimate: 1h
Depends on: 10

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/11.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Same worktree as 10, after 10.
Files: `bin/squad-usage`, `bin/squadtranscript.py`, `tests/test_squad_usage.py`, `tests/test_squadtranscript.py`

## Problem
8 of 11 Developers in the last scope started over 55k context before their first action, and nothing shows how many turns they read first. The draft proposed writing the first Stop-hook size into the spawn event, but the spawn event is written at launch, before any transcript exists.

## Change
Derive it from the transcript, no hook or event change. `start` = context of the session's first main-thread turn. `act turn` = 1-based index of the first main-thread turn that holds an action (same `is_action` as `1st act`), `-` when none. Sidechain turns do not count. `--sessions NAME` gets columns `start`, `1st act`, `act turn`; the table gets `act turn` after `1st act`.

## AC
- AC1: fixture with 3 main-thread read turns then an Edit in turn 3: `act turn` 3 and `start` = context of turn 1.
- AC2: a leading sidechain turn does not shift `act turn`.
- AC3: no action in the session: `act turn` is `-`.
- AC4: a message with several usage lines keeps the maximum.
- AC5 (real data): `squad-usage --sessions <a Developer of this scope>` prints `start`, `1st act` and `act turn` for a session with an edit.

## Comments
