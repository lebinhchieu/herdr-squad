Status: resolved
State: done (PASS qaw-board + qab-board at 0d58139 on squad/dev-board-13; its tip carries everything: 927c5a7 merged as a184796)
Task ID: BRD-32
Blocked by: 31, 19 (same `TimelineBuilder.message`; the new route reads messages through BRD-19's `read_logs`)
Files touched: `bin/squad-board` (row clip in `TimelineBuilder.message`, new route `GET /message/<msg_id>`, handler dispatch), `bin/squad-board.html` (panel "show more" fetches), `tests/test_board_state.py`, `tests/test_board_http.py` (or a new `tests/test_board_message_route.py`), `tests/test_board_panel.py`

# BRD-32: the state payload sends message text clipped; the full text is fetched on demand

**Done when `/state` and every `/events` push carry at most 140 characters of text per message row, and the side panel's "show more" still shows the whole message, fetched when the user clicks it.** Totals, bars, rows, tasks and needs-you do not change.

## Measured (tech-board, 2026-10-14, this squad's `messages.jsonl`)
478 messages, 245 590 bytes of text. Clipped to 140 chars: 66 792 bytes (-179 KB); to 200: 93 607 bytes (-152 KB). Iteration 1 is 384 KB per push, so 140 gives about 205 KB (-47 %), 200 about 232 KB (-40 %). **Decision: 140**, the same as the panel's `PANEL_CLIP`, so the page shows exactly what it shows today until the user asks for more (the PO said "~200"; the 60 extra characters would never be drawn). Clipping alone does not reach 50 %: the other 200 KB are rows, bars, columns and keys; a diff push is a different ticket.

## Design
1. **Clip (server).** In `TimelineBuilder.message`, the row's `text` is cut to `ROW_TEXT_CLIP = 140` characters (Python `str`, so no half code point; no ellipsis added: the page already adds one) and the row gets `"text_clipped": true` **only when it was cut** (an uncut row has no new key). Everything server-side that reads message text (`derive_tasks`, `po_checkin_filled`, needs-you, the recorder) keeps reading the raw log: only the rows are clipped. A message without `msg_id` is never clipped (nothing to fetch it by). Needs-you item texts and task fields are not touched.
2. **Route (server).** `GET /message/<msg_id>?token=...`: plain text (`text/plain; charset=utf-8`) of that message's full text. Check order as `handle_notes`: token (403, same body as notes), then id (`^[0-9A-Za-z-]{8,64}$`, else 400), then lookup in the current `read_logs(...)` messages (404 `not found`); same Host and Origin checks as every other route (`check_request`), `Cache-Control: no-store`, never the token in the body, no directory access (the id is looked up, never joined into a path). Works in replay and live mode and in BRD-19's per-scope layout (it goes through `read_logs`, not a path).
3. **Page.** `panelMessage`: when `row.text_clipped` is true, "show more" fetches `/message/<msg_id>?token=<token>` once, keeps the result in a `Map` keyed by `msg_id`, and shows it; "show less" shows the clip again without a fetch. While loading the row shows the clip and a muted `loading…`; on a failed fetch the clip and a muted `full text not available`, and the button stays so a click retries. The card key (`renderPanelMessages`) includes whether the full text is loaded, so a state push neither wipes nor flickers an expanded message. A row that is not `text_clipped` behaves as today (no fetch). The page uses the token the way its other fetches do (notes), nothing new in storage or URLs.
4. **Tests that read row text** (`tests/*`): where an existing assertion compares a row's `text` with a long original, change only that assertion and name it in the commit message.

## Technical AC
1. **Clip tests** (built logs): (i) 139, 140, 141 characters: only 141 is cut and gets `text_clipped`; (ii) a 3-byte or astral character at the cut is not split; (iii) a message with no `msg_id` is never clipped; (iv) `/state` and one `/events` frame both carry the clipped text; (v) totals, bars, `tasks` and `needs_you` of a fixture are byte-identical before and after (compare the JSON with the `rows[*].text` and `text_clipped` keys removed).
2. **Route tests** (as `test_board_notes.py`): 403 without or with a wrong token and the body is the same for both; 400 for a bad id; 404 for an unknown id; 200 with the full text of a long message; the token never appears in any body; a foreign `Host` is refused; the route works against a per-scope layout fixture (BRD-19) and a flat one.
3. **Page test** (Playwright, replay): a long message in the panel shows the clip and `show more`; a click shows the whole text (assert the last 20 characters are on the page); `show less` returns to the clip; an `/events` push while expanded keeps it expanded and unflickering; a failing route (kill-switch via a bad token in the test) shows `full text not available` and the clip.
4. **Size evidence** (`evidence/BRD-32/size.md`): `cp -r` this squad folder to a temp dir, run `bin/squad-board --replay <copy> --port 0`, fetch `/state` for iteration 1 before and after the commit (same copy, `git stash`-free: build both from two checkouts or one flag-less run per commit) and print bytes and `rows` count in a table. Required: at least 35 % fewer bytes on this squad; if less, say why and stop, do not clip harder. Kill the server by its PID.
5. **Suite receipt (process.md Safety):** `python3 tests/run_suite.py --receipt evidence/BRD-32 --tz` once BRD-30 has passed; otherwise the two receipt files by hand. Python 3.9-safe, no `.pyc` committed, touch only the listed files.

## Out of scope
- Diff pushes (sending only changed rows), gzip on `/state`, a cap on the number of rows, dropping `rows` of old iterations: separate tickets if the PO still finds the page heavy.
- Clipping needs-you or task text.
- Any change to what a bar, total or status means.

## Cost, files and order (for the Manager)
- About 1.5 hours, one Developer, one commit `BRD-32: ...`. Reviewers: qaw-board (route security, tests), qab-board (panel behaviour, one screenshot of an expanded message).
- **dev-board-13** is the natural owner after BRD-31 (same `message()` function); if it is gone, any Developer starting from the branch tip that has BRD-19 merged.
- **Overlap:** BRD-31 (`TimelineBuilder.message`: the build order resolves it), BRD-19 (`read_logs`/`read_squad`, the route's lookup: branch from the merged tip, call `read_logs` as it stands there), BRD-29 (none after it passes). **BRD-22-25 do not touch these files** (new `bin/squad-board-start`, plugin files, README), so no conflict and no order between them.

## Comments
