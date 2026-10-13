Status: ready-for-agent
State: ready
Task ID: BRD-12
Blocked by: 09 (branch from BRD-09's passed sha; the demo fixture of 08 is not used)
Files touched: `bin/squad-board.html` (new), `bin/squad-board` (`handle_root`, the E10 headers, the `live` key in `build_state` only), `tests/fixtures/board/page/**` (new fixture), `tests/test_board_page.py` (new), `tests/test_board_state.py` only the top-level key-list assertion (adds `live`), approved 2026-10-12

# BRD-12: page skeleton: file, server wiring, palette, headers, needs-you bar, text mirror, page fixture

**Done when `GET /` serves the real page file, the page loads `/state` and draws the pod band, column headers and the needs-you bar in the Mango Parrot light palette, the text mirror exists, and every later page ticket has its section and stubs to fill.**

Read first: design-iteration-2.md (all, especially E26 "The look"), spec "Page behaviour", user stories 1 to 17 and 69, 70, and open `~/workspace/chat/squad-board-round6.html` in a browser: **it is the confirmed look**; match its needs-you card, pod bands and header cards (copy the look, not the code). `design.md` for the state keys.

## Build
- **`bin/squad-board.html`** with the sections of E25, each behind a marker, stubs with final signatures. Contains: state fetch + `EventSource('/events?iteration=N')` with reconnect (1 s, 2 s, … cap 15 s, "reconnecting…" in the bar), the viewport-sized sticky canvas and scroll spacer (E15), the draw loop (E16), layout of E20, pod band, headers, needs-you bar, and the mirror (E17) for what this ticket draws.
- **Server:** `handle_root` serves the file (E9) with `Content-Type: text/html; charset=utf-8` and E10 headers; missing file → 500 JSON. `build_state` gains `live` (E11); nothing else in `build_state`.
- **Page fixture `tests/fixtures/board/page/`** (fake names/data, committed, small): 12 agents in 3 pods (Manager's pod plus two), one retired agent with no events, one blocked agent, the Manager idle with an empty PO check-in, one unanswered escalation, a task at 2 returns whose FAILs are fanned out to three recipients each (so the page must show 2, not 6), a PASSed task followed by `STATUS … PASS from …` and `DECISION … PASS by …` messages (it must stay done), 3 iterations, about 300 rows including gaps over 180 s, an open bar, a self-start bar, a message whose text is `<img src=x onerror=alert(1)>`, one agent with null tokens. Replay is started with a fixed `--now`, stored as one ISO line in `tests/fixtures/board/page/now.txt` (UTC, `…Z`, later than every record in the fixture, so open bars have positive durations). Blackbox QA and the Developer's evidence read this file instead of guessing.

## Technical AC (BRD-12)
1. **Seam A page tests** (`tests/test_board_page.py`, real server): `GET /` 200 with the file's content, E10 headers, `Cache-Control: no-store`; no external URL and no E18 forbidden token; every hex literal is in the palette set; missing file → 500 JSON; `/state` has `live` (false in replay) and still exactly the other keys; no absolute path appears in `/state`.
2. **Sections:** all E25 sections and markers exist in the file, in order; stubs have final signatures (QA reads the file).
3. **State flow:** the page fetches `/state` once on load, then follows the event stream; an unreachable server shows a visible "reconnecting" state and recovers (Developer shows it in evidence by stopping and restarting the replay server).
4. **Canvas:** viewport-sized, devicePixelRatio-aware (sharp on 2x), resizes with the window; no canvas taller than the viewport; the draw loop is idle when nothing animates (Developer shows rAF count stays 0 over 5 s on a quiet fixture).
5. **Mirror (E17):** `#needs-you`, `#pods`, `#columns` hooks exist and match `/state`; built with `textContent`.
6. **XSS:** the fixture's `<img src=x onerror=alert(1)>` message is never executed (Playwright: no dialog, no `img` element in the DOM).
7. **Baseline AC 1 to 5, 7, 9, 10** from design.md; page technical AC 1 to 7 of design-iteration-2.md.

## Behaviour AC (blackbox: checkable in the browser with Playwright in replay mode, no code reading)
Start: `bin/squad-board --replay tests/fixtures/board/page --now <fixed> --port 0`, open the printed URL.
B1. **Needs-you bar on top:** shows "Needs you" and a count equal to its listed items; with the fixture it lists the blocked agent, the unanswered escalation and the idle Manager (3 items); a BLOCKED message between agents is not listed. With a fixture that has none, the bar says nothing is waiting.
B2. **One column per live agent**, Manager's column first, grouped by pod with the pod name and size on a band above; order is roster order and does not change on reload.
B3. **Headers** match the round 6 header card: name, status dot (pulsing ring while working or blocked), `⏱` working total on the left, `⛔` blocked total on the right only when non-zero, and the context tokens as a raw count with thousands separators or `—` (no percentage, no meter). Role and the status word are in the card or on hover and always in the text mirror.
B4. **Look:** the page looks like the round 6 prototype (needs-you card with mango left edge, tinted pod bands labelled `POD · SIZE`, header cards). **Colours:** needs-you mango, working teal, idle muted grey, blocked red; the background is the light cream, never dark.
B5. **Blocked header** has a red outline and a pulsing marker.
B6. **Retired agent with no events** in the viewed iteration is a narrow stub, not a full column.
B7. **12 columns fit** at 1280 px wide with no horizontal scrollbar; names are truncated with `…`.
B8. **Reload keeps the view** (same state, same order). A server restart makes the page show "reconnecting" and recover on its own.
B9. **Hostile text** in a message never runs script or shows markup.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
