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

## Return 1 (QA whitebox findings)
1. Removed the 120 px floor in `placeColumns` (max height is now window - button bottom - 12). 3. `applyFont` re-places both lists at once and again after 250 ms (panels animate). 2, 4, 5, 6, 7: tests rewritten/extended: `Popover25` (Panels list: 1440x900 and 1000x800, 3 text sizes, scroll 600, open while scrolled, text size while open, Esc/outside close + focus + caret, resize while closed, `popPlace` fits/right/low/tiny) and `Panels20.test_T25_AC2_AC3_AC5_TA2_TA3_TA7...` (Tasks Columns list: same matrix; inside window, footer visible, on top at its bottom, so not cut by the panel). `run_page` and `Panels20.page` got an optional `size` argument.

## Open gaps
- When the button has less room below it than the list's fixed parts need (about 100 px: title, hint, footer), the list still passes the window bottom. Tests use 1000x800.
- At Extra large in a 700 px window the Columns button itself is below the window; the test then checks only the gap.
- A click on a text-size button closes the list (outside click), as QA blackbox noted; the text-size hook is tested by calling `setFont`.

## Tests
Run: test_squadboard_panels (48 ok). Edited existing tests: `test_T25_AC5_columns...` and `test_T25_AC1_...` (both mine, from the first hand-in, renamed and widened).
