# Evidence 40: Work time control corners

## Behaviour
One CSS rule changed (`templates/board/timeline.js:549`): `.tl .seg` loses the 1px border, 8px corner and `overflow:hidden` it inherited from `board.css`. The `−+` and `◀▶` groups were a 28px box with an 8px corner around two pill buttons (double outline, clipped focus ring). Now the buttons carry the round ends alone: segment 62.4x26.4 instead of 64.4x28.4.

Finding about the "All" pill: `All` and `All tasks` are 999px on all four corners at rest, hover, focus, active, at 1000 px, Extra large and a narrow panel, **before and after** the fix. The square look the PO saw came from the two segments, not from the pill.

Crops (Playwright, device scale 3, not browser zoom; script `shots-40.js` next to this file; "before" serves `timeline.js` from `00d8ca7~1`). Taken on the demo (`--demo`, `?squad=fix&goal=alpha&scope=checkout`).

| Case | Before | After |
|---|---|---|
| 1440 | ![before 1440](img/bar-before-1440.png) | ![after 1440](img/bar-after-1440.png) |
| 1000 | ![before 1000](img/bar-before-1000.png) | ![after 1000](img/bar-after-1000.png) |
| Wrapped (Extra large, 1.3 font) | ![before wrapped](img/bar-before-wrapped.png) | ![after wrapped](img/bar-after-wrapped.png) |
| Narrow panel | ![before narrow](img/bar-before-narrow.png) | ![after narrow](img/bar-after-narrow.png) |
| Hover | ![before hover](img/bar-before-hover.png) | ![after hover](img/bar-after-hover.png) |

The 1000 and wrapped crops are identical: the bar has the same width at both; the narrow crop shows the wrapped rows.

## AC table
All proofs are in `tests/test_squadboard_timeline.py::Safety::test_T40_TA1_TA2_TA3_pills_and_segments_are_round_and_not_clipped` (l.436-506), which loops 4 cases: 1440x900, 1000x700, 1000x700 Extra large (20.8px), 1440x900 narrow panel (parent 330 px, asserted <= 360).

| Item | Claim | Proof |
|---|---|---|
| T40.AC1 | every `.tl-bar .tc`: 4 radii >= half height | test l.469-490 (count >= 8 asserted); crops 1440 |
| T40.AC2 | segment ends round, inner corners 0, 1px line between | test l.469-486; templates/board/timeline.js:549-550 |
| T40.AC3 | same at 1000x700, both buttons on one line | test case 1000x700, `whole` l.480; crops 1000 |
| T40.AC4 | same at Extra large | test case 1000x700 Extra large; crops wrapped |
| T40.AC5 | same in a narrow panel | test case narrow panel; crops narrow; see gap 2 |
| T40.AC6 | hover, focus, active keep corners; ring not clipped; active chip mango | test l.487-499 (focus ring inside clipping ancestor for `−`, `▶`, `All`, `All tasks`; hover rules copied to a class, hovRules >= 1); crops hover |
| T40.AC7 | demo gives the same | crops (demo); see gap 1 |
| T40.AC8 | nothing else moves, zoom/pan work | test l.484 (heights 26 px); timeline, worktime, page, grid, panels pins green |
| T40.TA1 | computed corners at 1440 | test l.469-486 |
| T40.TA2 | nothing clipped, all states, All pill radii at rest/hover/focus/active/narrow | test l.487-499, `All` and `All tasks` asserted 999px |
| T40.TA3 | nothing else moves; Text size / Sort keep 8px + hidden | test l.484 and l.501 |
| T40.TA4 | demo | screenshots + computed values only (gap 1) |
| T40.TA5 | before/after crops 1440 and 1000, scale 3, wrapped, script kept | this file; shots-40.js |
| T40.TA6 | diff only timeline.js + test | `git show --stat 00d8ca7 5ccab11`: timeline.js (1 line), test_squadboard_timeline.py; no board.css |
| T40.TAx | counts asserted so an empty loop fails | test l.469 (segs == 2), chips >= 8 |

Fails without the fix: with `timeline.js` from `00d8ca7~1` the test fails.
Pins run: test_squadboard_timeline (29 OK), worktime (22 OK), page (20 OK), grid (28 OK), panels (58, 1 known fail), test_squadreport_tasks (14 OK), test_squadreport_ui (27 OK).

## Known / open gaps
1. TA4: the demo is covered by crops and computed values taken on the demo, not by a test loop over two servers.
2. Narrow panel is set by the parent width (330 px, asserted <= 360), not by the T36 resize handle.
3. The test_T12 `1 d ago` failure in test_squadboard_panels.py also fails on main.
