# 14 files
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 2
Blocked by: 12
Feature: 8 (`tasks/features.md`)

## What the PO gets
Everything the squad made for the PO, in one list.

## Rules
- Scope: `tasks/*.md`, `ui-design/`, `promote.md`, `report/report.html` and `data.json` (after squad-report or close), `evidence/`, ticket `evidence.md`; goal: `shared/`, `shared/decisions.md`; answered questions with the PO's answer. Columns: name, kind, last changed (local zone). ADRs are not listed.
- A click opens the file in a new tab: markdown shown readable, HTML as a page. Only files under the squad folder and `.scratch`; agent-written HTML cannot reach the board's data.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T14.AC1** Given a scope with a feature list, 3 prototypes and promote.md, then each lists with name, kind, last changed in the local zone.
- **T14.AC2** Given a click on a markdown file, then a new tab shows it readable (no raw `#` marks); given an HTML file, then it opens as a page.
- **T14.AC3** Given a path outside the squad folder and `.scratch` (also with `..`), then a message and no content.
- **T14.AC4** Given a live scope without a report, then "no report yet (made at close)".
- **T14.AC5** Given a closed scope with a report, then `report.html` and `data.json` are listed.
- **T14.AC6** Given an opened agent HTML page that tries to call the board's data, then the call fails (sandboxed).

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M8 + file panel (iteration 2).
- New: `bin/squadboard_files.py`, `templates/board/panel_files.js`.
- Edit: `templates/board/board.js` (register). The `/api/file` allow-list lives in ticket 03; reuse it, do not edit `squadboard.py`.
- Tests (new): `tests/test_squadboard_files.py`; extend `tests/test_squadboard_panels.py`.
- Design: `ui-design/design-v5.md`.

## Comments
