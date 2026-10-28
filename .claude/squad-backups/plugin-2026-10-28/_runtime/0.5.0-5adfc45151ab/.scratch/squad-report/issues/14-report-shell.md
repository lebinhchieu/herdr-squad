Status: ready-for-agent
Type: task
Task ID: 14
Touches: `templates/report/report.css` (shell region: body/main/header/nav), `templates/report/report.js` (`header()`, `nav()`, main wrapper, scroll-spy), `templates/report/template.html`, `bin/squadreport.py` (`scope.goal`, `scope.rollup_href`, D2), `bin/squadreport_build.py` only if href needs `out`, `tests/test_squadreport_ui.py` (NEW: harness + state helper), `tests/test_squadreport_collect.py`
Does not touch: overview/banners/other-tab code, rollup.*
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_ui test_squadreport_collect test_squadreport_html`
Blocked by: none (starts on main a4e37c5)

# 14: Shell: centred column, header right block, pill tabs

**Done when** the real report/rollup matches the mock for the screens and states below. Mock (visual oracle, copy only): `.claude/squads/plugin/scopes/report-ui-fix/ui-design/mock/`. Business AC: `.claude/squads/plugin/scopes/report-ui-fix/tasks/ba-ac.md` → T1 (AC1.1-1.6). Technical design and AC: `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` (row "1 Shell" of "Tickets: files and tests", Technical AC 1-2, 11, 13-14, plus those named below).

140

## Rules
- Mock rules copied where the mock has them; Mango Parrot light only; no `innerHTML` (textContent); renderer stays one self-contained file.
- Compare your build with the mock at 1440x900 and 400x800 (serve on 127.0.0.1 per `project.md`), save screenshots in `dev-evidence.md` under `.claude/squads/plugin/scopes/report-ui-fix/evidence/14/`. Stop servers/browsers by PID.
- One commit per hand-in; name the final sha in the HANDIN. QA mode full.

## Fixture (Tech Lead DECISION 16)
- Implement fixture F-e from `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` → "Fixtures" (goal + rollup link case); share the generator `tests/report_ui_fixtures.py` (add to Touches; ticket 16 extends it).

## AC update (Tech Lead)
- Technical AC now 17 items in tech-design.md; this ticket adds AC15 (goal validation, relaxed href test).
