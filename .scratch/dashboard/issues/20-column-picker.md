# 20 column picker
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`; the Designer adds the picker control, see Comments). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 2
Blocked by: 11
Feature: 1, 14 (`tasks/features.md`; the "column choose cut" there is restored by the Manager's decision, PO iteration 2: picker IN)

## What the PO gets
In each table panel he chooses which columns show and in which order, and it comes back next time.

## Rules
- Table panels: Tasks, Agents now, Files and the Scopes strip of a goal. Each has a Columns control. Needs you (a list) and Work time (a timeline) have no Columns control. There is no Decisions panel: goal and scope decisions are listed in Files (ticket 14).
- Each table panel has one "Columns" control: a list of its columns with a check box each and a way to move one up or down (drag or arrow buttons). Changes show at once.
- Each panel has one **identity column** (Tasks: Task; Agents now: agent name; Files: name; Scopes strip: scope name). It cannot be hidden, wherever the PO moves it (it may move, e.g. to the last place). So a table never has zero columns and a row always says what it is. The other columns can all be hidden. "Reset columns" in the control returns that panel to its default.
- Saved per squad in `board-ui.json` (ticket 09 format, new field for columns, same `saved_at` rule), one setting for every choice (goal or scope). The Scope column of a goal view follows the same rule; it shows only in a goal view, and a hidden or moved setting is kept when the PO opens a scope.
- "Reset layout" (ticket 10) also resets every panel's columns, as feature 14 says. Font size and the choice are not touched.
- Hiding a column never changes what counts: the needs-you count, the tab title and the "ready for review" flag stay as they are even if the column that shows them is hidden.
- No `%` character in the control; no write other than `board-ui.json`.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T20.AC1** Given the Tasks panel with its default columns, when the PO opens "Columns", then every column of the panel (Task, Title, Stage, Last active, What happened, Agents involved, Waits on; Scope in a goal view) is listed in its current order with a check box; the Task box cannot be cleared. Given the PO moves Task to the last place and clears all other boxes, then only Task shows, last.
- **T20.AC2** Given the PO clears "Waits on" in Tasks, then the Waits on column is gone at once and the other columns keep their order; given he checks it again, then it returns in its place. Given the same in Files, Agents now and the Scopes strip, then each panel has its own Columns control and the same behaviour.
- **T20.AC3** Given the PO moves "Last active" before "Stage", then the table shows that order at once.
- **T20.AC4** Given Tasks has a hidden column and a new order, when the board is reopened on another port or browser, then the same columns show in the same order (T09.AC1 rule); given the file is unwritable, then the browser copy holds it with "settings not shared".
- **T20.AC5** Given the same setting, when the PO switches between a goal, a scope, and back, then the columns are the same (Scope column only in a goal view; its place in the order is kept).
- **T20.AC6** Given a task is "ready for review" and the column that shows the flag is hidden, then the needs-you count and the tab title still include it.
- **T20.AC7** Given columns changed in Tasks, Agents now and Files, when the PO clicks "Reset columns" in Tasks, then only Tasks returns to default; given he clicks "Reset layout", then all three return to default and font size and choice stay.
- **T20.AC8** Given the picker shows a table panel at "Extra large" font and 1000 px width, then the control opens without being cut off (it scrolls if long) and the table keeps LF1 to LF6 of ticket 10.
- **T20.AC10** Given the Needs you panel and the Work time panel, then neither has a Columns control, and "Reset layout" does not change what they show.
- **T20.AC9** Given the file has columns for a panel that no longer exists, or a column name the page does not know, then the page ignores it, shows the defaults for that panel, and does not fail.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: confirmed (`tasks/business-ac-agreement.md`).

## Touched files
Set by the Manager (iteration 2; builds on 09, 11, 12, 14 passed).
- Edit: `bin/squadboard_ui.py` (additive `columns` field in `board-ui.json`, schema_version unchanged; never raises on a bad value).
- Edit: `templates/board/board.js` (columns hook: one control, save, Reset layout resets columns; minimal lines).
- Edit: the panel files that show columns (`panel_tasks.js`, `panel_agents.js`, `panel_scopes.js`, files panel of 14).
- Tests: extend `tests/test_squadboard_ui.py` (field) and `tests/test_squadboard_panels.py` (control).
- Design: `ui-design/design-v6.md` (Status: final; with `design-v5.md`). AC added: built UI matches the design: every screen and state.

## Comments
- BA 2026-11-04: Manager restored the column picker (PO iteration 2). Ticket 10 rule "No column picker (cut)" and features.md lines 23, 29, 90 are updated by the BA to point here. The Designer must draw the control, its open state and its Extra large state.
