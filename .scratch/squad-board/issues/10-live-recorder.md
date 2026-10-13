Status: ready-for-agent
State: ready
Task ID: BRD-10
Blocked by: 09 (branch from BRD-09's passed sha; the demo fixture of 08 is not used)
Files touched: `bin/squad-board` (new `recorder` section; the live branch of `main`; the one `--replay`-required test in `tests/test_board_state.py` that live mode makes obsolete), `tests/fake_herdr.py` (new), `tests/test_board_recorder.py` (new)

# BRD-10: live mode skeleton and the herdr activity recorder

**Done when `squad-board` with no `--replay` serves the same `/state` from `$SQUAD_DIR` and, against a fake herdr socket, appends correct records to `activity.jsonl` for every status change of a rostered agent.**

Read first: design-iteration-2.md (E1 to E7), spec "Activity recorder" and Further Notes ("herdr events work, with three catches"), `herdr api schema --json`. Capture one real `session.snapshot` result and one real `pane.agent_status_changed` frame read-only (`herdr api snapshot`, and a short subscription on the socket), strip anything personal, and build `tests/fake_herdr.py` from those shapes.

## Build
- **Live branch of `main`** (E1, E7): no `--replay` → squad folder from the environment; `--now` with no `--replay` is an error (exit 2); everything else as in replay. The startup line is the same.
- **`recorder` section** with `start_recorder(squad_dir, socket_path)` running on a daemon thread: connect, snapshot (E2), subscribe once per agent pane plus `pane.created`, map pane to name through the snapshot, stamp the time, append records (E4, E5), re-snapshot on an unknown pane or `pane.created`, reconnect (E6).
- **`tests/fake_herdr.py`**: a Unix-socket server in a thread that speaks the framing above, lets a test add panes, emit status changes, drop the connection and stop. Tests build the snapshot answer from rows the test gives it.
- **Obsolete test:** the BRD-01 test asserting "`--replay` required" now means "live mode without `SQUAD_DIR` and without a squad folder exits 2 with a message". Edit only that test.

## Technical AC (BRD-10)
1. **Records:** each event → one line `{ts, agent, status, iteration}` with `ts` ending `.mmmZ` (3 digits). Seam A: start the real command with `HERDR_SOCKET_PATH` = fake socket and `SQUAD_DIR` = temp fixture; read `activity.jsonl`.
2. **One subscription per pane** plus `pane.created`: the fake records subscription requests; two agent panes → two status subscriptions (each with its `pane_id`), one `pane.created`.
3. **New agent:** after `pane.created` + snapshot shows a new rostered agent, its later status changes are recorded. An agent not in `roster.md` is never recorded (E3); the roster is re-read when an unknown name appears, at most once per second (test with a roster row added after start).
4. **Initial sync (E4):** at start, a rostered agent `working` in the snapshot with no prior record → one record; with a last record already `working` → none. Same after a reconnect.
5. **Iteration tag:** highest numbered iteration file at write time, null with none; adding `iterations/3.md` between two events changes the tag.
6. **Reconnect (E6):** fake drops the connection → records resume after it returns, and an event during the outage is not invented; herdr absent at start → server still answers `/state`, one stderr line per outage, no traceback.
7. **Robust:** malformed frame, unknown event type, event for an unknown pane id (resnapshot, then skipped if still unknown), a very long line (1 MB) → no crash, no record.
8. **`/state` in live mode:** `live` true, `now` is the wall clock (two requests 1 s apart differ), tokens/jump unchanged from replay.
9. **Append safety:** records written with `flock` and one write each; a concurrently running hook writer (messages.jsonl) is unaffected (different file); two recorders on one folder do not interleave partial lines (test with threads).
10. **Security:** the socket path comes from env or default, never from a request; no shell; the recorder never writes outside `$SQUAD_DIR`.
11. **Shutdown:** SIGTERM/SIGINT stops server and recorder thread promptly (under 2 s) with the fake connected.
12. **Baseline AC 1 to 5, 7, 9, 10** from design.md.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
