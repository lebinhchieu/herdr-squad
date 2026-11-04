## Behaviour
Every panel has an east-edge handle `.rz.e` (a focusable separator). A drag shows a dashed outline, a pill `k of G columns` and guides; nothing moves until release. On release one save writes `tracks` (twelfths, 1..12) and `place` runs once. Esc cancels, double-click removes `tracks`, Left/Right change the span by one. `PUT /api/ui` keeps `tracks` 1..12 and drops `col`, `span`, `auto`. Code sha: 31ec56a. Tests: test_squadboard_grid, test_squadboard_ui, test_squadboard_page 61 OK.

What I saw (headless Chrome, real server, fixture, Agents panel handle; shots at 1000/1440/1920):
- Hover: a thin vertical line on the panel's east edge (at 1920 the Agents handle is at the window edge, so the line is faint).
- Focus: a dark frame the full panel height and 12 px wide on the east edge. Clear, but heavy.
- Drag: dashed outline over the panel, dark pill `2 of 4 columns` at its top right, vertical guides over the page; other panels stay put.
- I found no CSS fault small enough to fix and none that blocks use. Open for the Designer: the focus frame is heavier than the hover line.

![hover 1000](img/hover-1000.png)
![hover 1440](img/hover-1440.png)
![hover 1920](img/hover-1920.png)
![focus 1000](img/focus-1000.png)
![focus 1440](img/focus-1440.png)
![focus 1920](img/focus-1920.png)
![drag 1000](img/drag-1000.png)
![drag 1440](img/drag-1440.png)
![drag 1920](img/drag-1920.png)

## AC table
Technical AC (SQ-6): tests/test_squadboard_grid.py, class Resize, unless named.

| AC | Test | Result |
|---|---|---|
| T36.TA1 `snapTracks` | `Resize::test_T36_TA1_pure_functions` (o.snap) | pass |
| T36.TA1 `widthToTracks` | `Resize::test_T36_TA1_pure_functions` (o.w2t, round trip) | pass |
| T36.TA1 `tracksToWidth` | `Resize::test_T36_TA1_pure_functions` (o.t2w, round trip) | pass |
| T36.TA2 drag saves `tracks` only, reload draws it | `Resize::test_T36_TA2_drag_saves_tracks_only_and_reload_draws_it` | pass |
| T36.TA3 narrow window keeps the saved share | `Resize::test_T36_TA3_narrow_window_keeps_the_saved_share` | pass |
| T36.TA4 server bounds, old keys, bad saved values | tests/test_squadboard_ui.py::test_T36_TA4_tracks_bounds_and_old_keys; page reader: `Grid::test_T35_bad_tracks_values_fall_back_and_files_at_six_twelfths` | pass |
| T36.TA5 Esc, double-click, keyboard | `Resize::test_T36_TA5_esc_dblclick_and_keyboard` | pass |
| T36.TA6 `place` once on pointerup, none while dragging | `Resize::test_T36_TA6_place_runs_once_on_pointerup_and_panels_do_not_move_while_dragging` | pass |
| T36.TA7 handle attributes | `Resize::test_T36_TA7_handle_is_a_focusable_separator_and_the_banner_has_none` | pass |

Business AC (QA blackbox owns the live check):

| AC | Shown by |
|---|---|
| T36.AC1 handle exists | TA7 test; shots hover-*/focus-* |
| T36.AC2a, AC2b span and snap | TA1, TA2 tests |
| T36.AC3 limits | TA1 test (minSpan, beyond G) |
| T36.AC4 live outline, pill, no move | TA6 test; shots drag-1000/1440/1920 |
| T36.AC5 Esc | TA5 test |
| T36.AC6 neighbours re-place | TA6 test; T35 TA2 geometry |
| T36.AC7 saved | TA2 test |
| T36.AC8 window narrower and wider | TA3 test (fixture files6) |
| T36.AC9 bad saved values | `Grid::test_T35_bad_tracks_...` (fixtures bad-tracks, files6) |
| T36.AC10 keyboard | TA5 test |
| T36.AC11 Reset, hide, show | `Grid::test_T35_AC9_...` (tracks back to default) |
| T36.AC12 height independent | `Grid::test_T35_AC7_...` (width and side stay) plus TA2 (no max_height in the PUT) |
| T36.AC13 nothing cut off | open gap: no test; QA blackbox. Shot at 1000: Tasks table scrolls inside its panel (known, from before 35) |
| T36.AC14 matches design-v8 | shots; QA blackbox |

## Edits to old `.col` pins
Same as ticket 35 (one branch, one diff vs 181b048); see ../35-smart-grid.evidence/evidence.md. The edit that belongs to 36: the banner test in test_squadboard_page.py looks for a handle only in `.bannerslot` (before it looked for any `.rz.e`, which now exists on panels), and test_squadboard_ui.py: `test_T36_TA4_tracks_bounds_and_old_keys`.

## Fixtures check
See ticket 35's table. For 36: board-ui-files6.json is used by `Resize::test_T36_TA3_...`; board-ui-bad-tracks.json by `Grid::test_T35_bad_tracks_values_fall_back_and_files_at_six_twelfths` (T36.AC9).
