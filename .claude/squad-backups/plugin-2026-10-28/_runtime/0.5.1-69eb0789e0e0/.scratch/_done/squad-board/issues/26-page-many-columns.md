Status: ready-for-agent
State: droppable, after 17 (built with or after BRD-21)
Task ID: BRD-26
Blocked by: 17 (branch from BRD-17's passed sha)
Files touched: `bin/squad-board.html` (column layout and TASKS card position only), `tests/test_board_page.py`

# BRD-26: 13 or more full columns scroll sideways, TASKS never covers a column, controls stay aligned

**Done when, at 1280 px, a fixture with 13 non-collapsed columns scrolls horizontally and the TASKS card sits beside the last column, not on top of it.** Found by qab-board on BRD-16 (2026-10-13): on a fixture copy where retired `dev-shop-0` still gets messages (so its column is not a 24 px stub), `scrollWidth` is 1338 and the TASKS card covers the last column. The pristine fixture (stub) fits and does not overflow.

## Technical notes
- E20 allows the scroll above 12 columns (minimum column 84 px: 13 × 84 + 230 = 1322 + margins). The scroll is by design; the covered column is the defect.
- Cause to check first: the TASKS card is positioned against the viewport width, not the scroll width. Make the scroll area include the card's 230 px, or position it relative to the columns' right edge. Do not change `ROW_H`, header sizes or E20 numbers.
- The real squad often has 13+ rostered agents. Most are retired stubs; the case matters when several retired agents still get messages.

## Technical AC
1. Fixture copy with `dev-shop-0` still addressed: at 1280 px no element of `#columns li` is overlapped by the TASKS card (compare bounding boxes of the last column and the card: no intersection), and `document.documentElement.scrollWidth` ≥ the right edge of the card.
2. Pristine fixture at 1280 px: no horizontal scroll, as before.
3. **Canvas height with a horizontal scrollbar (qaw-board, BRD-14 PASS):** the BRD-12 relayout reads `window.innerHeight`, which includes the scrollbar. With a horizontal scrollbar the canvas shifts about 15 px and BRD-14's fixed `#bar-controls` sit off the needs-you bar. Use `document.documentElement.clientHeight`. Check: in the 13-column fixture of AC 1, the controls' vertical centre is within 2 px of the needs-you bar's centre.
4. Whole suite green; Python 3.9-safe; touch only the listed files.

## Comments
