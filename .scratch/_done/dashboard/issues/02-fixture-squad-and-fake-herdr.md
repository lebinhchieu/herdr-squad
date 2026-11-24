# 02 fixture squad and fake herdr
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: -
Feature: F0 (QA blackbox) (`tasks/features.md`)

## What the PO gets
A committed test squad, so every business AC can be checked in a browser without a real squad. (For QA and Developers; the PO sees nothing.)

## Rules
- A fixture squad folder committed in the repo (the path is set by the ticket's Developer), built to the givens of the AC: 3 goals (one with 4 scopes), 6 lone scopes, 20 done scopes, a long name, a closed scope, a scope with an open question, a scope with a parked question, a broken `open-questions.md`, tasks in every stage (todo and unassigned, in progress, returned with 3 FAIL, blocked, 1 of 2 PASS, ready for review, sha changed after PASS, merged), a ticket id token with no ticket (`REV-8`), a transcript set (including a night gap and a gap across a DST change), one missing transcript, one missing source, a second squad path to stand for another repo.
- A recorded herdr status file in the fixture (agents blocked, working, retired; and a "herdr not running" case). Behaviour the board must have: it can read this file instead of calling `herdr` (the flag or variable name is the Architect's).
- A written list of fixture steps for the AC that need a broken environment: make `board-ui.json` unwritable, block browser storage, stop and restart the server, add events to the message log, answer a question by CLI.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T02.AC1** Given a fresh checkout, when QA starts the board on the fixture, then the picker shows 3 goals, 6 lone scopes (Open) and "Done (20)".
- **T02.AC2** Given the fixture, when each task stage is looked up, then a task exists for every stage in the list above, with the exact words from ticket 07.
- **T02.AC3** Given the fixture and the recorded herdr file, when the board runs with that file, then the banner, Agents now and "herdr not running" can each be shown without a real herdr.
- **T02.AC4** Given the written list of fixture steps, when QA follows each, then the state it describes (unwritable file, storage blocked, server restart, new events, CLI answer) is reached.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
No module; test support. New files only.
- New: `tests/fixtures/board/**` (fixture squad, recorded herdr status file, transcripts, `FIXTURE-STEPS.md`), `tests/board_fixtures.py` (helper that copies the fixture to a temp dir and returns paths).
- Edit: none. The flag that reads the recorded herdr file is `squad-board --herdr-json FILE` (built in 08; AC3 is checked after 08).
- Test harness: `tests/test_board_fixtures.py` (checks the givens exist). Shared by all later tickets; later tickets may add fixture files only in their own subfolder.

## Comments
