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

## Review

AC trace
- AC5 (no `done`) | tests/test_squadboard_panels.py T12 AC7 (`Passed (2)`, no `Ready for review` or `Done` button) | `python3 -m unittest tests.test_squadboard_panels.Panels12.test_T12_AC7_AC8_AC9_tasks_stages_ready_flag_detail_in_time_order_toggle_and_esc`
- s3 (`passed` replaces `ready for review`) | same test (`ready` flag on 2 passed rows); tests/test_squadboard_inbox.py `passed=` hook, `unknown` has no `passed` | `python3 tests/test_squadboard_inbox.py`
- Dashboard spec AC4 | .scratch/dashboard/spec.md s3, s7, AC4 reworded | `grep -n "eady for review" .scratch/dashboard/spec.md` (no hit)

Targeted runs on 1692ec1: inbox 12 ok, board_fixtures 4 ok, tasks 24 ok, panels 58 with 2 clock fails (T12 AC1, T14), demo 13 with 1 clock fail (T37). All 3 fail on base too.
