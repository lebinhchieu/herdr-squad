# 13 page new since last looked
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 1
Blocked by: 07, 11, 12
Feature: 16 (`tasks/features.md`)

## What the PO gets
A dot and a count for what happened while the PO was away.

## Rules
- "Away" = the page tab is hidden or closed. The browser stores the time the page was last visible, per choice. On return, a task row or picker row shows a dot and "N new" (counts from ticket 07). Opening a task's detail clears its dot. No text list. First visit: nothing new.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T13.AC1** Given the PO opens a choice, closes the tab, 2 PASS and 1 FAIL are added to task 03 in the message log, and he reopens, then 03 shows "3 new" and its scope's picker row shows "3 new".
- **T13.AC2** Given the first visit of a choice, then nothing is new.
- **T13.AC3** Given the PO opens task 03's detail, then its dot clears and the picker row count drops by 3.
- **T13.AC4** Given a new event on 03 after clearing, then the dot and "1 new" show again.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M13 part.
- New: none.
- Edit: `templates/board/board.js` (away detection, dot and count), `panel_tasks.js`, `panel_inbox.js`, `panel_scopes.js` (the dot only).
- Tests: extend `tests/test_squadboard_panels.py`.
- Design: `ui-design/design-v5.md`.

## Comments
