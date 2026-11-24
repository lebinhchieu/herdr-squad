# 04 choice data picker
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 02, 03, 17
Feature: 11, 4 (`tasks/features.md`)

## What the PO gets
The data for the picker and for the goal and scope views: what exists, what needs the PO, how recent.

## Rules
- Goals and lone scopes (open and done), scopes of a goal, brief, goal-less scopes tagged "no goal", close date (folder time; shown with the word "approx"), tasks "x of y done".
- Per row, in this order: needs you N, stuck N, tasks "x of y", agents working now, last active, N new.
- Goal status is not derived: the Scopes table cells show as written; open/done is by folder.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T04.AC1** Given the fixture, when picker data is asked with no choice, then it holds only names and the six row facts (no task, inbox or work-time data); Open is ordered by needs-you (most first), then stuck, then last active; Done (20) is separate, newest close first.
- **T04.AC2** Given the data is asked with `goal=G` or `scope=S`, then only that choice's rows come back; with neither, the answer is "selection required".
- **T04.AC3** Given goal G with S1 (2 tasks open) and S2 done, then G lists S1 and S2 (S2 marked done).
- **T04.AC4** Given a lone scope, then it says "no goal". Given a goal with no scope, then "No scopes in this goal".
- **T04.AC5** Given a closed scope, then its close date shows as "closed <date> (approx)" and its data is read-only.
- **T04.AC6** Given a saved choice whose folder is in neither the live place nor `_done/`, then "saved choice <name> not found".

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M2.
- New: `bin/squadboard_list.py` (`/api/squads`, summary facts per scope, cheap sources only).
- Edit: none (the module defines `ROUTE`; see ticket 03).
- Tests (new): `tests/test_squadboard_list.py` (includes the 25-scope speed check).
- Uses: `squadboard_time.py`, `squadboard_git.py`, `squadtickets.py` (ticket 17).

## Comments
