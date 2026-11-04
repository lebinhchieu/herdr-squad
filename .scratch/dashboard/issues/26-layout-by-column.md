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
- The page has N page columns side by side (not to be confused with the table columns of ticket 20). Panels sit one under the other inside a page column. A panel is as wide as its page column. Default: 2 page columns at 1440 px; the Designer sets the count for other widths and the default place of each panel in design-v7 (if the Designer changes the 2, the AC numbers change with it, like the gutter).
- A page column never shows an empty gap below a short panel while another panel waits: panels in a column follow each other with the gutter (12 px) between them. Columns may end at different heights.
- The PO drags a panel to another place in its page column or to another page column; the drop spot shows where it will land. Resize changes a panel's height only (its width is the column's) — an assumption, the PO may change; the smallest and largest height are set in `design-v7.md` and checked at those two values.
- Hide, Panels list, Reset layout, Fit, font sizes and the rule that the permission banner cannot be hidden or dragged (T10.AC2) stay. The banner stays above all columns, full width.
- Saved with the layout (ticket 09). A saved layout from the old row arrangement is not an error: the page ignores its positions and shows the default column layout, and keeps hidden panels hidden.
- Fit rule of ticket 10 stays per panel (as tall as its content up to a maximum, then scrolls inside).

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T26.AC1** Given the default layout at 1440 x 900 on the fixture, then the panels are in 2 page columns (default count and place of each panel: only from `design-v7.md`); in each page column, panel N+1's top = panel N's bottom + 12 px (within 2 px); and each panel's height is its content height up to its maximum (a short panel does not grow to match the other column).
- **T26.AC2** Given a short panel (e.g. Files, 1 row) above a tall one (8 rows) in one page column, then the panel below starts 12 px under the short one (T10.AC5 holds for columns), at 3 font sizes.
- **T26.AC3** Given the PO drags the Tasks panel to the other page column and between two panels there, then it lands where the drop spot showed, the column it left closes up (no gap), and after a reload (and on another port, T09.AC1) the place is the same.
- **T26.AC4** Given the PO hides a panel, then the panels under it in that column move up; given he shows it again, then it returns to its place in that column.
- **T26.AC5** Given a panel resized taller by the PO, then the panels under it in that column move down and no other column changes; its width stays the column's width.
- **T26.AC6** Given "Reset layout", then the default column layout returns, every panel's table columns return to default (T20.AC7), and font size and choice stay.
- **T26.AC7** Given a `board-ui.json` saved by the previous version (row-based positions), then the page opens without an error message, shows the default column layout, and hidden panels stay hidden.
- **T26.AC8** Given the window is 1000 px wide, then nothing overlaps or is cut off (T10 rule); below 1000 px the page scrolls sideways (unchanged).
- **T26.AC9** Given the permission banner is shown, then it is above both columns, full width, and has no hide or drag control (T10.AC2).
- **T26.AC10** Given the built page at 1000, 1440 and 1920 px wide, then the number of page columns and the place of each panel equal `design-v7.md` at each width, and every screen and state of it matches (QA blackbox checks it).
- **T26.AC11** Given the PO drags a panel up or down inside the same page column, then it lands where the drop spot showed, and the other panels of that column close up with a 12 px gap; the order stays after a reload.
- **T26.AC12** Given a panel is taller than its content, when the PO presses Fit, then it becomes as tall as its content (up to its maximum) and the page columns stay.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Fixtures
A `board-ui.json` saved by iteration 1 (main 584720f): the Dev copies one written by that build into the test fixtures (hidden panel, moved panel, resized panel, a `columns` entry); T26.AC7 uses it. Fixture squad for the rest.

## Touched files
Set by the Manager: `templates/board/board.js`, `templates/board/board.css`, `tests/test_squadboard_panels.py` (browser: column stacking, drop, old saved layout). Design: `ui-design/design-v7.md`.

## Comments
- BA 2026-11-04: ticket 10 AC3-AC5 (LF1-LF3) were written for the row packing; the column rule here replaces their wording where they differ. The BA updates ticket 10 to point here.
