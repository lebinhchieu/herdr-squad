# Evidence 26: Layout by column

## Behaviour
`#canvas` is a CSS grid of N `.col` elements (12 px gap). N = `BOARD.layout.colCount(innerWidth, scale)`: 3 from W 1800, 2 from W 932, else 1 (W = width / text scale); not saved, no control. Panels are normal blocks in a column, so a short panel is as tall as its content and the next one starts 12 px under it. `layout.js` pure helpers: `colCount`, `place` (shortest column, leftmost on a tie), `norm` (clamps `col` for display only, skips hidden and no-col panels, sorts by `order`, tie by default order).
The default place runs on first load, Reset layout, a new choice, a text-size change and a change of column count, only while `auto` is true; never on a data refresh, hide or show. Drag: header, 4 px, dashed drop spot, column outline, Esc or a drop outside cancels, `Drop a panel here` in an empty column. Keyboard: Up/Down in the column, Left/Right to the next column, focus stays on the title; Shift+Up/Down 80 px. Resize: south edge and Fit only (east and corner handles removed).
Saved: per panel `col` (0..11, optional), `order` (place in the column), `hidden`, `max_height`; `span` is no longer written. A file without `col` shows the default place, keeps hidden panels hidden and heights, and nothing is written on load. A `col` above the count shows in the last column; the file keeps it. Server (`bin/squadboard_ui.py`): `col` optional integer 0..11, `span` optional. The Manager confirmed this (decisions-iter2 D2, FINAL 26).

## AC table
| Id | Shown by |
|---|---|
| T26.AC1, AC2, AC8, AC13 | `test_squadboard_page.py` `Layout.test_T26_AC1_AC2_AC8_AC13_...`: 1440 at 3 text sizes, 1000 small/xl, 1920: count, 12 px gaps, no overlap, content height; `layout.js` `colCount`, `board.css` `#canvas`, `.col` |
| T26.AC3, AC4, AC6, AC11, AC14, AC15 | `Layout.test_T26_AC3_AC4_AC6_AC11_AC14_AC15_...`: drop spot, landing, column closes up, save (`col`, `order`, `auto` false), Esc, keyboard and edges, focus, hide/show, reload, Reset; `layout.js` `drag`, `key` |
| T26.AC5, AC12 | `Layout.test_T26_AC5_AC12_...`: height grows, width same, below moves down, other column same, Fit; `layout.js` `resize`, `caps` |
| T26.AC7 | `Layout.test_T26_AC7_TA5_TA12_...` with `tests/fixtures/board/layout-26/board-ui-iter1.json` (hand-written to the iteration-1 shape, see gaps) |
| T26.AC9, TA11 | `Layout.test_T26_AC9_TA11_...`: banner outside `#canvas`, no `.rz.e/.rz.se` |
| T26.AC10 | counts 2/2/3 in the AC1 test (1440, 1000, 1920); place of each panel: `PureRules.test_T26_TA3_...` (design-v7 s2 case); look is QA blackbox's |
| T26.TA1, TA13 | `PureRules.test_T26_TA1_TA13_...` (norm); pure, no DOM |
| T26.TA2 | `PureRules.test_T26_TA2_...` (8 cases) |
| T26.TA3 | `PureRules.test_T26_TA3_...` (n=1, 2, 3, tie; goal view with Scopes at n=2, 3: return fix) |
| T26.TA4 | the AC1 test (12 px, no stretch, no overlap) |
| T26.TA5, TA12 | the AC7 test (no PUT, `col: 9` kept in the snapshot, mixed rows) |
| T26.TA6 | page drag/key test (`put` carries `col`, `order`, `auto`); `test_squadboard_ui.py` `test_T26_TA6_...` |
| T26.TA7, TA8 | drag/key and resize tests above |
| T26.TA9 | see HANDIN: `pack`, `autoPlan`, grid code deleted from `layout.js`; remaining `span` hits are table/CSS/timeline words and the panel definitions' unused `span:` field (files outside this ticket) |
| design-v7 s2, s7 | `board.css` `.col`, `.col.over`, `.col .empty` (min 110 px), `.ghost`, `.panel.drag` |

## Tests changed
Removed (they pinned the 12-column grid): `PureRules` `T10_AC5_AC6_short_beside_tall...`, `T10_TA1_same_state...`, `T10_AC8_taller_content_scrolls...`, `T10_TA10_fewer_columns_at_1000`; `Layout` `T10_AC3_to_AC9...` and `T10_AC1_AC2_AC7_move_resize...` (replaced by the T26 tests above). None skipped.

## Open gaps
- The iteration-1 fixture is written by hand in the shape of the iteration-1 docstring, not copied from a live iteration-1 build.
- Panel definitions (`panel_*.js`, `timeline.js`) still carry `span:`/`spans:` fields; they are unused. Left alone: those files are not in this ticket's touched list (TC.10).
- No screenshots: the look is QA blackbox's (design-v7).
