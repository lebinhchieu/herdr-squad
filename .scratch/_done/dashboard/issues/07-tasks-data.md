# 07 tasks data
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 02, 03, 17
Feature: 3, 7a, 16 (`tasks/features.md`)

## What the PO gets
Every task, its stage and what happened to it; ready for review; new-event counts.

## Rules
- A row is a task only with a ticket file or a plan-table row (a token like `REV-8` is not a task). Optional `tickets: <feature-slug>` line in `scope.md` names the ticket folder; else the reader guesses (one shared copy of the guess, used by report and board).
- Stage words (exact): `todo`, `in progress`, `returned`, `blocked`, `done`, `ready for review`, `sha changed after PASS`, `merged`; while checking: `checking, 1 of 2 PASS, waiting on QA blackbox, 40 min`. A task with no owner shows `unassigned`.
- Ready for review = every checker PASS on the branch tip and unmerged. It counts toward needs-you only while ready. Branches of other scopes never show.
- Returns: "3 returns" and the first line of the newest FAIL reason in the row; all steps in the detail.
- "N new" = HANDIN, FAIL, PASS, BLOCKED, DECISION events newer than a time the page sends.
- Age words: see ticket 10 (G8).

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T07.AC1** Given tasks in all stages, then each row has id, title, stage (exact word), owner, who it waits on, last active.
- **T07.AC2** Given a todo task with no owner, then the owner shows "unassigned", not blank.
- **T07.AC3** Given a task with 3 FAIL shas, then the row shows "3 returns" and the first line of the newest reason.
- **T07.AC4** Given one checker PASS and one missing, then the row reads "checking, 1 of 2 PASS, waiting on QA blackbox, 40 min", not "done".
- **T07.AC5** Given all checkers PASS the branch tip and it is unmerged, then "ready for review" and it counts in needs-you.
- **T07.AC6** Given the tip moved after PASS, then "sha changed after PASS", not ready, not counted. Given merged, then "merged", not ready, not counted.
- **T07.AC7** Given a message token `REV-8` with no ticket, then no task row.
- **T07.AC8** Given `tickets:` in `scope.md`, then that folder is used; without it, tasks still list.
- **T07.AC9** Given a goal choice, then tasks carry a Scope column; given a scope choice, then no Scope column.
- **T07.AC10** Given a task's detail is asked, then agents and steps come in time order with times; no free-text feed.
- **T07.AC11** Given 2 PASS and 1 FAIL on task 03 after the given time, then 03 counts "3 new" and its scope's count includes them. Given no time (first visit), then 0 new.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M5 + the reader half of M11.
- New: `bin/squadboard_tasks.py`.
- Edit: `bin/squadtickets.py` (read `tickets:` from `scope.md`; file created by ticket 17).
- Tests (new): `tests/test_squadboard_tasks.py`; extend `tests/test_squadtickets.py`.
- Uses the `tickets:` line text defined by ticket 06; if 06 is not merged, test with a fixture `scope.md` carrying that line.

## Comments
