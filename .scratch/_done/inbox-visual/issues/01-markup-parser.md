Status: ready
Blocked by: none
Task ID: IV-01
Files touched: `hooks/po-inbox/markup.ts` (new), `hooks/po-inbox/markup.test.ts` (new), `hooks/po-inbox/fixtures/visual.ts` (new)

# IV-01: the markdown-subset parser (pure)

**Done when `parseBody(text)` turns any string into a list of blocks, never throws, never loses a word, and every V-05/V-06/V-07/V-28 case passes as a unit test.** No drawing here. Design: `design.md` T1-T5, T12. Business AC: V-05, V-06, V-07, V-28 (parser half).

## What to build
- `markup.ts` exports the types `Block`, `Span`, and `parseBody`, `parseInline`, `plainOf` as in `design.md` T5. Pure, no `$`, no imports from `ui`/`actions`.
- `fixtures/visual.ts`: the fixtures of T12 (E1, E2 verbatim; a heading/list/table/code body; a table wider than 40 columns; a table with CJK and emoji cells; a 40-line body; a 300-char title; empty and title-only bodies; ESC/OSC/U+202E variants; unclosed fence; only `|`). Big generated cases (10,000 chars on one line, 5,000 `**`) are built in the test.

## Technical AC
1. One test per row of V-05's "must stay plain" list: `#1 priority`, `2024-10-16`, `1.5`, `-5`, `*italic*`, `_x_`, a lone `**`, a `-` inside a word; each yields plain paragraph text.
2. One test per recognised element (heading levels 1-3, `-` and `*` bullets, nested bullets keep depth, `1.` list, bold, code, fenced code with and without a closing fence, pipe table with header/separator/rows, table with a malformed separator = paragraphs). `[rec]` tests: leading spaces ok; `[REC]`, mid-line `[rec]`, `[rec]x` stay literal.
3. **Never drop:** for every fixture and for 200 seeded random strings drawn from `# - * 1. ** \` | [rec] <br>` spaces and words (a fixed seed, in the test), the words of `plainOf(parseBody(x))` equal the words of `x` after removing the syntax characters of recognised elements only (the test states its own oracle in a comment).
4. **Linear:** 10,000 chars on one line, 5,000 `**` in one line, 5,000 backticks, 2,000 table rows and an unclosed fence each parse in under 200 ms in the test (assert on a generous bound, not a benchmark).
5. Two real samples (E1, E2) and the constant case (empty body; body equal to the title) are among the cases; the fixtures file's header says where each came from.
6. No body in `.claude/squads/*/scopes/_done/*/escalations.md` makes `parseBody` throw or lose a word (a script in `dev-evidence.md`, read-only; paste the count).
7. Common AC 1-8 of `design.md`.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **1.3 (tighten) Never-drop oracle must not be the parser.** Oracle = the alphanumeric words (`/[\p{L}\p{N}]+/gu`) of the input, in order, minus only: the `rec` of a recognised `[rec]` tag, the digits of a recognised `N.` marker. It is compared with the alphanumeric words of `plainOf(parseBody(x))` **in order** (V-07 says "in order"; a set or multiset compare is a FAIL). The comment in the test states this oracle. Run it on every fixture and on the 200 seeded strings; the generator alphabet adds CJK, emoji, `\r\n`, tab, 20 leading spaces, and `<br>`.
- **1.7 (new) `<br>` and the title line.** T2's pipeline (`sanitize` → `<br>` → drop first line if equal to title → parse) is a pure function in `markup.ts` (e.g. `bodyBlocks(body, title)`), not inline in `ui.tsx`, so IV-01 tests it: `<br>` in E2 shape, `<BR/>`, first line equal to title (dropped), first line equal to title but a second line also equal (only the first dropped), body equal to title (empty result, not a crash), `\r\n` body.
- **1.4 (tighten) Linear.** Add the quadratic killers to the list: `**a ` x 5,000 (unclosed openers), `**a**b` x 5,000 pairs, alternating `` ` `` and `*`, `|` x 10,000 on one line, a table of 2,000 rows x 20 cells, 5,000 `- ` nested by leading spaces (depth 2,500), 10,000 `<br>`, and `plainOf` on each result. Besides the absolute bound (< 200 ms), assert scale: time(4n) < 12 x time(n) + 20 ms for the bold and backtick cases (catches O(n^2) without a benchmark).
- **1.8 (new) Totality edge.** `parseBody('')`, `'\n'`, `'   '` return a defined list (empty or blanks) and `plainOf` of it is `''`; the result type says which, in a test.
- **1.9 (new) Table edges.** Ragged rows (fewer and more cells than the header), one-column table, empty cells, trailing pipe absent, separator with alignment colons (`:---:`), a table directly after a paragraph with no blank line, `\|` (decision stated in a test: split or literal, but no word lost).
- **1.10 (new) Fence edges.** Fence with info string (` ```ts `), `~~~`, fence indented, fence inside a bullet; stated behaviour per case, no word lost, and a `[rec]`/`#`/`**` inside a fence stays literal.
- **1.6 (tighten)** The script reads `scopes/*/inbox.jsonl`, `scopes/*/escalations.md`, `scopes/_done/*/escalations.md` of every `.claude/squads/*`, and `squad-inbox list --json` per home; prints bodies seen, blocks found per type, throws 0, words lost 0 (same oracle as 1.3). The count is pasted. Read-only.
- **1.5 (tighten)** Fixtures E1/E2 are byte-copies: a test asserts a fixed known substring of each (E1's `(c), built (a) first`, E2's `<br>` and `[rec]` run) and the header says the source path and date.

## Decision after HANDIN (Tech Lead, 2026-10-16)
`fixtures/index.ts` is generated by `tests/po_inbox_fixtures.py` and stays untouched: the `export { E1_OPTIONS, ... VISUAL }` line is removed. Tests of this scope import `from './fixtures/visual'` directly. No change to `tests/*.py`.
