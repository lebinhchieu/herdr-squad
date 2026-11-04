## Behaviour

- Merged `squad/board/dashboard/board-dev-new-18` (ticket 13, passed 4e32975) into the integration branch with `--no-ff`.
- 3 trivial conflicts, both sides kept: `templates/board/board.js` (column rules + seen/new helpers), `tests/test_squadboard_panels.py` (ticket 14/20 and ticket 13 tests), `templates/board/panel_tasks.js` (the new-badge now goes into `cell.task`).
- Targeted tests: panels, page, inbox, timeline, files = 115 OK; README hits (squad_close, path_guard, promotion_0_6_0) = 103 OK.
- Full suite not run here (QA whitebox).
