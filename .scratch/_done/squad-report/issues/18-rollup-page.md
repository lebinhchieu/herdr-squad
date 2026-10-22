Status: ready-for-agent
Type: task
Task ID: 18
Touches: `templates/report/rollup.css`, `templates/report/rollup.js`, `templates/report/rollup.html`, `bin/squadreport_rollup.py` only if data missing, `tests/test_squadreport_rollup.py`, `tests/test_squadreport_rollup_ui.py` (NEW; own harness copy so no clash with ticket 14's file)
Does not touch: report.css, report.js, template.html, bin/squadreport.py
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_rollup test_squadreport_rollup_ui`
Blocked by: none (own files; may run in parallel with 14)

# 18: Rollup page vs rollup.html

**Done when** the real report/rollup matches the mock for the screens and states below. Mock (visual oracle, copy only): `.claude/squads/plugin/scopes/report-ui-fix/ui-design/mock/`. Business AC: `.claude/squads/plugin/scopes/report-ui-fix/tasks/ba-ac.md` → T5 (AC5.1-5.8). Technical design and AC: `.claude/squads/plugin/scopes/report-ui-fix/tech-design.md` (row "5 Rollup" of "Tickets: files and tests", Technical AC 1-2, 11, 13-14, plus those named below).

180

## Rules
- Mock rules copied where the mock has them; Mango Parrot light only; no `innerHTML` (textContent); renderer stays one self-contained file.
- Compare your build with the mock at 1440x900 and 400x800 (serve on 127.0.0.1 per `project.md`), save screenshots in `dev-evidence.md` under `.claude/squads/plugin/scopes/report-ui-fix/evidence/18/`. Stop servers/browsers by PID.
- One commit per hand-in; name the final sha in the HANDIN. QA mode full.
