Status: ready-for-agent
Type: task
Task ID: 17
Touches: `templates/report/report.css` (tables/grid/timeline/drawer regions), `templates/report/report.js` (tasks, roles, grid, timeline, drawer, states), `tests/test_squadreport_ui.py` (extend)
Does not touch: `header()`, `nav()`, `overview()`, `banners()`, bin/*
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_ui test_squadreport_html`
Blocked by: 16 (same files; starts on 16's last whitebox-passed sha)

# 17: Tasks, Roles, Task x role, Timeline, drawer, states, 400px

**Done when** the real report/rollup matches the mock for the screens and states below. Mock (visual oracle, copy only): `.claude/squads/plugin/scopes/report-ui-fix/ui-design/mock/`. Business AC: `.claude/squads/plugin/scopes/report-ui-fix/tasks/ba-ac.md` → T4 (AC4.1-4.12). Technical design and AC: `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` (row "4 Other tabs" of "Tickets: files and tests", Technical AC 1-2, 11, 13-14, plus those named below).

170

## Rules
- Mock rules copied where the mock has them; Mango Parrot light only; no `innerHTML` (textContent); renderer stays one self-contained file.
- Compare your build with the mock at 1440x900 and 400x800 (serve on 127.0.0.1 per `project.md`), save screenshots in `dev-evidence.md` under `.claude/squads/plugin/scopes/report-ui-fix/evidence/17/`. Stop servers/browsers by PID.
- One commit per hand-in; name the final sha in the HANDIN. QA mode full.
