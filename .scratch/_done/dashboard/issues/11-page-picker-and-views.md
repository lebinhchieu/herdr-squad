# 11 page picker and views
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 1
Blocked by: 04, 09, 10
Feature: 11, 4 (`tasks/features.md`)

## What the PO gets
The picker page and the goal and scope views.

## Rules
- Landing = picker: Recent (last 5; a 6th pushes out the oldest; the same choice twice shows once), Open (needs-you first), Done (N) collapsed, search. Goal rows expand to their scopes; a goal opens expanded if a scope needs the PO.
- Search: case-insensitive substring on name or brief, Done included. `/` focuses the box when no text field has focus. Enter opens the top visible row. No match: `Nothing matches '<text>'`.
- Opening order: flag, URL (`#/goal/G`, `#/scope/S`), saved choice, picker. Back button from a choice returns to the picker. `#/scope/nope` opens the picker with "not found".
- Header shows `goal G` or `goal G > scope S`, a switcher sheet (Esc closes), "N more need you in <name>" links.
- Goal view: brief, Scopes strip (per scope: brief, stage, needs you, blocked, tasks "x of y", last active), panels with a Scope column. Scope view: the goal named or "no goal", a link up.
- No control or link named "All"; no sum of data across choices except the squad-wide needs-you count.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T11.AC1** Given the fixture, no flag and no saved choice, then only the picker shows: Open rows (needs-you first), "Done (20)" collapsed, no task, inbox or work-time panel.
- **T11.AC2** Given the picker, then no control or link is named "All" and no number sums data across choices except the squad-wide needs-you count.
- **T11.AC3** Given the PO types "INBOX" in search, then rows whose name or brief contain it (any case) show, done ones too; Enter opens the top row.
- **T11.AC4** Given a search with no match, then the text "Nothing matches 'xyz'".
- **T11.AC5** Given no text field has focus, when the PO presses `/`, then the search box is focused.
- **T11.AC6** Given 6 different choices made in turn, then Recent shows the last 5; given the same choice twice, then it shows once.
- **T11.AC7** Given S1 was chosen yesterday and is open, then S1 opens with no flag.
- **T11.AC8** Given that S1 was closed since, then it opens read-only marked "closed".
- **T11.AC9** Given its folder is gone, then the picker shows "saved choice S1 not found".
- **T11.AC10** Given `--goal G` and a saved scope choice, then G shows.
- **T11.AC11** Given `#/scope/S1`, then S1 opens; reload keeps it; Back returns to the picker. Given `#/scope/nope`, then the picker with "not found".
- **T11.AC12** Given S3 has an open question and the choice is S1, then the header says "1 more needs you in S3", the tab count includes it, and clicking "S3" shows S3.
- **T11.AC13** Given a goal is open, then every panel shows only its scopes' rows; the Scopes strip shows brief, stage, needs you, blocked, tasks "x of y", last active per scope.
- **T11.AC14** Given the PO clicks a scope in the strip, then that scope shows, the header reads "goal G > scope S" and a link goes back up to G.
- **T11.AC15** Given a chosen scope closes while the page is open, then the page turns read-only with "closed" and a link to the picker, and does not fail.
- **T11.AC16** Given the fixture (25 scopes), then picker rows show within 3 s of load.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M13 part: picker and views.
- New: `templates/board/panel_scopes.js`.
- Edit: `templates/board/board.js` only to register the view (one line); no other edit. If it needs more, `BLOCKED 11` first.
- Tests: extend `tests/test_squadboard_panels.py` (created by this ticket).
- Design: `ui-design/design-v5.md`.

## Comments
