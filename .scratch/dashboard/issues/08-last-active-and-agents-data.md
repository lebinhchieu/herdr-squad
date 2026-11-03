# 08 last active and agents data
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 02, 03, 17
Feature: 12, 5 (`tasks/features.md`)

## What the PO gets
What went quiet, and who is working now.

## Rules
- Last active = newest of commit, message and transcript time, for a task, scope and goal. Unknown = "no activity recorded"; a missing source = "partial: <source> missing". Age words: ticket 10 (G8).
- Quiet: an in-progress task with a live owner and no activity for **60 min (fixed, no setting)** shows "quiet 3 h".
- Agents now from herdr status (or the recorded file) joined to `roster.md` (role, owns, live or retired), of the choice only; retired ones behind a click labelled "N retired".

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T08.AC1** Given a task last messaged 3 days ago whose owner works now, then last active reads like "3 min ago, approx" (not the message age). Given done, then the last message or commit age.
- **T08.AC2** Given no message, commit or transcript, then "no activity recorded".
- **T08.AC3** Given the transcript is missing but a commit exists, then the commit age with "partial: transcript missing".
- **T08.AC4** Given a goal, then its last active is its newest scope's, or later if the goal Manager acted.
- **T08.AC5** Given an in-progress task, a live owner and 90 min of silence, then "quiet 1 h 30 min"; given 30 min of silence, then no "quiet".
- **T08.AC6** Given 5 live agents and 1 retired, then 5 rows with role, task, status, time since last activity, and a control "1 retired" that shows the retired one.
- **T08.AC7** Given herdr is not running, then "status unknown: herdr not running" and roles still list.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Modules M6 + M7.
- New: `bin/squadboard_agents.py` (herdr status or `--herdr-json FILE`, roster join, banner entries), `bin/squadboard_active.py`.
- Edit: none (modules define `ROUTE`; see ticket 03).
- Tests (new): `tests/test_squadboard_agents.py`, `tests/test_squadboard_active.py`.
- Ticket 05 imports `squadboard_agents` after this ticket.

## Comments
