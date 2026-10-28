Status: resolved
State: done
Task ID: BRD-06
Blocked by: 05 (stacked: branch from BRD-05's passed sha, so `check_request` and the http section are real)
Files touched: `bin/squad-board` (only `handle_events` and a small change-watcher in the `http` section), `tests/test_board_events.py` (new)

# BRD-06: server-sent events stream of state updates

**Done when `GET /events` sends the current state on connect and a fresh state whenever the squad folder's files change, and does not send when nothing changed.**

Read first: design.md "HTTP and security", spec "HTTP contract" (event stream). Replace the stub `handle_events` only. Live herdr and token-refresh triggers come in iteration 2; here the trigger is file changes.

## Technical AC (BRD-06)

1. **On connect:** `Content-Type: text/event-stream`, then one `event: state` with `data:` equal to the `/state` JSON (parsed equal to a `GET /state` of the same moment).
2. **On change:** appending to `messages.jsonl` or `activity.jsonl`, or editing `escalations.md`, `roster.md`, `scopes.md` or an iteration file, makes a new `state` event arrive within 5 s (poll every 0.5 s, constant `POLL_S`). The new event reflects the change (e.g. a new row).
3. **No change, no event:** with the files untouched, no second `state` event within 3 s. `now` is ignored when deciding whether state changed.
4. **`?iteration=N`** is honoured; a bad value → 400 before any stream starts.
5. **Keepalive:** a comment line `: keepalive` every 15 s (constant), so proxies and browsers don't drop the connection.
6. **Disconnect:** a client that closes the connection frees its thread; no traceback on stderr (test: connect, read one event, close, then `GET /state` still works and stderr is empty).
7. **Host check:** BRD-05 owns it and tests it on `/events` too. Here, route through the real `check_request`; add no Host test of your own.
8. **Many clients:** 3 simultaneous streams each receive the change event.
9. **No sleeps for correctness:** tests read the stream with a deadline.
10. **Handler socket timeout (from BRD-05 N3):** a client that connects and sends nothing does not hold a thread forever. Set a read timeout on the handler for request lines (it must not cut a healthy stream: an SSE connection only writes). State the value as a constant and test it with a short override or a small value.
11. **Baseline AC 1 to 5, 7, 9, 10** from design.md "Technical AC".

### QA whitebox additions (qaw-board)
Q1. **Keepalive testability:** a 15 s wait in a test is acceptable once; otherwise constants may be overridden by environment variables read at startup (`SQUAD_BOARD_POLL_S`, `SQUAD_BOARD_KEEPALIVE_S`), documented in the file. Either way the test asserts the keepalive line really arrives, not just that the constant exists.
Q2. **Change detection cost:** per poll the server does not rebuild the state for every client. Proposal: one shared watcher thread computing a `(size, mtime_ns)` signature of the watched files, building state only when it changes, and fanning out. QA reads the code; N clients must not mean N rebuilds every 0.5 s.
Q3. **Atomic replace and new files:** an editor that rewrites `escalations.md` via rename, a file that appears later (`messages.jsonl` created after start) and a file that disappears all trigger or tolerate correctly; no crash in the watcher thread (an exception in it is caught and logged, the loop continues).
Q4. **SSE framing:** `data:` is one line (JSON has no raw newline); `event: state` and a blank line end each event; `Content-Type: text/event-stream; charset=utf-8`, `Cache-Control: no-store`, no `Content-Length`.
Q5. **Thread leak:** after 20 connect/disconnect cycles the server's thread count does not grow (observable by the server answering `/state` promptly and exiting on SIGTERM within 2 s). SIGTERM/SIGINT shut the process down with exit 0 or the signal's code, even with open streams.
Q6. **Slow client:** a client that stops reading does not block other clients' events (writes have a timeout or the thread is per client and isolated).
Q7. **Iteration changes with a stream open:** the stream's `?iteration=N` stays fixed for that connection; the event after a change uses the same N.

## Comments
- 2026-10-12 tech-board: round 1 FAIL (qaw-board-2, 9e38eb6: keepalive spacing and `version = current` after a failed rebuild, tests only). Rulings: N1 and N2 go to BRD-11 (AC 9, 10). N3 accepted (local only). N4 adopted: the three env knobs are validated at start (finite number > 0, else exit 2 with `squad-board: SQUAD_BOARD_POLL_S must be a number greater than 0`), with a test each. The watcher's `except Exception` stays (BRD-06 Q3 requires a watcher that survives faults); fault-injection check by QA accepted.
- 2026-10-12 tech-board: dev-board-7 builds on 9d30599, where `derive_needs_you` is still a stub, so the escalations.md event test cannot show a changed state. Decision: watch `escalations.md` anyway, test the other watched files here, the escalations event test moves to BRD-09 (AC 13b). `query_iteration(handler)` extraction in `handle_state` approved; the third env knob `SQUAD_BOARD_REQUEST_TIMEOUT_S` (default 10 s) approved, documented where the other two are.
- 2026-10-12 tech-board: PASS by qaw-board-2 at d057b06 (squad/dev-board-7), round 3. Round 1 FAIL 9e38eb6, round 2 PASS 1c74e47, round 3 closed N5 (env knobs capped at 86400).
