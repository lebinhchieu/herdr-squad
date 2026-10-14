Status: resolved
State: done (PASS; in the iteration-2 line merged at 7f0b436)
Task ID: BRD-14
Blocked by: 12
Files touched: `bin/squad-board.html` (sections `follow`, `picker`, and their mirror parts)

# BRD-14: page history: follow live, pause, ↓ live, iteration picker

**Done when the page follows new events by default, pauses when the PO scrolls up, resumes from "↓ live", and replays another iteration from the picker.**

Read first: design-iteration-2.md (E15, E21, E22), spec stories 50 to 54. Replace only the `follow` and `picker` sections.

## Technical AC (BRD-14)
1. **Follow (E21):** within 40 px of the bottom = following; new rows keep the bottom in view; the new-row count while paused is exact.
2. **Scrolling programmatically** (resize, state update, picker change) never flips following by itself; only a user scroll does (wheel, key, scrollbar drag).
3. **Picker (E22):** `<select>` of `state.iterations`; changing it requests `/state?iteration=N` and reconnects the stream with `N`; an unknown iteration is not offered; the stream never mixes iterations.
4. **Banner** `#replay-banner` only for a non-current iteration; choosing the current one removes it and resumes following.
5. **No request storm:** switching iteration three times quickly leaves exactly one open stream and shows the last choice (older responses are ignored).
6. **Mirror:** `#live-state`, `#live-button`, `#iteration-picker`, `#replay-banner` as in the hooks table.
7. **Baseline AC 1 to 5, 7, 9, 10**; page technical AC 1 to 7.

## Behaviour AC (blackbox)
B1. **Default follows:** with the page open at the bottom, appending a message to the log shows it at the bottom without any scrolling; `#live-state` says Live.
B2. **Scroll up pauses:** after scrolling up, new events do not move the view; the state says Paused and a **↓ live** button shows how many rows arrived.
B3. **↓ live resumes:** clicking it jumps to the bottom, the button disappears, state says Live.
B4. **Picker:** lists every iteration; choosing iteration 1 shows only iteration 1's rows and bars (totals in headers stay whole-run), shows the replay banner and stops following.
B5. **Back to the current iteration** returns to live and following.
B6. **History survives:** closing and reopening the page shows the same history (it comes from the logs).
B7. **Reload on a replayed iteration** returns to the current one (the picker is not persisted).

### QA whitebox additions (qaw-board)

Checked by running the Developer's tests plus my own scratch checks; a point I cannot run is a FAIL with the reason. Applies on top of the BRD-12 Q-points.
- **Q1 Scope:** diff touches only `bin/squad-board.html`, sections `follow`, `picker` and their mirror parts; markers of the other sections unchanged; no server change. No stubs left in the two sections.
- **Q2 40 px edge:** exactly 40 px from the bottom is following, 41 px is paused (I scroll to those offsets in Playwright). Following uses the scroll position of the page, not a stale cached height; a page shorter than the viewport counts as following.
- **Q3 Programmatic scroll never flips following:** window resize, a state update that adds rows while paused, and a picker change must not set paused or following by themselves. Test each by the mirror's `#live-state`. Wheel, key (PageUp/Home) and scrollbar drag do flip it. A scroll event fired by our own `scrollTo` is not treated as a user scroll.
- **Q4 Count exact:** rows that arrive while paused: `#live-button[data-new-rows]` equals the number of rows I append (1, 2, 5), also across two state updates, and resets to 0 after `↓ live`. A gap row or status row counts as a row.
- **Q5 Picker options:** the options are exactly `state.iterations`, each `Iteration N`, current one selected; an iteration not in the list cannot be requested (a crafted `?iteration=99` URL is handled by the server, not offered). With a single iteration the picker still works and shows no banner.
- **Q6 One stream:** switch iteration three times quickly (script `select.value` changes within 50 ms): exactly one open `/events` connection afterwards (I count requests and closed streams), the displayed iteration is the last choice, a late response of an older request is ignored (delay the first `/state` response with route interception). The stream URL carries `iteration=N`; rows of two iterations never appear together.
- **Q7 Banner:** `#replay-banner` exists only for a non-current iteration, text `Replay of iteration N`; choosing the current one removes it, follows again and scrolls to the bottom. Reload on a replayed iteration returns to the current one (not persisted: no `localStorage`/URL state for it).
- **Q8 Headers on replay:** header totals stay whole-run when an old iteration is viewed (B4 of the ticket); I check against `/state?iteration=N` of the server.
- **Q9 Reconnect interplay:** an `/events` drop while paused keeps paused and the count; recovery does not reset the view or double the rows.
- **Q10 No leaks:** old `EventSource` closed before the new one opens; no listener added per picker change (I count scroll listeners before/after ten changes via a spy in an init script).
- **Q11 Console clean** and no NaN in the mirror at 0 new rows; evidence screenshots at 1280, 1600, 1920 exist in squad/evidence/BRD-14/.

## Comments
- 2026-10-13 tech-board rulings (asked by the first dev-board-14, who was retired before building):
  - **State-section edit approved:** only `let stream = null`, a `closeStream()` call first in `connectStream`, `stream = source`, and an `onerror` guard `stream !== source` (signature unchanged). The pending retry must also do nothing if `stream` changed or another iteration was chosen since (AC 5); test the stale retry.
  - Picker, ↓ live button and replay banner are DOM overlays built from JS inside the `follow`/`picker` sections: `textContent` only, mirror hooks as in the table, palette-only colours, no HTML or CSS edits.
  - In a replayed iteration ↓ live returns to the current iteration.
  - The stream stays pinned to its iteration; when a newer iteration appears the Replay banner names the iteration shown and offers the same ↓ live return. Test: a newer iteration appears while on N.
  - Tell qaw-board in the HANDIN that the `connectStream` edit is deliberate (it already knows).

