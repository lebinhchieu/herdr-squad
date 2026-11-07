# 04 Board words: done to passed, fixtures and panel text

Status: ready-for-agent
Blocked by: 03 (same test files, runs after it)

Rename in templates/board/panel_tasks.js, squadboard_inbox.py, demo and fixtures; `done` gone from the board. `ready for review` is dropped (E3): panel flag `isReady` now flags `passed`; Inbox count text, `ready_for_review` (hook and `unknown` name, now `passed`), dashboard spec s3, s7 and AC4 follow (states.md s3). Runs after 03 because tests overlap.

Files: templates/board/panel_tasks.js, templates/board/panel_inbox.js, bin/squadboard_inbox.py, .scratch/dashboard/spec.md, tests/test_squadboard_panels.py, test_squadboard_inbox.py, test_squadboard_demo.py, test_board_fixtures.py, tests/board_fixtures.py (comment)
AC: states.md AC5 (no `done`), s3, AC4 of the dashboard spec.
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.

## Built
- `isReady` flags `passed`; `DONE` is `merged` only. Filter buttons: `Passed (n)` and `Merged (n)` (was `Ready for review`, `Done`).
- Inbox text: "passed branches: see Tasks". `squadboard_inbox` hook key and `unknown` name `ready_for_review` -> `passed`.
- Dashboard spec s3, s7, AC4 reworded. `squadboard_tasks.ready_by_scope` keeps its name (03's file, not in this ticket's Files).
