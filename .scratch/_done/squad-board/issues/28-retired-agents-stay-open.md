Status: resolved
State: done (PASS at e77b69d; in squad/dev-board-19 at 927c5a7)
Task ID: BRD-28
Blocked by: 17 (and 27 only through 17's branch)
Files touched: `bin/squad-board` (reader, `TimelineBuilder`/`derive_timeline`, `build_columns`, `Recorder`), `tests/test_board_timeline.py`, `tests/test_board_recorder.py`, `tests/test_board_state.py` (columns); fixtures only if one of them breaks (see AC 2)

# BRD-28: a retired agent's bar ends at its last event, a closed pane records `done`, no phantom columns

**Done when, on a copy of this squad folder, no agent whose roster status is not `live` has `working_s` above the span between its first and last record, and `dev-board-1` shows about its real work time instead of ~48 h.** Found by the PO on the live board (17a build): `dev-board-1` has one open bar since 2026-10-11T17:51 (duration 176060 s, `self_start`), because nothing ever closed it: herdr emits no idle when a pane closes, so a retired agent stays "working" until `now`.

## The four parts (Manager's ask, decisions from tech-board)

### (a) Timeline: a bar of a non-live agent ends at its last event
- In `TimelineBuilder`, remember for every agent the time (µs and `ts`) of its **last event**: any message it sent or received (a `from` or `to`), or any status record. An agent's bar still open at the end of the replay, and **not live**, is closed there: `end_us = last event`, `end_ts` = its ts, `open: false`, `duration_s` = last event − start. An open blocked segment closes at the same time. A closed bar draws as closed on the page already (`end_row` may be null with `end_ts` set, see `finish_bar`).
- **Not live** = the agent is not a roster row with a live status (rule (d)), which also covers an agent that is only seen in logs (never rostered, "never seen live"). A live agent keeps today's behaviour (open until `now`).
- `derive_timeline` needs the set of live agents: pass it in (`columns` already carries `retired`; add the unlisted case, `live_agents = {c["agent"] for c in columns if not c["retired"] and c["rostered"]}` or a plain set built in `build_state`: tech choice, keep it one parameter).
- Both replay and live go through `derive_timeline`, so one change covers both. Totals (`working_s`, `blocked_s`, `wakes`) follow from the shorter bars.
- A later event for a non-live agent (a late message to a retired agent) just moves its last event; the bar still ends at the last event. The agent does not become live because of it.

### (b) Recorder: a closed pane records `done`
- When a **rostered** agent's pane goes away, append `{"agent": name, "status": "done"}` (same record shape and writer as `append`), once. Cases: (1) at the E4 sync, a rostered agent whose last log status is not `done` and which is **missing from the snapshot** and has at least one record; (2) while running, a pane that was in `self.names` and disappears from a later snapshot.
- **Check against the real socket first, read-only** (`session.snapshot`, and whether `events.subscribe` accepts a `pane.closed` subscription; the herdr binary contains the string `pane.closed`). If `pane.closed` is subscribable, handle it (sync on receipt: the snapshot is the truth, the event is only the trigger). If not, resync on a timer (`RESYNC_S = 30`) in the same loop that waits for frames. Put what you found in `evidence/BRD-28/herdr-socket.md` (the exact request and reply shapes, nothing destructive: do not close, spawn or move any pane).
- **Safety:** write `done` only after a snapshot that *succeeded* and contained at least one agent pane (an empty or failed snapshot must not mark the whole squad done). A `working` record for the same name later reopens a bar as today (status `working` with no open bar starts one).
- Never write for an agent that is not rostered (E3). `done` is already a recorded status (`RECORDED_STATUSES`), so no schema change.

### (c) Phantom columns `uds:/run/user/1000/cc-socks/<n>.sock`
- **Cause (checked in `messages.jsonl`, 8 records):** these are the `to` of replies sent to a cross-session address (an `ANSWER` or `STATUS` back to a peer session that is not a squad name), not a sender-less `from`. `squad-log-message` records `to` as sent. There is no reliable way to map a socket to a roster name (the socket belongs to a session id, and the roster stores one only for some agents), so **do not map: drop**.
- Decision: a name that does not look like an agent name is not an agent. Add one helper `is_agent_name(name)` (`re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name)`; `uds:` fails on the colon and slashes) and use it in the two places that create agents from log names: the `sightings` loop in `build_columns` (no column) and `TimelineBuilder.message` (no bar start, no last-event entry for it). The message **row stays** in the list and mirror (it was sent; the page draws no arrow when a column is missing, as today), and the sender's own bar and last event still count.
- The log is not rewritten and the hook is not changed.

### (d) The roster status cell
- `build_columns` has `r["status"].lower() != "live"`; the cell can be `live (respawned 2026-10-14 ...)`. Retired = `not r["status"].strip().lower().startswith("live")`. One line, one test (`live`, `Live`, `live (respawned)` are live; `retired 2026-10-12 (...)`, `gone ...`, empty are not). Use the same test wherever the live set is built for (a).

## Technical AC
1. **Timeline unit tests** (fixtures built in the test, no new fixture files): (i) a retired agent with a `working` record and no later event: bar closed at that record, `duration_s = 0`; (ii) a retired agent with messages after its `working` record: bar ends at the last message, `open: false`, `working_s` = last − start; (iii) a live agent with the same records stays open until `now`; (iv) an unlisted agent (only in the log) is closed at its last event; (v) an open blocked segment of a retired agent closes at the same instant; (vi) a late message to a retired agent extends the bar to that message and does not reopen it.
2. **Existing fixtures:** the replay fixture `tests/fixtures/board/page` and the others may hold retired agents with open bars; where an existing assertion about such a bar changes, change only that assertion and say which in the commit message. A live agent's bars must not change.
3. **Recorder tests** (the fake herdr socket pattern in `tests/test_board_recorder.py`): (i) sync with a rostered agent missing from the snapshot and last status `working`: one `done` appended; with last status `done` or no record: nothing; (ii) a pane that disappears from a later snapshot: one `done`, and a second sync adds none; (iii) an empty snapshot writes nothing; (iv) a name not on the roster is never written; (v) the trigger you found (`pane.closed` event or the timer) causes the resync.
4. **Phantom column test:** a log with a `to` of `uds:/run/user/1000/cc-socks/1.sock` gives no column and no bar for it; the sender's column and bar are unchanged; the row is present.
5. **Roster cell test** as in (d).
6. **Whole-squad check (evidence, `evidence/BRD-28/squad-copy.md`):** copy this squad folder to a temp dir (`cp -r`, never point the test at the live folder for writes), run `bin/squad-board --replay <copy> --now <last record ts + 1 h> --port 0`, fetch `/state` with the token, and show: for every agent with a non-live roster status, `working_s <= last record - first record` for that agent (a short script that prints the table), and `dev-board-1`'s `working_s`. Kill the server by its PID and show none left.
7. **Suite receipt (process.md Safety):** run the full suite once under the flock lock (default) and save `evidence/BRD-28/suite-default.txt`; then run the time-handling test files (timeline, state, tokens, recorder, plus any test file the ticket touches) once under `TZ=America/New_York LC_ALL=C` and save `evidence/BRD-28/suite-tz.txt`. Each file has the first line `sha <rev> clean=yes|no` and the tail `Ran N tests ... OK`. QA whitebox checks the receipt and runs only targeted tests. Python 3.9-safe, no `.pyc` committed, touch only the listed files.

## Out of scope
- Live recorder against a real herdr is not exercised in the suite; the `herdr-socket.md` note and one manual read-only snapshot are the check.
- Bars of live agents that really stopped without an idle (a crashed but open pane) stay open: only a closed pane is recorded.
- Rewriting existing `activity.jsonl` lines: the squad's history needs no repair (rule (a) fixes the display of old data without it).

## Delivery
- One Developer, about 1.5 hours. One commit `BRD-28: ...` on a branch from BRD-17's passed sha. Reviewers: qaw-board (code, tests), qab-board (the page shows `dev-board-1` and the other retired agents with short bars; one screenshot of the live board against the squad copy).
- Order: build this **before BRD-19** (the layout adapter rewrites `build_state`, `StateWatcher` and the roster reader; BRD-19 branches from BRD-28's passed sha). BRD-22, 23, 24 are independent.

## Comments
- 2026-10-14 tech-board: written on the Manager's ask (PO found the 48 h totals on the live board). Part (c) differs from the report: the phantom is a recipient, not a sender. Not mapped; dropped.
