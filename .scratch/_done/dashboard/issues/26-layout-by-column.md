# 26 Layout by column
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO, E10).
Design: `ui-design/design-v7.md` (start only when it reads `Status: final`; LC-2b). AC added: built UI matches the design: every screen and state (QA blackbox checks it). The Columns control of design v6 (table columns, ticket 20) stays as it is.
Status: ready-for-agent
Iteration: 2
Blocked by: design-v7 (and 25, 27: they share `board.js` / `board.css`; one Dev on those files at a time)
Feature: 1, 14 (`tasks/features.md`); PO iteration 2, issue 2

## What the PO gets
The page is arranged in columns, and the panels stack down a column. Today panels are placed by row and he finds it hard to use.

## Rules
- The page has N page columns side by side (not to be confused with the table columns of ticket 20). Panels sit one under the other inside a page column. A panel is as wide as its page column. **No control for the count (PO choice via Manager, design-v7 s2):** it follows the window. W = window width divided by the text scale (Small 0.9, Normal 1, Extra large 1.3): W 1800 and up = 3 columns; W 932 to 1799 = 2 (1440 px at Normal: 2, 1000 px at Normal: 2); W under 932 = 1 (Extra large near 1000 px). A page column is never narrower than 460 px at Normal. The count is not saved.
- A page column never shows an empty gap below a short panel while another panel waits: panels in a column follow each other with the gutter (12 px) between them. Columns may end at different heights.
- **Default place** (design-v7 s2; first load, Reset layout, a text-size change, a change of column count, only while the PO has not moved a panel; never on a data refresh): panels in the order Needs you, Tasks, Agents now, Files, Scopes of this goal (goal view only), Work time; each goes to the shortest column at that moment, the leftmost when equal. At 1440 px in a scope: left = Needs you, Agents now, Work time; right = Tasks, Files.
- The PO drags a panel to another place in its page column or to another page column; the drop spot shows where it will land. Resize changes a panel's height only (its width is the column's) — an assumption, the PO may change; the largest height of each panel is in `design-v7.md` s2 (Needs you 720, Tasks 560, Agents 380, Files 380, Scopes 300, Work time 780 px at Normal, scaled with text size); over it the panel body scrolls. East and corner resize are gone; south edge and Fit stay.
- Hide, Panels list, Reset layout, Fit, font sizes and the rule that the permission banner cannot be hidden or dragged (T10.AC2) stay. The banner stays above all columns, full width.
- Drag: the panel floats after 4 px, a dashed drop spot shows where it lands; Esc cancels (panel returns); a drop outside every column cancels; an empty column shows a dashed box `Drop a panel here`. Keyboard (panel title focused): Up/Down move it in its column, Left/Right to the next column (design-v7 s2).
- Show after hide returns the panel to its saved column and position; if that column no longer exists it appears in the last column.
- Saved with the layout (ticket 09): per panel column, position, hidden, max height. A column index above the current count shows in the last column but stays in the file, so a wider window restores it. A saved layout from the old row arrangement is not an error: the page ignores its positions and shows the default column layout, and keeps hidden panels hidden.
- Fit rule of ticket 10 stays per panel (as tall as its content up to a maximum, then scrolls inside).

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T26.AC1** Given the default layout at 1440 x 900 on the fixture, then the panels are in 2 page columns, with the default place of design-v7 s2 (left: Needs you, Agents now, Work time; right: Tasks, Files); in each page column, panel N+1's top = panel N's bottom + 12 px (within 2 px); and each panel's height is its content height up to its maximum (a short panel does not grow to match the other column).
- **T26.AC2** Given a short panel (e.g. Files, 1 row) above a tall one (8 rows) in one page column, then the panel below starts 12 px under the short one (T10.AC5 holds for columns), at 3 font sizes.
- **T26.AC3** Given the PO drags the Tasks panel to the other page column and between two panels there, then it lands where the drop spot showed, the column it left closes up (no gap), and after a reload (and on another port, T09.AC1) the place is the same.
- **T26.AC4** Given the PO hides a panel, then the panels under it in that column move up; given he shows it again, then it returns to its place in that column.
- **T26.AC5** Given a panel resized taller by the PO, then the panels under it in that column move down and no other column changes; its width stays the column's width.
- **T26.AC6** Given "Reset layout", then the default column layout returns, every panel's table columns return to default (T20.AC7), and font size and choice stay.
- **T26.AC7** Given a `board-ui.json` saved by the previous version (row-based positions), then the page opens without an error message, shows the default column layout, and hidden panels stay hidden.
- **T26.AC8** Given the window is 1000 px wide (2 page columns at Normal, 1 at Extra large), then nothing overlaps or is cut off (T10 rule); below 1000 px the page scrolls sideways (unchanged).
- **T26.AC9** Given the permission banner is shown, then it is above both columns, full width, and has no hide or drag control (T10.AC2).
- **T26.AC10** Given the built page at 1000, 1440 and 1920 px wide, then the number of page columns is 2, 2 and 3 (Normal text) and the place of each panel equals `design-v7.md` s2 at each width, and every screen and state of it matches (QA blackbox checks it). The page has no control for the column count.
- **T26.AC11** Given the PO drags a panel up or down inside the same page column, then it lands where the drop spot showed, and the other panels of that column close up with a 12 px gap; the order stays after a reload.
- **T26.AC12** Given a panel is taller than its content, when the PO presses Fit, then it becomes as tall as its content (up to its maximum) and the page columns stay.
- **T26.AC13** Given the window is resized from 1440 to 1920 px and back (Normal text), or the text size is changed to Extra large at 1000 px, then the count follows the table in Rules (3 at W 1800 and up, 2 at W 932 to 1799, 1 under 932), no column is narrower than 460 px at Normal (also at the W 932 and W 1799 edges; if the page margin makes a column narrower, the Designer changes the number in design-v7, not the AC), and the count is not in `board-ui.json`. A panel saved in column 3 shows in the last column at 2 columns and returns to column 3 at 3 columns.
- **T26.AC14** Given a drag in progress, when the PO presses Esc or drops outside every column, then the panel returns to where it was and nothing is saved; given an empty column, then it shows `Drop a panel here`.
- **T26.AC15** Given the Tasks panel title has focus, when the PO presses Up, Down, Left or Right, then the panel moves one place in its column (Up/Down) or to the next column (Left/Right), and focus stays on the title; Up on the first panel of a column, Down on the last, Left in the left-most column and Right in the right-most column move nothing (focus stays); moving to a column with fewer panels puts the panel last there.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: agreed (PASS AC 25-30, 2026-11-04; `tasks/business-ac-agreement.md`).

## Fixtures
A `board-ui.json` saved by iteration 1 (main 584720f): the Dev copies one written by that build into the test fixtures (hidden panel, moved panel, resized panel, a `columns` entry); T26.AC7 uses it. Fixture squad for the rest.

## Touched files
Tech Lead (`tasks/issues-tech/26.md`): `templates/board/layout.js`, `templates/board/board.js`, `templates/board/board.css`, `bin/squadboard_ui.py` (optional `col`; Manager decision D2), `tests/test_squadboard_panels.py` (browser: column stacking, drop, old saved layout). Design: `ui-design/design-v7.md`.

## Comments
- BA 2026-11-04: ticket 10 AC3-AC5 (LF1-LF3) were written for the row packing; the column rule here replaces their wording where they differ. The BA updates ticket 10 to point here.
