Status: resolved
State: done (PASS qaw-board + qab-board at 7f659ba on squad/dev-board-13; not yet in the PO branch)
Task ID: BRD-31
Blocked by: 29 (same `TimelineBuilder`, same totals line)
Files touched: `bin/squad-board` (TimelineBuilder, derive_timeline), `bin/squad-board.html` (only if AC 0's page test finds drawBar wrong), `tests/test_board_timeline.py`, `tests/test_board_state.py`, `tests/test_board_page.py`

# BRD-31: bars end where the agent's last event is (closed bars carry an end row; unrecorded bars are cut at the burst end)

Two defects, one commit each (AC 0 first: the page shows it today).

## AC 0: every closed bar carries `end_row` (BRD-28 defect, found on the PO's live board)
`close_retired` (BRD-28) sets `end_us`/`end_ts` and leaves `end = None`, so `/state` has `open: false` with `end_row: null` (e.g. dev-board-2: `start_row 5`, `end_row null`, `end_ts 2026-10-11T17:51:44`). `drawBar` reads `end_row === null` as open and draws the bar to the bottom: the "retired agents' bars still continue" the PO sees. The cause is the code, not the data.
- `TimelineBuilder` keeps `last_row[agent]` = index of that agent's last row (updated wherever `add_row` is called for it: message rows for sender and receiver, status rows). `close_retired` and the new burst cut (rule 2 below) set `end = last_row[agent]` and the same row index on any open blocked/waiting segment they close (so a retired agent is not "blocked now"). `end_us`/`end_ts` stay as today (`last`).
- `end_row` is `null` in `/state` only for an **open** bar, or when the bar's end row is not visible in the selected iteration (the existing rule in `finish_bar`: then `end_ts` is set and the page must draw the bar to the bottom edge, unchanged).
- Tests: (a) `/state` test over the replay fixtures and a built log with a retired agent, a live agent, an unlisted agent and a late message to a retired agent: no bar with `open: false` and `end_row: null` when all rows are visible (no iteration selected); `start_row <= end_row` for every closed bar; each segment's rows lie within its bar's rows; (b) the same with an iteration selected: a closed bar whose end row is in the selected iteration has a non-null `end_row`; (c) **page test** (`tests/test_board_page.py`, Playwright, existing pattern): on a fixture with a retired agent's short bar followed by many more rows, the drawn bar's bottom edge sits at its end row (pixel check just below the end row is background, just above is bar colour), not at the bottom of the canvas. If `drawBar` is wrong for a closed bar with a non-null `end_row`, fix it there; otherwise the page needs no change.
- Lesson for BRD-21/17 (recorded as BRD-21 item 20): BRD-28 was checked on totals only; a shape invariant on `/state` (closed means an end row) would have caught it. Check the `/state` shape, not only the numbers.

## Rule: a bar that no status record backs ends at the agent's last message of the burst

**Done when no agent's `working_s` counts hours in which the squad log shows nothing but silence.** The PO sees `tech-board 50.1 h` on a bar of 43.1 h: a bar started by a message is closed only by the next `idle`/`done` record, and the recorder only runs while the board runs (`activity.jsonl` starts 2026-10-13T12:49 and has gaps), so that record can be days away.

## Cause (read from the code, `TimelineBuilder`)
- `message()` opens a bar for sender and receiver; only `status()` with `idle`/`done` closes it (`close_retired` only for non-live agents).
- A message-only history therefore keeps the bar open across every quiet night until the first status record after it. BRD-28 fixed this for non-live agents only.

## The rule (decision, tech-board; change what is wrong, not what a status means)
1. A bar is **recorded** if a status record of that agent falls inside it, or at most `WAKE_WINDOW_S` before its start (the hook's `working` stamp just before the waking message, D7). Set the flag in `status()` for every record of the agent while a bar is open (including a `working` that changes nothing), and in `start_bar` from a per-agent `last_status_us`.
2. A bar that is **not recorded** ends at the agent's last event (message sent or received) before a quiet stretch longer than `FOLD_GAP_S` (the existing constant, 180 s; no new constant). Do it as the replay goes:
   - in `message()`: before handling a message for an agent whose open bar is not recorded, if `us - last[agent] > FOLD_GAP_S * MICROS`, close that bar at `last[agent]` (same fields as `close_retired` after AC 0: `end_us`, `end_ts`, `end = last_row[agent]`), then the message opens a new bar as today (it counts as a wake if the agent received it, as today);
   - in `status()`: same check before the record is handled; the record then runs as today (an `idle` with no bar changes nothing; a `working` opens a bar if not woken);
   - at the end of `replay_records`: an open unrecorded bar whose last event is more than `FOLD_GAP_S` before `now` is closed at that event. This needs `now` passed in; keep the signature change small.
3. A **recorded** bar keeps today's rules exactly (idle/done ends it, blocked and waiting are segments, retired agents close at the last event).
4. Closing never invents time: `end_us >= start_us`; a one-message burst gives `duration_s = 0` (page must still draw something: check how BRD-28's zero-length retired bar is drawn and reuse it; if the page draws nothing, a minimum width belongs in `test_board_page.py`).
5. Consequences to accept, not fix: `wakes` rises (each burst opened by an incoming message is one wake, which is what it is); a long silent tool run with no recorder shows as idle time. Say so in the commit message, nothing else.

## Technical AC
1. **Timeline unit tests** (AC 0's tests come on top; each (i)-(viii) below also asserts `end_row` is the last event's row) (fixtures built in the test): (i) messages 10 s apart, then 1 h of silence, then a message: two bars, the first ends at its last message, `open: false`; (ii) the same with a gap of exactly `FOLD_GAP_S` (still one bar) and `FOLD_GAP_S + 1` (two); (iii) a bar with a `working` record inside keeps running through the same silence until its `idle`; (iv) the D7 case: `working` stamped 1 s before the first message, 20 min of silence, a second message: still one bar (recorded); (v) a message-started bar, 3 days of silence, then an `idle` record: the bar ends at the last message, the `idle` changes nothing; (vi) a live agent with an unrecorded bar last seen more than 180 s before `now` is closed at its last event, and within 180 s stays open; (vii) one-message bar has `duration_s = 0`; (viii) `working_s` of the agent equals the sum of its burst spans.
2. **Existing fixtures** (`tests/fixtures/board/*`, `squad-copy` style): where an existing assertion about a message-only bar changes, change only that assertion and name it in the commit message. A recorded bar must not change: the `waiting` and `blocked` fixtures stay as they are.
3. **Whole-squad check** (`evidence/BRD-31/squad-copy.md`): `cp -r` this squad folder to a temp dir (never write to the live one), run `bin/squad-board --replay <copy> --now <last record ts + 1 h> --port 0`, fetch `/state` with the token, and print one table: agent, `working_s` in hours, sum of its burst spans (messages within 180 s of each other, computed in the script from `messages.jsonl` for the unrecorded part), bar count. Required: every agent's `working_s` is at most the sum of its burst spans plus the span of its recorded bars, and none is above 12 h. If one is above 12 h because of recorded bars, show the records that justify it instead of loosening the rule. Before and after numbers for tech-board, qaw-board, qab-board, manager, dev-board-10, dev-board-11, qaw-board-2 (the PO's list: 50.1, 49.3, 41.4, 49.1, 33.1, 31.8, 42.6 h). Kill the server by PID and show none left.
4. **BRD-28 invariant** still holds: for every agent `working_s <= last record - first record`. BRD-29 invariant: `working_s + waiting_s` = bar duration for every bar.
5. **Page look** (qab-board, replay mode against the squad copy): bars are short bursts, not day-long stripes; header totals ⏱ read in plausible hours; one screenshot.
6. **Suite receipt (process.md Safety):** `python3 tests/run_suite.py --receipt evidence/BRD-31 --tz` if BRD-30 has passed by then, else the two receipt files by hand (full suite default under the flock lock, then the time-handling files under `TZ=America/New_York LC_ALL=C`; first line `sha <rev> clean=yes|no`, tail `Ran N tests ... OK`). Python 3.9-safe, no `.pyc` committed, touch only the listed files.

## Out of scope
- Rewriting any `activity.jsonl` or `messages.jsonl`.
- Making the recorder run without the board (it would fix the cause for new history; the PO has not asked).
- A per-agent "last seen" other than messages and status records (no transcript mtime, no pane reads).
- BRD-19's `home_log`/roster code: the rule is in `TimelineBuilder` only, so the BRD-29 merge into BRD-19 meets it only on `derive_timeline` (its two callers).

## Check on dev-board-30 showing idle with 0.00 h (done by tech-board, 2026-10-14)
Not a bug. The log has no message involving `dev-board-30` (it works in its worktree and reports through the Manager), and its only records until 20:56 were `idle` 20:47:30, `waiting` 20:47:35 (opened a bar), `idle` 20:49:24 (closed it): a bar of 109 s that was all waiting, so `working_s = 0`. A `working` record arrived at 20:56:34, after which it shows as working and its bar grows. A developer that sends no messages before its first hook stamp is invisible until then; nothing to change.

## Delivery
- dev-board-13, about 1.5 hours, two commits `BRD-31 (end rows): ...` and `BRD-31 (burst cut): ...` on `squad/dev-board-13`, started after the BRD-29 HANDIN so BRD-29 is not held up; dev-board-19 merges the tip once both pass. Reviewers: qaw-board (code, tests), qab-board (item 5).
- Tell tech-board if the page needs a change (AC 0's page test, zero-length bars); otherwise the ticket is timeline only.

## Comments
