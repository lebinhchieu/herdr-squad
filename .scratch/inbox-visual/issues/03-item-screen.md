Status: ready
Blocked by: 01, 02, Designer's final `ui-design/IV-03.md`
Task ID: IV-03
Design: ui-design/IV-03.md
Files touched: `hooks/po-inbox/ui.tsx` (`body`, `handledLines`, `answerForm`, `itemScreen` only), `hooks/po-inbox/draw.tsx` (new: block, inline, table, option-block drawing), `hooks/po-inbox/item.test.ts` (new), `hooks/po-inbox/ui.test.ts` (only assertions the new look breaks)

# IV-03: the item screen: header, structured body, option blocks, handled lines

**Done when an open answer item, an open read item, an answered, waiting, answered-in-chat, withdrawn and read item each draw as `ui-design/IV-03.md` shows, at 80x24 and 40x24, with the top block of V-01/V-02 (spec v3) in the first viewport.** Built UI matches the design: every screen and state. Business AC: V-01..V-14a, V-15 (item rows), V-17, V-18, V-22..V-24, V-26, V-27, V-28 (draw half), V-30 (keys unchanged except those `ui-design/IV-03.md` lists under "Keys").

## What to build
- `draw.tsx`: `drawBody(blocks, cols, T)`, `drawSpans`, `drawTable` (aligned or stacked by `tableLayout`), `drawOptions(options, key, picked, T)`; each a function of props, no `$`. Style and token per element come from the design; tokens only from `TONE` or weight (T6).
- `ui.tsx`: `body` = `bodyBlocks` + budget (T9 v3, the floor from the design) + `Show all`; the first viewport is the top block of T9 v3: back button, header, title, `recPointer` row (V-01), in that order, for an answer item; kind, blocks, title for a read item (V-02), with the design's "more below" hint; `itemScreen` header per V-03/V-04 with `blocksTone`/`kindTone`; `answerForm` options as blocks, the marked option from `recommendedKey`, the recommendation drawn once (under the marked option, else its own "Manager recommends" line); picked shown in words plus marker, nothing picked on open; `handledLines` tones per V-15 (read, withdrawn, removed = dim); the PO's answer, draft and note drawn plain (T11); title capped at 3 rows with Show all reaching the whole title (V-09).
- The unparsed-Options path (V-14) keeps `options_raw` whole and the reply field; a handled item with options shows them with the recommended mark and the PO's pick in words (V-14a).

## Technical AC
1. `item.test.ts` mounts every state of the design at 80, 60, 59, 40 and 30 columns with the real `scroll.bodyRows` of the engine (QA blackbox baseline: 7 content rows at 24 terminal rows, 11 at 40; confirm per 3.1), on E1, E2 and the fixtures of IV-01; asserts text (colourless), `styleOf` per element against the design's token table, and the **top block of V-01 in order** (back, kind + blocks, title, `recPointer` row) as the first rows of the drawn tree at bodyRows 7 and 11 and widths 80 and 40, counted with the test's own reference wrap (3.1), with and without a notice/error row.
2. Each V-11 table row through the real screen: the marked option has the mark text and `success`; unmarked rows have none; the rec text appears exactly once (V-12).
3. V-26: with a markdown body and options, picking an option and a note runs `answer` with the same argv and stdin as before the change (a test pinned to the pre-change values); the answer shown back is verbatim, with `**` still present.
4. Body cut by budget (T9 v3): E1 at bodyRows 7 shows the floor of body lines the design names, then "N more lines", then the options; Show all draws every word (V-07 oracle: words of the body in order in the pane text); at a tall pane (bodyRows 30) everything shows and there is no cut.
5. Hostile fixtures (10,000-char line, 5,000 `**`, unclosed fence, only `|`, empty) mount in under 2 s each (assert with a clock bound), draw as plain text where unstructured, and do not stop another item from drawing.
6. V-27: ESC, OSC and U+202E in title, body, option text, rec and a table cell draw none (one assertion per source).
7. V-15: no `success`/`error`/`warning` on any element the design lists as structure (V-18); a test walks the tree of a body with heading, code, bold and table and finds none.
8. Existing `ui.test.ts` assertions changed are listed in `dev-evidence.md` with the reason; no other test is weakened.
9. `variant="primary"` check (design.md, Button bullet): the Designer's answer is applied; recorded in `dev-evidence.md`.
10. Screenshots of every design state as pane text (herdr pane read to text, 80x24 and 40x24) in `dev-evidence.md`.
11. V-30: a test pins the item-screen key map (every key and its action) to today's values, except the keys the design lists under "Keys"; each listed change is named in `dev-evidence.md`.
12. Common AC 1-8 of `design.md`.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **3.1 (rewrite) V-01 is counted with an independent measure and the real `bodyRows`.** (a) `dev-evidence.md` records the `bodyRows` the engine actually delivers to the pane at 80x24 and at 40x24, read from a live herdr pane (print it once in a scratch run, or compute from a pane read); `item.test.ts` uses those numbers and cites the evidence file. (b) `rowsOfTree` must not call the same `rowsFor` the screen uses to decide the cut; the test counts with its own reference wrap (the one of 2.2b). (c) E1 at 80x24 and 40x24 each with: no notice, an `ok` notice, and an error row (the chrome is larger): the V-01 list still fits, or the body shrinks to the floor and the list stays. (d) `bodyRows` 14 and 10 (too small): no crash, every option still drawn, body floor 2 lines.
  **v3 override (spec V-01 v3):** "the V-01 list still fits" in (c) and "every option still drawn" in (d) now mean: the top block (back, kind + blocks, title <= 3 rows, rec pointer row) is first and fully inside `bodyRows` 7 at 40 columns; options and controls follow below it in V-03 order and are reached by scrolling (not required inside the first 7 rows). V-12: the full rec appears once in the item; the pointer row is never the only copy.
- **3.2 (keep) V-11 rows through the real screen** and add: the marked option's mark text is a separate `Text` from the option key/text, so colourless mode shows "recommended" as a word (V-17).
- **3.3 (rewrite) V-26 pinned to the base sha.** Expected argv, stdin and the `describePrompt` text are literals recorded by running the **base** sha (the commit before IV-03, named in the test comment), for: option + note; free text only; text with `**`, `#`, `|`, backtick, CJK, a trailing newline and two blank lines. Stdin is asserted byte for byte (no trim). The answer shown back is the same text drawn as plain children (no parse): assert the tree holds `**` literally. Picking the recommended-marked option and picking a different one send the same shape of call; the key sent is the picked option's key (V-13: no warning text appears).
- **3.4 (keep)**, plus: Show all draws every word of the body and the whole title (oracle 1.3, order kept).
- **3.5 (tighten)** Hostile set also: 5,000 leading spaces before a bullet (indent is capped, so nothing exceeds the pane: `rowsFor` over the drawn row stays within `cols`), a 200-character unbroken token in a body line, a code line of 200 characters, a table of 20 columns, at 40 and 30 columns. "Other items still draw": the test mounts a list/item for the hostile item next to E1 and asserts E1 intact.
- **3.6 (new) Nothing drops words by truncation.** A tree walk: no `Text` that draws body, code, table-cell, option or recommendation text has `wrap="truncate"` or `truncate-*`; they use wrap (V-07, V-08). Only the capped title may end with an ellipsis, and Show all removes it.
- **3.7 (tighten) V-27** adds ESC/OSC/U+202E in: the option key, the id, a code fence line, a `[rec]` line, the withdrawn reason, and the PO's answer shown back (from the file).
- **3.8 (new) Keys (V-30).** The existing hotkey and Select/Button behaviour is pinned by the existing `ui.test.ts` cases staying green; if option blocks replace `Select`, a new test drives pick, type, submit and back with the same keys as before, and no two Buttons on a screen share a hotkey.
- **3.9 (new) V-17 colourless.** For each state a helper strips every style prop and the test asserts the screen still carries: blocked vs not (words), recommended mark (word), waiting vs delivered (words), error vs ok (the `⚠`/`✓` glyph).
- **3.10 (tighten)** Screenshots: pane text at both sizes for every design state, plus **one `--format ansi`** capture of E1 showing the theme tokens render as colour in a real pane (a tree prop is not a pixel).

## Tech Lead notes on the final design (2026-10-16; binding)
- Design is `ui-design/IV-03.md` (final). Send is a plain Button: no `variant` (design's answer to item 9; record it in `dev-evidence.md`).
- The `[rec]` line draws `✓ recommended` and the bullets draw glyphs, so the pane has extra characters and a word (`recommended`) the body lacks: the V-07 pane oracle is "the body's words appear in the pane text **in order as a subsequence**, inside the body region", not equality (AC 1.3's equality stays for `plainOf`).
- "First block taller than the budget is clipped with `…`" needs a row clip: write `clipRows(text, cols, rows)` in `draw.tsx` on `rowsFor`/`cellWidth` (never a half wide char; a test with CJK); the words cut are reachable by Show all (test: Show all draws every word).
- The "↓ more below" hint is driven by the estimate (rows > `scroll.bodyRows`); `rowsFor` rounds up, so it may show once when all fits by a row; accepted. A test: hint absent at bodyRows 40 for E1, present at 7.
- Handled items put the state right after the title (design, BA informed); the `Picked:` row is removed: list it with the other changed `ui.test.ts` assertions.


## Spec v3.1 alignment (Tech Lead, 2026-10-16; binding)
- V-03 exception: a handled item (answered, waiting, answered in chat, withdrawn, read) draws the state line and `Your answer` right after the title, before the body; an open item keeps header, title, rec row, body, options. One test per handled state asserts the order from the pane text.
- V-05: bullets draw `•` / `◦` / `▪` by depth with the indent kept; numbered items keep the number as written. `plainOf` equality (AC 1.3) is unchanged; the pane oracle is the subsequence rule above.
- V-15 (item rows): `blocks X` is red while the item is open or answered-waiting, dim once released (delivered, answered in chat, withdrawn, read); a test per state asserts `styleOf`.
- Header: `created 5h ago` under one day, the date from one day (design); `Picked: none yet` is gone and no option shows as picked on an open item (V-10).

## Ruling: the first viewport is 6 rows at 24 (Tech Lead, 2026-10-16; binding, overrides every "7" above)
- QAW read `scroll.bodyRows` live: **6** at 80x24 and 40x24, 11 at 40 rows (`evidence/IV-03/qa-w-live/README.md`). "7 content rows" in the design, spec V-01/V-02, AC 3.1 and `item.test.ts` was a miscount.
- Rule (design.md T9 v3.2): the top block (back, header, title, rec pointer) fits `scroll.bodyRows`. `titleCap = clamp(bodyRows - 1 - headerRows - pointerRows, 1, 3)`: 3 rows at 80x24, 2 at 40x24 when the header takes 2 rows. A cut title keeps its `… full title` row. The pointer row always stays in the first viewport.
- Tests: mount at `bodyRows` 6 (24-row terminals) and 11 (40-row), the engine's real values, on E1, E2 and a 300-char title with a 2-row header at 40 columns (QAW's `long-title-40x24` case): the pointer row is inside the first `bodyRows` rows by the tree, and the expected `titleCap` is written out in the test per case. The "hint absent / present" test (Tech Lead notes) uses 11 and 6. Replace every `bodyRows 7` in `item.test.ts`.
- `dev-evidence.md`: pane text at 40x24 for the long-title case showing the pointer row in view.
- The refused-answer notice row is transient and outside `titleCap`; the first-viewport bar (V-01) applies to an item opened without a notice (Designer's edge-state row, accepted).
