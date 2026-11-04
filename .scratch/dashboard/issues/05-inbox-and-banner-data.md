# 05 inbox and banner data
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 02, 03, 08
Feature: 2 (`tasks/features.md`)

## What the PO gets
What waits on the PO: open questions, answers to read, permission prompts, and the needs-you count.

## Rules
- Rows from `squad-inbox list --json --no-write` for the choice (the page never writes inbox files). Permission banner from herdr status `blocked` (or the recorded file), squad-wide.
- Needs-you count = open questions + answers to read + branches ready to merge + permission prompts; parked excluded; squad-wide count, plus "N more need you in <name>" for items outside the choice.
- Visible columns of an inbox row: id, title, age, what it blocks, options; the recommended option carries the text "recommended".

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T05.AC1** Given 2 open questions and 1 unread item in the choice, then 3 rows, oldest first, with id, title, age, what it blocks.
- **T05.AC2** Given nothing open, then "Nothing needs you".
- **T05.AC3** Given a question with options and a recommendation, then the options show in the row and the recommended one carries the text "recommended".
- **T05.AC4** Given the PO answers by CLI, when the next refresh runs, then the item is gone and the count drops. Given the page runs, then `inbox.jsonl` gets no new line from it.
- **T05.AC5** Given an agent waits on a permission prompt in any scope, then the banner data names the agent and its pane whatever the choice; two prompts give two entries.
- **T05.AC6** Given scope S3 has an open question and the choice is S1, then the count includes it and "1 more needs you in S3" is offered; given the PO answers S3's question by CLI, then that line and the count drop within one refresh.
- **T05.AC7** Given herdr is not running, then "status unknown: herdr not running", never an empty banner or "all good".
- **T05.AC8** Given a ready-for-review branch of S3 and the choice S1, then it counts in "N more need you in S3" and its task row does not show under S1.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M3.
- New: `bin/squadboard_inbox.py` (calls `squad-inbox list --json --no-write`; needs-you count; banner entries come from `squadboard_agents.read`, ticket 08).
- Edit: none.
- Tests (new): `tests/test_squadboard_inbox.py`.
- Order: after 08 (the permission banner uses the agents reader).

## Comments
