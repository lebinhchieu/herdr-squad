Status: wontfix
State: deferred (backlog)
Task ID: BRD-20
Blocked by: 12 (branch from BRD-12's passed sha; runs parallel to 13..16, merged in BRD-17)
Files touched: `bin/squad-board.html` (header card drawing only), `tests/test_board_page.py`

# BRD-20: header totals stay readable at 12 and 13 columns

**Done when, at 1280 px with 12 columns on the page fixture, a card showing both `⏱` and `⛔` draws its totals at 9 px or larger, with no overlap and no clipping.** Found by qaw-board on BRD-12 (N1): the totals shrink to the 7 px floor (`dev-shop-3`), readable only zoomed. Not a BRD-12 return item: new behaviour waits for this ticket.

## Technical notes
- Card height stays as E20 (66 px) and the round 6 look stays. When `⏱` and `⛔` do not fit side by side at 9 px, put `⛔` on its own line under `⏱` (Developer chooses the exact spot; the layout must fit the 66 px card, else extend the header by the fewest px and shift rows start with it, never rows overlapping headers).
- The 7 px floor stays for the *other* header text only where it already applies; the totals never go below 9 px.
- Text mirror unchanged.

## Technical AC
1. Page test: a pure layout function (or the existing one) returns for 12 and 13 columns at 1280 px a totals font size ≥ 9 and non-overlapping rectangles for name, totals and tokens, with both totals present.
2. A card with only `⏱` is drawn as before (no empty second line). Mutant: always stack → that test fails.
3. Baseline page rules (no external URL, palette-only hex, CSP) still pass.

## Behaviour AC (blackbox)
B1. At 1280 with 12 columns, every header's totals are legible at 100 % zoom in a screenshot; no text overlaps a neighbour's.
B2. At 1920 the header looks as in BRD-12 (no stacking when it fits).

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
- 2026-10-13 tech-board: dropped from this goal by the PO (manager DECISION). Not built, not merged in BRD-17. Worktree `.worktrees/dev-board-20` stays unused.
