# 35 Smart grid
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. **35 and 36 are checked together in one QA pass (PO wish).**
Design: `ui-design/design-v8.md` (start only when it reads `Status: final`; LC-2b). AC added: the built UI matches the design: every screen and state (QA blackbox checks it). Every AC that needs a number cites a design-v8 section; the number lives there, not here.
Status: ready-for-agent
Iteration: 3
Blocked by: design-v8 (final); BA AC (this file). 36 waits for this ticket (same files).
Feature: PO iteration 3, request 1 (`tasks/po-request-iter3.md`)

## What the PO gets
Panels sit in a smart grid: a panel can be wider than one column, the grid has no holes a panel could fill, and dragging still works. Today (ticket 26) every panel is one column wide and the page is not what he expects.

## Rules
- **Grid.** The page is a grid of N grid columns with a 12 px gutter; N follows the window as in design-v8 s?? (table by width and text scale; ticket 26 had 3 / 2 / 1; the Designer may change it, and may use finer tracks). No control for N; N is not saved. A panel takes 1 or more grid columns (its span). Default spans and default order are in design-v8 s??. Resize of the span is ticket 36; this ticket uses default spans only.
- **Smart = fills holes.** Panels are placed in order. A panel goes to the first free spot, top first and then left, where it fits at its span; so a later, narrower panel can sit beside an earlier one, in a hole, instead of under it. Nothing overlaps. design-v8 s?? has a worked example (arrangement, one hide or move, result, with a mock); the hole AC cite it.
- **No gaps down a column.** A panel's top is the bottom of the lowest panel above it in its grid columns, plus the 12 px gutter. Columns may end at different heights.
- **Stable on refresh.** A data refresh (5 s) never moves a panel (T10.AC16). Only a PO action (drag, hide, show, Reset, Fit, height resize), or a change of window width or text size, places panels again. If the design needs live heights to place, the Designer says how this is kept.
- **Order.** The panel order starts as in ticket 26 (Needs you, Tasks, Agents now, Files, Scopes of this goal (goal view only), Work time) and changes only when the PO drags a panel. The order is saved with the layout (ticket 09).
- **Drag.** As ticket 26: the panel floats after 4 px; a dashed drop spot shows where it will land in the grid; Esc or a drop outside the grid cancels (nothing saved); an empty grid shows a dashed box `Drop a panel here`. The drop spot is the real landing place.
- **Keyboard.** BA default (the Designer may change the map; AC then follow design-v8): with a panel title focused, Up/Left move the panel one place earlier in the order, Down/Right one place later; focus stays on the title; nothing moves at the first or last place.
- **Stay as they are:** Hide, Panels list, Reset layout, Fit, font sizes, height resize by the south edge (largest heights of design-v7 s2), the permission banner above the grid, full width, no hide or drag (T10.AC2), the table columns control (ticket 20).
- **Saved layout.** Per panel: place in the order, hidden, max height (ticket 09). A layout saved by iteration 2 (`col`, `order`) or iteration 1 (numeric panel ids, `span` with an older meaning) is not an error: the page shows the layout design-v8 s?? says (default grid, or the nearest order), hidden panels stay hidden and saved heights are kept. **An old `span` is never read as a column span.** The Tech Lead and the Designer say how an iteration-1 file and an iteration-3 file are told apart (a new key name, or the `version` field); ticket 36 saves the new span with that key.
- Panel text, colours and the Files, Tasks, Work time contents stay (Light Mango Parrot, from the theme file).
- Ticket 25 (Panels dropdown) is not changed; QA blackbox re-runs its checks in the same pass.

## Earlier AC: what this ticket replaces (stop checking them)
T26.AC1, AC3, AC10, AC11, AC13, AC14 (page columns, drop between columns, counts), AC15 (keyboard map), AC7 (old saved layout: now T35.AC8). T26.AC2, AC4, AC5, AC6, AC8, AC9, AC12 stay true where they make sense for a grid: their grid versions are T35.AC3, AC5, AC7, AC9. The T26 default place (design-v7 s2) is replaced by design-v8 s??. T10.AC3-AC5 (row packing wording) were already replaced by 26.

## Business AC (one Given / When / Then each; a FAIL names one id). Every UI AC names its window size and the rule it is checked at (SQ-7). Text size Normal unless said.
- **T35.AC1** Rule: default placement, `design-v8` default tables (scope view and goal view). Given the default layout on the fixture, scope `checkout` and the goal view (`alpha`), at 1440 x 900, then each panel's column and row position equals the table in design-v8 s?? for that view (2 px; "Scopes of this goal" is in the goal table), nothing overlaps, and the gutter between neighbours (side and under) is 12 px (2 px).
- **T35.AC2** Rule: N follows the window, `design-v8` width table. Given the default layout at 1000 x 800, 1440 x 900 and 1920 x 1000 (Normal), and at 1000 x 800 with Extra large text, then the number of grid columns and each panel's place equal design-v8 s?? at each size; N is not in `board-ui.json`; resizing the window from 1440 to 1920 and back (and changing text size) gives the table's N each time; nothing overlaps or is cut off at any of these sizes (T10 rule); below 1000 px the page scrolls sideways (unchanged).
- **T35.AC3** Rule: no gaps down a column. Given the default layout at 1440 x 900 at the 3 text sizes (Small, Normal, Extra large), then for every panel its top = the bottom of the lowest panel above it in its grid columns + 12 px (2 px), or the panel is at the top; a short panel (Files with 1 row) does not leave a gap under it.
- **T35.AC4** Rule: fills holes, the worked example of `design-v8` s??. Given the arrangement of the worked example on the fixture at the width the example names, when the PO does the hide or move the example names, then every panel's place equals the example's result (2 px), the panel that moves up to fill the hole is the one the example shows, and nothing overlaps.
- **T35.AC5** Rule: hide and show. Given the default layout at 1440 x 900, when the PO hides a panel, then the other panels re-place by the hole rule (AC4) with no gap (AC3); given he shows it again, then it returns to its place in the order and the layout equals the one before the hide.
- **T35.AC6a** Rule: drag, at 1440 x 900. Given the PO drags the Tasks panel title more than 4 px, then it floats and a dashed drop spot shows its landing place.
- **T35.AC6b** Rule: drop, at 1440 x 900. Given the drag of AC6a, when he drops, then the panel lands exactly where the drop spot showed (2 px), the other panels re-place with no gap, and after a reload (and on another port, T09.AC1) the order is the same.
- **T35.AC6c** Rule: cancel, at 1440 x 900. Given a drag in progress, when the PO presses Esc, or drops outside the grid, then the panel returns to where it was and `board-ui.json` is the same as before (same bytes).
- **T35.AC6d** Rule: empty grid, at 1440 x 900. Given every panel is hidden, then the grid shows `Drop a panel here`.
- **T35.AC7** Rule: height resize, at 1440 x 900. Given a panel made taller by its south edge, then the panels below it in its grid columns move down, a panel beside it that does not share its grid columns does not move up or down, and its span is unchanged; given Fit, then it is as tall as its content up to its maximum (design-v7 s2).
- **T35.AC8** Rule: old saved layouts, at 1440 x 900. Given a `board-ui.json` saved by iteration 2 (`col`, `order`, hidden, one resized height) and one saved by iteration 1 (`layout-26/board-ui-iter1.json`, with its `span` values), then the page opens without an error message, shows the layout design-v8 s?? names, hidden panels stay hidden, the saved height of the resized panel is kept, and no panel is wider than the default span because of an old `span` value.
- **T35.AC9** Rule: Reset layout, at 1440 x 900. Given "Reset layout", then the default grid of AC1 returns, every panel's table columns return to default (T20.AC7), and font size and choice stay.
- **T35.AC10** Rule: stable on refresh, at 1440 x 900. Given the board is open and the data changes so that a panel's content gets taller or shorter (a new message is appended; step 4 of `FIXTURE-STEPS.md`), when the page refreshes, then the order of the panels and each panel's left position are unchanged, and a panel's top moves only by the height change of the panels above it in its columns; no panel jumps into another hole.
- **T35.AC11** Rule: keyboard, at 1440 x 900. Given the Tasks panel title has focus, when the PO presses Up, Left, Down or Right, then the panel moves one place earlier (Up, Left) or later (Down, Right) in the order, and focus stays on the title; at the first or last place it moves nothing and focus stays.
- **T35.AC12** Rule: banner and goal view, at 1440 x 900. Given the permission banner is shown, then it is above the grid, full width, and has no hide or drag control (T10.AC2); given the goal view, then "Scopes of this goal" is placed by the same rules and the panel order of Rules.
- **T35.AC13** Rule: built UI matches `design-v8.md`, at 1000, 1440 and 1920 px wide. Given the built page, then every screen and state in design-v8 (default grid, holes, drag in progress, drop spot, empty grid, narrow window, saved-layout migration) matches the design's mock (QA blackbox checks it).

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox review applied 2026-11-04 (35-M2, S1-S4). QA blackbox: pending final confirmation (needs design-v8 final for the `s??` numbers)

## Fixtures
Fixture squad, scope `checkout` and a goal view. A `board-ui.json` saved by iteration 1 (`tests/fixtures/board/layout-26/board-ui-iter1.json`) and one saved by iteration 2: the Dev writes it from a build of main 181b048 (hidden panel, moved panel, resized panel) and commits it next to the first one. The message-append step of `FIXTURE-STEPS.md` for AC10.

## Touched files
Tech Lead (`tasks/issues-tech/35.md`; the Manager's plan decides): expected `templates/board/layout.js`, `board.js`, `board.css`, `bin/squadboard_ui.py` (saved layout), `tests/test_squadboard_panels.py`. 36 touches the same files, so 36 runs after this.

## Comments
- BA 2026-11-04: "smart grid" read as: panels have spans, and a later panel may fill a hole beside an earlier one. The PO may correct it. The Designer's worked example is the measured form of "fills holes".
- BA 2026-11-04: constraints sent to the Designer: `tasks/ba-constraints-v8.md`.
