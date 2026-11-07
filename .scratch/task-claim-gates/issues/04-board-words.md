# 04 Board words: done to passed, fixtures and panel text

Status: ready-for-agent
Blocked by: 03

Rename in templates/board/panel_tasks.js, squadboard_inbox.py, demo and fixtures; `done` gone from the board. `ready for review` rename only if Chieu answers ASK 1 yes; otherwise untouched. Runs after 03 because tests overlap.

Files: templates/board/panel_tasks.js, bin/squadboard_inbox.py, tests/test_squadboard_panels.py, test_squadboard_demo.py, test_board_fixtures.py
AC: states.md AC5 (no `done`), s3.
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.
