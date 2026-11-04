# Evidence 25: Panels dropdown opens under its button

## Behaviour
The Panels list and the Columns list now sit in a `position:relative` wrapper (`.popwrap`) with their button. The list is `position:absolute; top:calc(100% + 4px)`, so it scrolls with the button. `BOARD.popPlace` (pure) shifts it left to keep 8 px from the right edge and sets max height = window height - button bottom - 12. It never flips above. The Panels list has the title "Hidden panels", the caret is ▴ while open, and every close path returns focus to the button. The open Columns panel gets `z-index:40` so no later panel covers its list.

## AC table
| Id | Shown by |
|---|---|
| T25.AC1, AC2, AC3 | `tests/test_squadboard_panels.py` `Popover25.test_T25_AC1_AC2_AC3_TA1_...` (3 font sizes, scroll 300 px; gap, inside window); `board.js` `popPlace`, `placePop`; `board.css` `.popwrap`, `.pop` |
| T25.AC4 | same test: Esc closes, focus on button; `togglePop` focus on close; caret in `renderPop` |
| T25.AC5 | `test_T25_AC5_columns_popover_...` (Extra large, on top, footer, scroll); `placeColumns` |
| T25.AC6 | existing tests in `test_squadboard_page.py` (show hidden panel) pass unchanged |
| T25.TA1 | pure cases in the Popover25 test (shift, tiny viewport) |
| T25.TA5 | listeners added on open, removed on close (`togglePop`) |
| T25.TA6 | no `position:fixed` in `.pop`/`.cpop`; no hex outside `:root` |
| design-v7 s3 | caret ▴, title HIDDEN PANELS, 4 px, 12 px, no flip |

## Open gaps
- Not tested: 1000 px window width (the headless window is 1440), the 600 px scroll (300 px used), and the max-height scroll with a very tall list.
- The Columns list does not re-measure max height on scroll (it follows the button by layout).

## Tests
Run: test_squadboard_panels (48 ok), test_squadboard_page, test_squadboard_timeline, test_squadboard_worktime (ok). Edited tests: none; added `Popover25` class and one Columns test. Grep `board.css|togglePop|\.pop` hits other than these are `list.pop()` uses in unrelated files.
