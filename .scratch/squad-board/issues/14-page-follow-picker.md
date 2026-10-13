Status: ready-for-agent
State: ready
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

(qaw-board adds points here.)

## Comments
