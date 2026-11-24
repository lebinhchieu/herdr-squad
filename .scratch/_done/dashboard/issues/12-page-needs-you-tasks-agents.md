# 12 page needs you tasks agents
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 1
Blocked by: 05, 06, 07, 08, 10, 11
Feature: 2, 3, 5, 12, 13, 7a (`tasks/features.md`)

## What the PO gets
The working panels: Needs you (with Parked), Tasks, Agents now, last active.

## Rules
- Needs you: open items oldest first, then a Parked group; each open item shows the copy-only text `squad-inbox answer E2` with a copy control. Tab title shows the count (ticket 10).
- Banner above all panels for permission prompts: one line per prompt (agent and pane), under every choice.
- Tasks: rows from ticket 07 with the flag "ready for review"; click opens detail (agents, steps in time order with local times, FAIL reason first line); click again or Esc closes it. No event feed.
- Agents now: small panel; "N retired" control.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T12.AC1** Given 2 open questions and 1 unread item, then 3 rows oldest first with id, title, age, what it blocks.
- **T12.AC2** Given nothing open, then "Nothing needs you".
- **T12.AC3** Given a question with options and a recommendation, then options show and the recommended one carries "recommended".
- **T12.AC4** Given 3 open and 1 parked, then Needs you shows 2 open and "Parked (1)", the tab title says "(2) <squad>", and the parked row names what it blocks.
- **T12.AC5** Given an open item, then `squad-inbox answer E2` (its id) is visible and, after the copy control is clicked, the clipboard holds exactly that text.
- **T12.AC6** Given two permission prompts, then two banner lines, each with agent and pane, under any choice; herdr not running gives "status unknown: herdr not running".
- **T12.AC7** Given tasks in all stages, then each row shows id, title, stage, owner, who it waits on, last active, in the words of ticket 07.
- **T12.AC8** Given the PO clicks a task, then its agents and steps show in time order in the local zone; Esc or a second click closes it.
- **T12.AC9** Given a branch is ready for review, then the task shows "ready for review" and the needs-you count includes it.
- **T12.AC10** Given every control on the page, then none is labelled answer, park, merge or anything that implies a write; commands are text only.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M13 part: working panels.
- New: `templates/board/panel_inbox.js`, `panel_tasks.js`, `panel_agents.js`.
- Edit: `templates/board/board.js` only to register the panels (one line each).
- Tests: extend `tests/test_squadboard_panels.py` (ticket 11 creates it; 11 before 12 to avoid a conflict in that file).
- Design: `ui-design/design-v5.md`.

## Comments
