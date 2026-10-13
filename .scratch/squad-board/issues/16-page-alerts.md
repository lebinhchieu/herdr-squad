Status: ready-for-agent
State: ready
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

(qaw-board adds points here.)

## Comments
