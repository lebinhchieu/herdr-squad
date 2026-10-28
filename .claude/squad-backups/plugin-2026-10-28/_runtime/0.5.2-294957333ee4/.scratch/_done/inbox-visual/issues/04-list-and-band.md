Status: ready
Blocked by: 02, Designer's final `ui-design/IV-04.md`
Task ID: IV-04
Design: ui-design/IV-04.md
Files touched: `hooks/po-inbox/ui.tsx` (`renderBand`, `listScreen`, `heading` only), `hooks/po-inbox/testkit.ts` (only the `rowsOfTree` row-Box fix, if taken), `hooks/po-inbox/list.test.ts` (new), `hooks/po-inbox/ui.test.ts` (only assertions the new look breaks)

# IV-04: the list and the band: colour meaning and the 7-row fold

**Done when the band and the list draw as `ui-design/IV-04.md` shows: V-15 colours per element, groups of at most 7 rows with `+N more` expanding in place, at 80 and 40 columns.** Built UI matches the design: every screen and state. Business AC: V-15, V-16, V-19, V-20, V-21, V-22 (band and list), V-27, V-30 (keys unchanged except those `ui-design/IV-04.md` lists under "Keys"; `+N more` is the one expected addition).

## What to build
- `renderBand`: colours per V-15 (answers and waiting amber, problems red, "to read" no colour: `suggestion` is removed); one line at 80 and 40 columns; counts never fold.
- `listScreen`: kind word and "blocks X" per `kindTone`/`blocksTone`; each group through `capGroup`, a `+N more` Button (key or label from the design) that sets `more` with `patchUi`; hotkeys 1-9 over shown rows; group headings and totals unchanged; folded blocking items stay reachable.

## Technical AC
1. `list.test.ts` (uses `testkit.ts`): band states as today (both, reads, answers, waiting, errors, none) with `styleOf` per V-15 row; `suggestion` appears nowhere in the drawn tree.
2. Fold edges of V-20: 7, 8, 12+9, and 7+0; `+N more` expands only its group; going to an item and back resets `more` (T10); the heading counts and the band equal the totals folded or not; the 8th blocking item is reachable after expanding.
3. Row text at 80, 60, 59, 40, 30 columns: nothing wider than the pane after `rowsFor`, kind and blocks both visible.
4. Hotkeys: a test pins 1-9 over the shown rows and that `+N more` takes no digit.
5. Sanitiser: ESC, OSC, U+202E in title, blocks and an error row draw none (V-27).
6. Existing `ui.test.ts` band/list assertions changed are listed in `dev-evidence.md`.
7. Pane-text screenshots at 80 and 40 columns of: 12+9 list folded and expanded, band both/narrow, in `dev-evidence.md`.
8. V-30: the list-screen key map is pinned to today's values except the keys the design lists under "Keys" (test 4 covers the digits).
9. Common AC 1-8 of `design.md`.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **4.2 (tighten) fold.** Also 0 items in a group; 7+8; a snapshot refresh while expanded where an item is answered and the group drops to 7 or fewer (no crash, no stale `+N more`); items past 9 when expanded still have an `onPress` (hotkey only on 1-9).
- **4.3 (rewrite) row text.** No use of `fit` (code points) for width: a CJK title and an emoji title at 30 and 40 columns; a 300-char `blocks` value and a 300-char title: the row ends with an ellipsis, kind and blocks word both visible, nothing wider than `cols` by `cellWidth`.
- **4.4 (tighten)** Hotkeys: unique across the screen, `+N more` for two groups gets two distinct keys or labels (as the design names); `i`, `d`, back are not reused.
- **4.8 (new) Band width.** The widest case (`120 to answer`, `15 waiting`, `3 problems`) is one line at 80 columns; at 40 it is 42 cells at rung 5, so it takes rung 6 (2 rows, every count present; corrected 2026-10-16 after IV-04's ASK); at 30 nothing crashes and the counts stay first.
- **4.9 (new)** Within a folded group the shown rows are the oldest 7 (B-06) in order; the hidden count equals the total minus 7.

## Carried from IV-02 (QAW 2026-10-16; pass conditions)
- **2.10 old atom:** every reader of `ui.more` uses `ui.more ?? []`; one test drives `goTo`, `patchUi` and the list screen on `{...FRESH_UI, more: undefined}` without a crash.
- **`rowsOfTree`/`lines()` over-count a `flexDirection="row"` Box** (they count every Text/Button as its own row): the one-line band tests (V-21, 4.8) must not use `rowsOfTree`; they assert the band is one row from its Box structure or fix `rowsOfTree` in `testkit.ts` (allowed in this ticket, with its own test).

## Tech Lead notes on the final design (2026-10-16; binding)
- Design is `ui-design/IV-04.md` (final).
- **Do not reuse `fit`** (design "What it reuses" lists it): it counts code points. Title clipping uses `clipCells` from IV-02 (QAW 4.3).
- **The band ladder rule wins over the design's example lines.** Rungs 1-6 are chosen by `cellWidth` of the whole line against `bodyColumns`; some examples at 35 columns are wider than 35 (e.g. `Inbox  3 to read   [ Open inbox (i) ]` is 37 cells and takes rung 2). Tests assert the rule per state at 75 and 35 columns (compute the expected rung from the rule in the test, written out literally), not copies of the examples.
- `+N more` is a plain Button with `dimColor`, no hotkey, no digit; with the keys test (AC 4) it is in the Tab order after the last shown row of its group.


## Spec v3.1 alignment (Tech Lead, 2026-10-16; binding)
- V-21 exception: the band is one line at 80 and 40 columns in every state except four kinds at once with two-digit counts at 40 columns, where it wraps to two rows (design IV-04 rung 6); counts are never cut. Tests assert both: the one-line states by Box structure, the exception as exactly 2 rows with all four counts present. AC 4.8's widest case (`120 to answer`, `15 waiting`, `3 problems`) is 42 cells at rung 5, so at 40 columns it takes rung 6 (2 rows, every count present; Tech Lead ruling after IV-04's ASK, my 4.8 was wrong); at 80 it is one line. The rule is the design's: counts are never cut, so the wrap is the fallback of rung 6 for any state too wide, not only the four-kinds case.
- V-15 (list rows): `blocks X` red while open or answered-waiting, dim on released rows (delivered, answered in chat, withdrawn, read); a `styleOf` test per row state.
- List group titles carry a dim total `(12)`; the waiting count in the heading and the band is amber.
- **Dim on `+N more` (ruling after QAW FAIL d784203, overrides the note above):** the Button is `plain` with a `Text dimColor` child; the engine's Button support for `dimColor` is unconfirmed. The V-15 test asserts it on the child Text of both `more-blocks` and `more-nothing`. IV-05's `+N more` row is the same (design IV-05 says `dimColor`; read it as on the child). IV-06's ansi capture confirms it.
