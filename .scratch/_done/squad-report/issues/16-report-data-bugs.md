Status: ready-for-agent
Type: task
Task ID: 16
Touches: `bin/squadreport.py` (`collect` dedupe of duplicate roster names only), `templates/report/report.js` (`banners()`), `templates/report/report.css` (banners region: .banner), `tests/test_squadreport_collect.py`, `tests/test_squadreport_ui.py` (extend)
Does not touch: `header()`, `overview()`, digest
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_collect test_squadreport_ui test_squadreport_html`
Blocked by: 15 (same files; starts on 15's last whitebox-passed sha)

# 16: Data bugs and banners: retired agent, returns count

**Done when** the real report/rollup matches the mock for the screens and states below. Mock (visual oracle, copy only): `.claude/squads/plugin/scopes/report-ui-fix/ui-design/mock/`. Business AC: `.claude/squads/plugin/scopes/report-ui-fix/tasks/ba-ac.md` → T3 (AC3.1-3.5) and AC4.9 banner order/kinds. Technical design and AC: `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` (row "3 Data bugs + banners" of "Tickets: files and tests", Technical AC 1-2, 11, 13-14, plus those named below).

160

## Rules
- Mock rules copied where the mock has them; Mango Parrot light only; no `innerHTML` (textContent); renderer stays one self-contained file.
- Compare your build with the mock at 1440x900 and 400x800 (serve on 127.0.0.1 per `project.md`), save screenshots in `dev-evidence.md` under `.claude/squads/plugin/scopes/report-ui-fix/evidence/16/`. Stop servers/browsers by PID.
- One commit per hand-in; name the final sha in the HANDIN. QA mode full.

## Fixtures and copy (Tech Lead DECISION 16)
- Implement fixtures F-a, F-a2, F-b, F-c, F-d from `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` → "Fixtures" (data and expected numbers there). Generator `tests/report_ui_fixtures.py` (add to Touches); output committed to `.claude/squads/plugin/scopes/report-ui-fix/evidence/16/fixtures/` for QA blackbox.
- Flag banner copy per AC3.4/3.5: `1 task reached 3 returns` (supersedes the banner text in the What section above).

## FINAL copy and AC update (Tech Lead, supersedes banner text above and in Fixtures section)
- Flag banner: `N task(s) reached 3 or more returns (Task 04: 3) of T in all. Rework so far <time>, about $<cost>.` Expected values in tech-design.md → Fixtures (F-c).
- Technical AC now 17 items in tech-design.md; this ticket adds AC5 (order-independence) and AC16 (real-data shape).
