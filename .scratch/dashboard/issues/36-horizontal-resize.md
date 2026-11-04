# 36 Horizontal resize
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. **35 and 36 are checked together in one QA pass (PO wish).**
Design: `ui-design/design-v8.md` (start only when it reads `Status: final`; LC-2b). AC added: the built UI matches the design: every screen and state (QA blackbox checks it). Numbers live in design-v8; AC cite its sections.
Status: ready-for-agent
Iteration: 3
Blocked by: 35 (same files; the grid and its hole rule must exist), design-v8 (final)
Feature: PO iteration 3, request 1 (`tasks/po-request-iter3.md`)

## What the PO gets
He drags the right edge of a panel and the panel takes 1 to N grid columns; the other panels move around it. The width comes back when he reopens the board.

## Rules
- Every panel has a resize handle on its right edge (look and hit area: design-v8 s??). A drag moves the edge; it snaps to grid column boundaries. The panel's span is a whole number of grid columns, from 1 to N (N = the grid column count at this window width, ticket 35). Never a width between two spans.
- While dragging, an outline shows the span the panel will take on release. Release sets it (a release outside the browser window counts as a release at the last position). Esc cancels: the span stays as before and nothing is saved. A window resize in the middle of a drag cancels the drag. Dragging beyond 1 or N stays at 1 or N.
- Other panels re-place by the hole rule of ticket 35: a wider panel pushes later panels along; a narrower one lets later panels fill the hole. A panel's height setting (max height) is kept as the PO set it.
- Saved per panel with the layout in `board-ui.json` (ticket 09): the span, under a key that cannot be mistaken for the iteration-1 `span` (the Tech Lead and Designer name it, see ticket 35). A saved span that is a whole number above the current N shows as N and stays in the file, so a wider window restores it. **A value that is 0, negative or not a number is read as the default span of the panel** (BA decision, settles the Designer's choice); the page opens without an error message and the file keeps the value until the PO changes that panel.
- With N = 1 (a narrow window, or Extra large text near 1000 px) there is nothing to resize: no handle shows.
- Keyboard: the handle can take focus (Tab); with it focused, Left makes the panel one column narrower and Right one wider; focus stays on the handle; at 1 or N nothing changes (BA default, the Designer may change the keys: AC then follow design-v8).
- Reset layout returns every span to the default span of design-v8 s??. Fit and the south-edge height resize stay as they are and are independent of width. Hide then Show returns the panel with its saved span. The permission banner has no handle (T10.AC2).
- Panel contents stay readable: nothing is cut off at 1000, 1440 and 1920 px (T10 rule); a table wider than its panel scrolls inside the panel body (unchanged).

## Earlier AC: what this ticket replaces
T26 said "resize changes a panel's height only; east and corner resize are gone". That rule is replaced for the east edge: it now sets the span. The corner handle stays gone unless design-v8 s?? brings it back. T26.AC5 (height only) stays true for the south edge.

## Business AC (one Given / When / Then each; a FAIL names one id). Every UI AC names its window size and the rule it is checked at (SQ-7). Text size Normal unless said.
- **T36.AC1** Rule: handle exists when N >= 2, `design-v8` s?? for the handle. Given the board at 1440 x 900 (N from design-v8) and at 1920 x 1000, then every panel shows a handle on its right edge with the hit area design-v8 states (measured); given 1000 x 800 with Extra large text (N = 1), then no panel shows a handle; the banner never has one.
- **T36.AC2a** Rule: span = whole columns, at 1440 x 900. Given the Tasks panel at its default span, when the PO drags its right edge to the right by about one grid column and releases, then its width = span x column width + (span - 1) x 12 px (2 px) with the span one larger.
- **T36.AC2b** Rule: snap, at 1440 x 900 and 1920 x 1000. Given a drag that ends between two column boundaries, then the panel snaps to the nearest boundary and its width is a whole-span width, never the in-between width; at 1920 x 1000 the same works from span 1 up to 3.
- **T36.AC3** Rule: limits, at 1440 x 900 and 1920 x 1000. Given a drag far to the left, then the panel stays at span 1; given a drag far to the right, then it stays at span N (N for this window width).
- **T36.AC4** Rule: live outline. Given a drag in progress at 1440 x 900, then an outline shows the span the panel will take, and it changes as the pointer crosses a column boundary; when the PO releases, the width equals the outline's width (2 px).
- **T36.AC5** Rule: Esc cancels, at 1440 x 900. Given a drag in progress, when the PO presses Esc, then the panel returns to its width from before the drag, the other panels return to their places, and `board-ui.json` is the same as before the drag (same bytes).
- **T36.AC6** Rule: neighbours re-place by the hole rule of ticket 35, at 1440 x 900 and 1920 x 1000. Given a panel is made wider, then later panels move (beside or under it) with no overlap, gutters of 12 px (2 px), and no gap down a column (T35.AC3); given a panel is made narrower, then a later panel that fits the freed space moves into it as the hole rule says (the worked example of design-v8 s?? done by resize), and nothing overlaps.
- **T36.AC7** Rule: saved, at 1440 x 900. Given three panels with changed spans, when the board reopens on another port or browser (T09.AC1) at 1440 x 900, then each span, order and hidden state is the same; `board-ui.json` holds the span of each changed panel as a whole number. Given an iteration-1 file with `span: 2` on a panel, then that panel shows its default span; given a file saved by this version with span 2, then it shows span 2.
- **T36.AC8** Rule: window narrower and wider. Given a panel saved at span 3, when the window goes from 1920 to 1440 (N drops), then it shows at span N and `board-ui.json` still holds 3; when the window goes back to 1920, then it shows at span 3 again.
- **T36.AC9** Rule: bad saved values, at 1440 x 900. Given a `board-ui.json` with a panel span of 0, -2, `"wide"` and 99 (one panel each), then the page opens without an error message, the panels with 0, -2 and `"wide"` show their default span, the panel with 99 shows span N (2 at 1440 x 900), and the other panels are as saved.
- **T36.AC10** Rule: keyboard, at 1440 x 900. Given a handle has focus (Tab to it), when the PO presses Right, then the panel is one column wider; Left, one narrower; focus stays on the handle; at span 1 Left and at span N Right change nothing.
- **T36.AC11** Rule: Reset layout, hide and show, at 1440 x 900. Given a changed span, when the PO uses "Reset layout", then the span returns to the default of design-v8 and the table columns return to default (T20.AC7); given a hidden panel with a changed span is shown again, then it returns with its saved span.
- **T36.AC12** Rule: height stays independent, at 1440 x 900. Given a panel resized taller by its south edge, when its width is changed, then the height saved in `board-ui.json` for it is the same before and after; given Fit, then the width is unchanged.
- **T36.AC13** Rule: nothing cut off, at 1000, 1440 and 1920 px wide. Given the Tasks panel at span 1 and at span N, then the table or its panel body scrolls inside and no panel's content is cut off at the page edge or overlaps another panel (T10 rule).
- **T36.AC14** Rule: built UI matches `design-v8.md`, at 1000, 1440 and 1920 px wide. Given the built page, then every screen and state in design-v8 (handle at rest, hover, focus, drag with outline, limits, narrow window, saved span above N) matches the design's mock (QA blackbox checks it).

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox review applied 2026-11-04 (36-M1..M3, S1, S2; the bad-value result is now fixed in the Rules). QA blackbox: pending final confirmation (needs design-v8 final for the `s??` numbers)

## Fixtures
Fixture squad; a `board-ui.json` with bad span values (0, -2, "wide", 99) and one with a span of 3 (the Dev adds both to the fixtures).

## Touched files
Tech Lead (`tasks/issues-tech/36.md`; the Manager's plan decides): same files as 35, runs after it; `tests/test_squadboard_panels.py` and `tests/test_squadboard_ui.py` for the saved span.

## Comments
- BA 2026-11-04: the PO said "1..N columns". With the T26 count table N is 2 at 1440. If design-v8 uses finer tracks, "1..N" then means "smallest readable width..N" and the BA edits AC1-AC3, AC6, AC13 to the Designer's numbers.
