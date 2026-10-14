# squad-board: status for the PO (2026-10-14, tech-board)

**Merge `squad/dev-board-19` at `927c5a7`.** It holds everything that has passed so far; nothing else is waiting to be merged yet.

## What the branch carries

| Tickets | What you get | Passed by |
|---|---|---|
| 01-09 | Server core, replay mode, state, bars, tasks, tokens, hardening, SSE, demo fixture | qaw-board |
| 10-18 (+17a) | Live recorder and sources, the canvas page (sequence, follow, picker, panel, jump, alerts) | qaw-board + qab-board |
| 27, 28 | Page idles at ~5 % of a core (was 37 %); retired agents' bars close | qaw-board (28 also checked by me, no qab replay) |
| 29 | `waiting` state for an agent whose monitor or shell runs in the background (amber dot, hatched bar segment, panel line) | qaw-board + qab-board |
| 30 | `tests/run_suite.py`: parallel full suite with a receipt | qaw-board |
| 19 | Layout adapter: flat and per-scope squads | qaw-board (no qab: the page shows nothing new) |
| 22-25 | `squad-board` launcher, `squad-start` opens the board, `/squad:squad-board` skill, `squad-init` gitignore and README | qaw-board |

Receipt on the merged tree: 1010 tests OK (`evidence/BRD-19/suite-default.txt`).

## Not in the branch

| Ticket | State |
|---|---|
| 31 message-only bars, 32 state payload diet | PASSed (qaw-board + qab-board): 31 at `7f659ba`, 32 at `0d58139`, both on `squad/dev-board-13`; 31 ends the day-long stripes, 32 clips row text to 140 chars with a token-checked `/message/<id>` for the full text |
| 26 many columns, 21 test hardening (items 1-26) | backlog until you say yes |
| 20 header totals | dropped (your decision) |

## Your two paths

1. **Recommended: one merge of `squad/dev-board-13` at `0d58139`.** It already contains `927c5a7` (merged as `a184796`), so it carries everything: 19, 22-25, 29, 30, 31 and 32.
2. **Or in two steps:** `squad/dev-board-19` at `927c5a7`, then `squad/dev-board-13` at `0d58139`; the result is the same tree.

## Known limits

- One board per herdr workspace (BRD-22; README says so).
- `waiting` only detects a monitor or a shell in the pane's status line. `← N agent` is in every pane, so it counts for nothing.
- Message-only bars are cut after 180 s of silence (BRD-31): a long silent tool run with no recorder shows as idle time, and `wakes` rises (one per burst).
- While the recorder is down the log is silent, so a bar between two recorder starts can read hours long (BRD-21 item 24).
- Test flake: `test_board_sequence` (and other pixel tests) fail now and then under load and pass alone. The final tip's default receipt shows 2 of 55 failing in that file; the full suite was green at `b958b11` (1041 OK) and the time-zone run is green (269). Fix is BRD-21 items 19 and 26.
- Cosmetic: waiting labels can cross a neighbour's pill (BRD-21 item 23).
- Merges and pushes stay with you.
