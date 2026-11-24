# 15 work time data
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 2
Blocked by: 02, 03, 17
Feature: 10 (`tasks/features.md`)

## What the PO gets
Per agent, how long it worked, waited, was blocked or idle, from transcripts.

## Rules
- Data for a requested time range of the choice: pieces per agent (start, end, working/waiting/blocked/idle, task, approx flag) in UTC, drawn from the unfiltered pieces. Task = latest message naming it, else roster `Owns`, else unattributed; the unattributed share is returned in hours and minutes (no %). Commit, hand-in, FAIL, PASS, BLOCKED, merge times as marks (copies within 120 s count once).
- A gap over N minutes (default 60, range 15 min to 4 h) is marked collapsible whatever its kind, so a night gap never reads as work; waiting and blocked pieces never collapse. Break labels use real elapsed time (checked across a DST change). No transcript: "no transcript", no time invented.
- Cut (E7): exact time per task, worktree/branch per slice, artifact marks.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T15.AC1** Given a Developer on task 03 for 2 h, then pieces for 03 split working/waiting/idle sum to the 2 h.
- **T15.AC2** Given time not tied to a task, then the unattributed share is returned as hours and minutes, never %.
- **T15.AC3** Given a task-attributed piece, then it carries "approx"; commit and hand-in marks do not.
- **T15.AC4** Given an agent with no transcript, then "no transcript: <agent>" and no time.
- **T15.AC5** Given an 11 h gap ended by a system record, then it is marked collapsible and not counted as working time.
- **T15.AC6** Given a gap across a DST change, then its label shows the real elapsed time.
- **T15.AC7** Given a time range, then only pieces in that range come back; a request with no choice is refused.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M9 (iteration 2).
- New: `bin/squadboard_worktime.py`.
- Edit: `bin/squadreport_tasks.py` only if `_segments` needs an `unfiltered` switch (additive); `bin/squadtranscript.py` is M10 (not in this ticket).
- Tests (new): `tests/test_squadboard_worktime.py`; `tests/test_squadreport_tasks.py` must still pass.
- Order: after 17 (which also edits `squadreport_tasks.py`).

## Comments
