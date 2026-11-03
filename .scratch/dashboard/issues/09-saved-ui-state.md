# 09 saved ui state
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 03
Feature: 14 (`tasks/features.md`)

## What the PO gets
The layout, the last choice and the font size come back when the board reopens.

## Rules
- The server saves `<squad folder>/board-ui.json` (the only file the board writes; version field, atomic write; a token from page load is needed). The browser keeps a copy. Saved per squad: panel position, size, hidden; last choice and the 5 recent; font size. Each save has `saved_at`; the newer of file and copy wins.
- "Comes back" = same grid positions, same hidden panels, same choice, same font size.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T09.AC1** Given layout, choice and font size set, when the board opens on another port or browser, then positions, hidden panels, choice and font size all come back.
- **T09.AC2** Given `board-ui.json` is unwritable, then the page works from the browser copy with "settings not shared".
- **T09.AC3** Given the file is unwritable and browser storage is blocked, then defaults with "layout not saved".
- **T09.AC4** Given the file is unreadable or has an unknown version, then defaults with "settings file unreadable" and the picker shows.
- **T09.AC5** Given a write without the page's token, or from a wrong Host, then it is refused and the file is unchanged.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module of `architecture.md` section 1 (`board-ui.json`, `PUT /api/ui`).
- New: `bin/squadboard_ui.py` (read and atomic write of `board-ui.json`, version field, token check helper).
- Edit: `bin/squadboard.py` (route rows `GET` state field and `PUT /api/ui`) only; ticket 03 is done first.
- Tests (new): `tests/test_squadboard_ui.py` (unwritable file, two writers, bad JSON, version).

## Comments
