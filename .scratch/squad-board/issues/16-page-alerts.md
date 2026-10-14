Status: resolved
State: done (PASS; in the iteration-2 line merged at 7f0b436)
Task ID: BRD-16
Blocked by: 12
Files touched: `bin/squad-board.html` (sections `alerts` and its mirror part)

# BRD-16: page alerts: notification, chime, tab title, no repeats

**Done when a needs-you item that appears while the page is open fires one notification and one soft chime, never again for the same item, and nothing fires for items already present at load.**

Read first: design-iteration-2.md (E23), spec stories 6 to 9. Replace only the `alerts` section.

## Technical AC (BRD-16)
1. **Seen set (E23):** ids in `localStorage`, pruned as specified; items at first render count as seen; an id reappearing after it resolved (same id) does not notify again, a new id does.
2. **Permission:** requested only from the **Enable alerts** click; after a decision the button is hidden; `Notification` undefined, denied or throwing → silent, the rest of the page unaffected.
3. **Notification content:** title "Squad needs you", body the item text (plain); `tag` = the item id so the browser replaces rather than stacks.
4. **Chime:** WebAudio, two sine notes, peak gain ≤ 0.08, under 600 ms; created lazily after a user gesture; a suspended or failed context is silent; no audio file, no network.
5. **Tab title:** `(n) squad board` while `n > 0` items, `squad board` otherwise.
6. **Testability:** the page reads the `Notification` constructor and `AudioContext` from `window` at fire time, so a Playwright init script can replace them with recorders; no other hook is added to production code.
7. **Baseline AC 1 to 5, 7, 9, 10**; page technical AC 1 to 7.

## Behaviour AC (blackbox)
Playwright stubs `Notification` and `AudioContext` with recorders through an init script.
B1. **New item notifies once:** with the page open, make an agent blocked (append `blocked` to the activity log); exactly one notification and one chime fire, the bar and the tab title update to include it.
B2. **No repeat:** further unrelated events and a reconnect do not fire it again; reloading the page does not fire for items already present.
B3. **Resolved then new:** when the item resolves and a different new item appears, only the new one notifies.
B4. **Enable alerts** asks permission once and then disappears; if permission is denied nothing breaks and no sound plays.
B5. **A BLOCKED message between agents** does not notify (it is not a needs-you item).

### QA whitebox additions (qaw-board)

Checked by running the Developer's tests plus my own scratch checks; a point I cannot run is a FAIL with the reason. Applies on top of the BRD-12 Q-points.
- **Q1 Scope:** diff touches only `bin/squad-board.html`, section `alerts` and its mirror part; other markers unchanged; no server change; no stubs left. Production code adds no test-only hook (AC 6): the page reads `window.Notification` and `window.AudioContext` at fire time, not at load (I replace them after load with a recorder, notifications must still hit it).
- **Q2 Seen set:** key is exactly `squad-board.seen:<origin>`; value is ids only; pruned to current ids plus the last 200 (feed 250 ids, check 200 + current kept, order = most recent). Items at first render are seen: reload with 3 current items notifies 0. A resolved-then-reappearing same id: no second notification; a new id: one. **Open point (to tech-board):** pruning drops ids not current beyond the last 200, so after 200 other ids a long-resolved id could notify again. I accept that as the design (E23), not a defect, unless tech-board says otherwise.
- **Q3 Unusable storage:** `localStorage` throwing (private mode), corrupt JSON, a non-array value → page works, treats as empty, no exception; and no mass notification then (items at first render still count as seen).
- **Q4 Permission:** `Notification.requestPermission` is called only from the **Enable alerts** click, never on load or on a new item; the button hides after granted or denied (also if `requestPermission` rejects or returns a promise-less value); `Notification` undefined, `permission === 'denied'`, and a constructor that throws → silent and the bar, title and rest of the page still update.
- **Q5 Notification content:** title exactly `Squad needs you`, body = the item text as plain text (hostile item text such as `<img src=x onerror=alert(1)>` arrives as the same string, no markup effect), `tag` = item id. One notification per new item. **Decision needed from tech-board:** two new items in one state update: one chime or two? E23 and the ticket say "a chime" per item; I test it as one notification per item and at most one chime per update (no overlapping chimes) unless tech-board rules otherwise.
- **Q6 Chime:** two oscillator notes of type `sine`, peak gain value never above 0.08, total under 600 ms, context created lazily on a user gesture; no `fetch`/`Audio()`/`src` use; `suspended` or constructor throwing → silent. I measure with a recording `AudioContext` stub (gain setValueAtTime/linearRamp values, oscillator start/stop times).
- **Q7 Title:** `(n) squad board` with the number of current needs-you items, `squad board` at 0; it follows the count when items resolve and appear, also when a notification is denied or `Notification` is missing.
- **Q8 No repeat:** reconnect of the stream, unrelated state updates, and a page reload never fire again for an id in the seen set. A BLOCKED message between agents (not needs-you) fires nothing. The first state after a reconnect that already contains known items fires nothing.
- **Q9 Blocked transition:** appending `blocked` to the activity log of a rostered agent creates one new item → one notification, one chime, count and title +1 (the ticket's B1). I run it on a scratch copy of the page fixture.
- **Q10 Console clean**, no uncaught rejection from `Audio`/`Notification` in any of the failure modes above (I listen to `pageerror` and `unhandledrejection`). Evidence: a Playwright log of the recorded calls in squad/evidence/BRD-16/.

## Comments
