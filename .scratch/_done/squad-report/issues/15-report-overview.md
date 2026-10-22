Status: ready-for-agent
Type: task
Task ID: 15
Touches: `templates/report/report.css` (overview region: .kpis .digest .two .legend), `templates/report/report.js` (`overview()`), `bin/squadreport_digest.py` (reason cap), `tests/test_squadreport_ui.py` (extend), `tests/test_squadreport_digest.py`
Does not touch: `header()`/`nav()`, `banners()`, bin/squadreport.py
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_ui test_squadreport_digest test_squadreport_html`
Blocked by: 14 (same files; starts on 14's last whitebox-passed sha)

# 15: Overview body: no stray banners, KPI 3x2, Worth a look 4x2 with reason cap, side-by-side blocks

**Done when** the real report/rollup matches the mock for the screens and states below. Mock (visual oracle, copy only): `.claude/squads/plugin/scopes/report-ui-fix/ui-design/mock/`. Business AC: `.claude/squads/plugin/scopes/report-ui-fix/tasks/ba-ac.md` → T2 (AC2.1-2.11). Technical design and AC: `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` (row "2 Overview body" of "Tickets: files and tests", Technical AC 1-2, 11, 13-14, plus those named below).

150

## Rules
- Mock rules copied where the mock has them; Mango Parrot light only; no `innerHTML` (textContent); renderer stays one self-contained file.
- Compare your build with the mock at 1440x900 and 400x800 (serve on 127.0.0.1 per `project.md`), save screenshots in `dev-evidence.md` under `.claude/squads/plugin/scopes/report-ui-fix/evidence/15/`. Stop servers/browsers by PID.
- One commit per hand-in; name the final sha in the HANDIN. QA mode full.
