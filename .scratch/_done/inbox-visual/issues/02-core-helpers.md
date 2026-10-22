Status: ready
Blocked by: none
Task ID: IV-02
Files touched: `hooks/po-inbox/core.ts`, `hooks/po-inbox/core.test.ts`, `hooks/po-inbox/testkit.ts` (new), `hooks/po-inbox/actions.ts` (`FRESH_UI`, `goTo` only), `types/index.d.ts` (`InboxUi.more`)

# IV-02: pure helpers: recommended key, widths, table layout, cap, tones, test kit

**Done when `core.ts` offers the helpers of `design.md` T6-T10 with tests, `InboxUi` carries `more`, and `testkit.ts` lets the UI tickets mount the pane and read colour and weight.** No drawing. Business AC: V-11 (matching), V-08/V-22 (widths, layout), V-20 (cap), V-15 (the tone constants).

## What to build
- `core.ts`: `TONE` (`good: 'success'`, `bad: 'error'`, `warn: 'warning'`; dim is `dimColor`), `recommendedKey`, `cellWidth`, `rowsFor`, `tableLayout`, `capGroup` (cap 7), `bodyBudget` (T9 v3: inputs bodyRows, chromeRows, floor; returns rows), `clipCells(s, cols)` (cut to at most `cols` cells by `cellWidth`, never splitting a wide char, ending with `…` when cut, `cols` < 1 = `''`), `recPointer(rec, options, cols)` ("recommends (c)" when `recommendedKey` finds one, else `clipCells` of the rec's first line, `''` when there is no rec; one row, never wider than `cols`), `kindTone`/`blocksTone`/`outcomeTone` mapping an item or done kind to `good|bad|warn|dim|none` per the V-15 table (one function per row family so a UI ticket never invents a colour).
- `types/index.d.ts` `InboxUi.more: string[]`; `actions.ts` `FRESH_UI` has `more: []`, `goTo` resets it. Nothing else in `actions.ts` changes.
- `testkit.ts`: the helpers `boot`, `item`, `snap`, `band`, `pane`, `lines`, `dump` copied from `ui.test.ts`, plus `styleOf(tree, text)` (the props `color`, `dimColor`, `bold`/`weight`, `italic`, `underline`, `inverse` of the Text that holds `text`) and `rowsOfTree(tree, cols)` (rendered rows via `rowsFor`). `ui.test.ts` is not edited.

## Technical AC
1. `recommendedKey`: every row of the V-11 table is one test, with the table's exact strings, plus `(c)` with options `[a,b]` = null, and `(a)` with `options` null = null.
2. `cellWidth`: ASCII 1; CJK `漢字` 2 each; an emoji 2; a combining accent 0; tab/newline never reach it (sanitised before). `rowsFor('', n)` = 1; exact fit = 1; one over = 2; a word longer than `cols` is hard-wrapped.
3. `tableLayout`: aligned only at `cols >= 60` and when the widest row fits; stacked otherwise; with CJK/emoji cells the aligned widths use `cellWidth` (a test for each of aligned/stacked on the same table at 80, 60, 59, 40, 30 columns).
4. `capGroup`: 7 items = no fold; 8 = 7 shown, `+1`; 12 and 9 = `+5` and `+2`; expanded = all; order unchanged.
5. `outcomeTone`/`kindTone`/`blocksTone` cover every row of V-15's table (a table-driven test); read kind = none; "blocks nothing" = dim; any other `blocks` = bad.
6. `testkit.ts` is imported by a test of its own (`styleOf` finds a bold, a dim and a coloured Text in a tiny tree).
7. `clipCells`/`recPointer`: ASCII, CJK and emoji at cols 30 and 40 (width by `cellWidth` never exceeds `cols`; a wide char at the cut is dropped whole), exact fit has no ellipsis, a 300-char rec, rec null and `''`, marked (`(c)`) and unmarked rec, `[rec]`/ESC in the rec (sanitised by the caller: a test says so).
8. `git diff` of `actions.ts` shows only `FRESH_UI` and `goTo`.
8. Common AC 1-8 of `design.md`.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **2.1 (tighten) `recommendedKey`.** Besides the V-11 rows: `(a)` alone; `(a)text`; `(a),(b)`; `(a) / (b)` with spaces; `(a) or (b)`; `(a) AND (b)`; `(a)and(b)`; `(b) yes (a) no` = b; `(a)` with `options: []`; duplicate option keys (two `a`) = null; `rec` null and `''`; leading tab/NBSP. Each is a test with the expected value written in the test, not derived.
- **2.2 (tighten) `cellWidth` / `rowsFor`.** Iterate by code point (`'😀'` is 2, not 4; an astral char followed by a combining mark is 2); fullwidth forms `Ａ` = 2; Hangul and `、` = 2; U+200B = 0; `❤` + U+FE0F: the chosen width is pinned in a test; ZWJ family: pinned (accepted limit, but pinned). `rowsFor` embedded `\n` counts rows per line, empty lines = 1; leading and repeated spaces; word-wrap on spaces, hard-wrap on a word longer than `cols`; `cols` 0 and negative do not hang or divide by zero.
- **2.2b (new) `rowsFor` is conservative.** A property test over 300 seeded strings and cols 30..100 compares it with a reference greedy word-wrap + hard-wrap written in the test file: `rowsFor` is never smaller than the reference. When Ink's real wrap is unknown, it rounds up.
- **2.3 (tighten) `tableLayout`.** Ragged rows, one column, zero rows, empty cells; the "fits" rule counts column separators and padding (state the formula in the test); exactly-fits and one-over at cols 60; the stacked form keeps every cell once and in order (words oracle as 1.3).
- **2.4 (tighten) `capGroup`.** 0 items; returns new arrays (input not mutated); `hidden` equals `items.length - 7` and `shown` is the first 7 in input order (B-06 oldest first).
- **2.5 (tighten) tones.** The test iterates the kinds from the real contract fixtures (`fixtures/contract-*.ts`: `answered`, `answered-file`, `read`, `withdrawn`, `removed`, source `chat`), not a hand list; an unknown kind returns `none`, never throws.
- **2.9 (new) `bodyBudget`.** `max(2, bodyRows - chromeRows)`; `bodyRows < chromeRows` = 2; `bodyRows` undefined or NaN does not crash (a pane without `scroll`), falls back to a stated number.
- **2.10 moved to IV-04** (no reader of `ui.more` exists in IV-02; QAW 2026-10-16). `types`/`FRESH_UI` still carry `more: []`.

## QAW FAIL 7c2731c (2026-10-16): four findings are pass conditions
Source `evidence/IV-02/qa-w.md`: (1) `rowsFor` hard-wrap places code points one at a time (a wide char that does not fit starts the next row; `'漢'x10` at 5 cols = 5 rows, `'漢'x3` at 3 = 3, `'漢'x200` at 31 = 14); (2) the 2.2b reference is an independent per-character simulation, the `toBe(1) && toBe(2)` line is split; (3) `styleOf` returns the innermost Text containing the text (nested Text case in `testkit.test.ts`); (4) `cellWidth` covers the emoji-presentation ranges listed there (`✅ ❌ ⭐ ⌛ 🫠` = 2, `✓ ⚠` stay 1, pinned).
