Status: ready-for-agent
State: done
Task ID: BRD-02
Blocked by: 01
Files touched: `bin/squad-board` (only the `timeline` section and its one call in `build_state`), `tests/test_board_timeline.py` (new)

# BRD-02: rows, folded gaps, activation bars, durations, totals

**Done when `/state` returns `rows` and `bars` per design.md "Timeline rules" and each column's `working_s`, `blocked_s` and `wakes` are correct, all through fixture tests.**

Read first: design.md "Timeline rules", "Iteration filter", "State JSON"; spec "Derivation rules" and its prototype block. Replace the body of `derive_timeline` only; do not edit other sections.

## Technical AC (BRD-02)

1. **Row order:** messages and status events interleave by `ts`; tie → message before status. `rows[].id` is 0-based after folding.
2. **Bar from a message:** receiver idle → bar starts at the message row, `self_start` false; sender with no open bar → bar starts there too, `self_start` true. A bar already open is not restarted.
3. **Self-start:** a `working` event with no message → bar with `self_start` true and a `status` row.
4. **Wake window (D7):** `working` for B 1 s before a message to B → bar starts at the message row, `self_start` false, no separate status row. 3 s before → self-start. Both orders tested (event before and after the message).
5. **Blocked:** `blocked` event → blocked segment on the bar (bar auto-started if none); next `working` closes the segment; a `working` with no open segment and an open bar emits no row.
6. **End:** `idle` and `done` both close the bar; the closing `status` row carries `duration_s`; an `idle` with no open bar emits no row. An open bar: `open` true, `end_*` null, `duration_s` runs to `now`.
7. **Totals:** `working_s` includes blocked time; `blocked_s` is the sum of segments; `wakes` counts `self_start` false bars. Test with two bars and one blocked segment, exact numbers.
8. **Fold (D5):** a gap of 180 s makes no gap row, 181 s makes one; the gap row has `seconds`, `from_ts`, `to_ts`; none before the first or after the last row.
9. **Iteration filter (D11):** a fixture with iterations 1 and 2: `?iteration=1` shows only iteration 1 rows and bars; totals do not change between the two queries; a bar that opens in iteration 1 and closes in iteration 2 is listed under 1 with `open` false. A record with `iteration: null` counts as the lowest iteration.
10. **Unknown agent** in the logs gets rows and a bar (its column comes from BRD-01).
11. **Baseline AC 1 to 5, 7, 9, 10** from design.md "Technical AC".

### QA whitebox additions (qaw-board)
Q1. **Diff scope:** changes to `bin/squad-board` are inside the `timeline` section (plus the single call). Any line outside it is a FAIL unless tech-board agreed. If BRD-01's `build_state` already merges `working_s/blocked_s/wakes`, BRD-02 must not touch the merge.
Q2. **Dangling row refs under the iteration filter:** a bar that starts in iteration 1 and closes in iteration 2, viewed with `?iteration=1`, has `end_row` pointing at a row that is not in `rows`. State the rule (proposal: `end_row` null, `end_ts` real, `open` false) and test it. Same for blocked segments crossing the boundary and for a message row whose receiver bar starts in the other iteration.
Q3. **Fold vs filter order:** gap rows are computed over the rows visible after filtering, never across the iteration boundary; test with a long gap between the last iteration-1 row and the first iteration-2 row (shown in neither view, or in one: state which).
Q4. **Exact boundary numbers:** durations asserted as exact integers (rounding rule stated: floor or round), with fractional-second timestamps (`.999Z`).
Q5. **Open bar at `now`:** `now` earlier than a bar's start (clock skew) → `duration_s` 0, never negative. A closing event with `ts` before the start → duration 0, no crash.
Q6. **Idle/done for an agent that never worked, `unknown` status, and a status from an agent with no open bar** produce no row and no bar.
Q7. **Performance guard:** 5,000 messages + 5,000 status events in a temp fixture return `/state` in under 5 s (no quadratic scan).

## Comments
- 2026-10-12 tech-board: PASS by qaw-board at 1b61398 (squad/dev-board-3). A repeated `blocked` event inside an open blocked segment adds no row and no new segment (accepted, written in design.md).
