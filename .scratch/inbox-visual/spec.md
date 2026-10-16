# Inbox visual

Status: v3.2 (BA 2026-10-16: 7 content rows corrected to 6 at 24 rows, V-01/V-02/Terms; behaviour bar unchanged) · v3.1 (BA 2026-10-16: V-03, V-05, V-15, V-21 take the Designer's rulings 1-3, 6; QA blackbox to confirm) · v3 (BA 2026-10-16): V-01, V-02, V-12 changed after QA blackbox's baseline finding (pane height); v2 agreement stands for every other AC, re-agreement on V-01/V-02/V-12 pending

**The PO inbox (TUI mod) shows an item as structure and colour instead of a wall of prose, so the PO reads what is asked, what it blocks and what the Manager recommends in about five seconds, without the Managers writing anything differently.** Brief: `scopes/inbox-visual/scope.md` (PO notes E1, E2 bind). Builds on `.scratch/po-inbox/spec.md` (B-01..B-36 stay true).

## The goal behind the brief

The PO decides from the inbox. Today the item screen prints the body line by line (`hooks/po-inbox/ui.tsx` `body`, `answerForm`): numbered questions, `[rec]` tags, `**bold**` and tables arrive as raw characters, options are plain `(a) text` lines and the recommendation is one dim line. The need is not "pretty": it is **"I see at a glance what is asked, what it costs to wait, and what the Manager would pick, and I answer in one step."**

## Terms

- **Item screen**: the pane that opens one item (header, title, body, options, recommendation, answer controls or handled state).
- **Structured body**: the item body drawn from the markdown subset of V-05.
- **Recommended option**: the option the Manager's `--rec` text names by its leading key (table in V-11).
- **Colour meaning**: fixed (V-15). Green = passed / recommended / delivered. Red = blocks work, failed, error. Amber = warning, waiting, not verified. Dim = metadata. Nothing else carries a meaning colour.
- **First viewport**: the rows of the mod's pane visible on opening an item, before any key press. The pane is a scrolling viewport of about a third of the terminal height (QA baseline: 24 rows → 6 content rows; 40 rows → 11, read live from the engine by QA whitebox, `evidence/IV-03/qa-w-live/README.md`; the first baseline said 7 and 12), so an item may be taller than the viewport and the rest is reached by scrolling. **Reference sizes: 80x24, 40x24, 80x40, 40x40** (columns x rows; the pane's own chrome rows count).
- **Group**: the list's three groups: *blocking* (open, blocks something), *other open* (open, blocks nothing), *answered-waiting*.
- **Fixtures**: E1 and E2 (real, `.claude/squads/plugin/scopes/inbox-visual/inbox.jsonl`) and QA blackbox's hostile set (`evidence/qa-b-spec-review.md` → Fixtures). The Tech Lead's plan names the fixtures dir.

## Scope

In: the item screen (first), the list, the band, the done list and done-item view. Out: HTML or pages (PO E1), the collapsed `squad-inbox add` row, the CLI's stored data, the `escalations.md` format, any change to how a Manager must write (no new `squad-inbox add` field; D3).

## User stories and business AC

Given/When/Then, observable in the pane: text (`herdr agent read --format text`, also the colourless check) and colour/weight (`--format ansi`, or the drawn tree in `claude plugin test`). Colour is judged by the **theme token the Designer names per element** (A4). IDs `V-nn` are for QA blackbox and tickets.

### US1: I grasp an item in five seconds
*As the PO I open an item and know what is asked, what waits on it and which answer is recommended, without reading the whole body.*

- **V-01** Given the E1 item (long rec, 3 long options, 12-line body), when I open it at each reference size, then the first viewport shows, in this order and without a key press: **(1) kind and what it blocks (or "nothing"), (2) the title, (3) one row naming the recommended answer**: "recommends (c)" when an option is marked (V-11), otherwise the start of the recommendation, truncated with an ellipsis. The Designer confirms (1)-(3) fit the 6 content rows the engine gives at 24 rows, 40 columns, back button included. Where the viewport has more rows, it fills with what follows in V-03 order. Everything else (the full recommendation, every option, the body, the answer controls) follows in V-03 order and is reached by scrolling; if the pane is tall enough for everything, everything shows. The Designer says how the PO can tell there is more below; QA checks that text. A title longer than the rows left in the first viewport may be shown cut, with a marked row that shows the rest on scrolling (v3.2); no word of it is dropped.
- **V-02** Given an open read item, the first viewport (every reference size) shows kind, what it blocks and the title (the hard bar); the start of the body shows where the viewport has room (not at 40x24, where the back button, header and title take the 6 content rows). Mark read follows and is reachable by scrolling, and by key `m` as today.
- **V-03** Position carries meaning: on every item screen the order is header (id, kind, blocks, age) → title → body → options and recommendation → answer controls or handled state. Same order for every item of the same kind; the one-row recommendation of V-01 sits right after the title and is a pointer, not a second copy of the order below. **Exception (v3.1, Designer's ask 1):** a handled item (answered, waiting, answered in chat, withdrawn, read) puts its state line and "Your answer" right after the title, before the body, so the outcome is in the first viewport; same for every handled item.
- **V-04** Labels sit beside the thing they name: each value on the same line as its label ("blocks spawning the pod", "created today").

### US2: The body reads as structure
*As the PO I read what Managers already write as structure, not as markup characters.*

- **V-05** The subset is: headings (`#`..`###` + space), bullets (`-`, `*` + space), numbered (`1.` + space), `**bold**`, `` `code` ``, fenced code blocks, pipe tables. Nested bullets keep their indent; a bullet draws as a glyph (•, ◦, ▪ by depth) in place of `-`/`*`, a numbered item keeps its number as written (v3.1). The Designer's `ui-design/` names, per element, the treatment (weight, glyph, indent, background; colour only per V-18); **each recognised element differs from plain body text in at least one named attribute**, and no raw `**`, backticks, heading `#`, or table pipe/separator row remains for a recognised element. Must stay plain text: `#1 priority`, `2024-10-16`, `1.5`, `-5`, `*italic*`, `_x_`, a lone `**`, a `-` inside a word.
- **V-06** A line whose first non-space text is exactly `[rec]` (lowercase; E2 writes it after spaces) shows a green "recommended" tag in place of the literal `[rec]`; the rest of the line is unchanged. `[REC]` and a `[rec]` mid-line stay literal.
- **V-07** Never dropped, mechanically: the body's words (split on whitespace, syntax characters of recognised elements removed) all appear in the pane text, in order, after Show all. Markup outside the subset (links, images, blockquote, HTML, unbalanced `**`, malformed table) shows as the plain text it is. `<br>` still means a line break.
- **V-08** A table wider than the pane (also with CJK or emoji cells) does not clip or overlap: it wraps, or each row stacks as `column: value` lines (the Designer picks one) with every cell readable.
- **V-09** A body of 40 lines or a title of 300 characters keeps V-01 true: the body is simply further down; the title shows at most **3 rows** with an ellipsis (the Designer may change the 3, but a cap exists) and the whole title and body stay reachable (Show all or the detail).

### US3: Options are choices, the recommended one is marked
*As the PO I see each option as its own block and which one the Manager recommends.*

- **V-10** Each option shows as its own block (key, text), not a dim list line. On open **no option shows as picked** (po-inbox D4). A keyboard focus marker, if any, is a marker or weight, never a meaning colour; picking shows the pick in words ("your pick") plus a marker.
- **V-11** Matching is exactly this table (QA tests every row; the spec row wins over any parser):

| `--rec` text | Marked |
|---|---|
| `(c), built (a) first: …` (E1) | c |
| `(c) yes`, `  (c) yes` (leading space) | c |
| `(a) no, (b) is worse` | a (only the leading run counts) |
| `(C) yes` | none (keys are lower-case, as the Options cell format) |
| `c) yes`, `Option c`, `c. yes` | none |
| `(a)+(b)`, `(a)/(b)`, `(a), (b)`, `(a) and (b)` | none |
| `(z) yes` (no such option) | none |
| `Reply 'all recs' …` (E2), empty rec | none |

- **V-12** The marked option carries a green "recommended" mark (words plus colour); the whole recommendation text is shown **once** in the item, in full: under the marked option, or, when nothing is marked, as its own line with a green "Manager recommends" label. The one-row pointer of V-01 is a key or a truncated start, never the only copy. The text is never dropped.
- **V-13** A pick on a different option than the recommended one shows no warning.
- **V-14** An item whose Options cell was not parsed (po-inbox B-22) shows the options text whole and readable; the reply field works as today.
- **V-14a** (A3) A handled item with options still shows them, the recommended mark stays, and the PO's pick is marked in words.

### US4: Colour means one thing
*As the PO I learn the colours once.*

- **V-15** One meaning per colour on every screen. Colours are theme tokens, never RGB, and hold under the default dark and the light theme. **What is coloured** (nothing else is):

| Element | Colour |
|---|---|
| Header/list kind word of an open **answer** item | amber |
| Kind word of a read item | none |
| "blocks X" label, X ≠ nothing, while the work is still blocked (open, or answered and waiting) | red |
| "blocks X" label on a released item (delivered, answered in chat, withdrawn, read) | dim |
| "blocks nothing", id, "created …", "+N more", other metadata | dim |
| "recommended" mark and "Manager recommends" label | green |
| Error rows (B-35), refused-answer message, "⚠" notices | red |
| "✓" ok notice | green |
| "answered, waiting for the Manager", "answered in the file (not through the inbox)", "this item changed while you were reading" | amber |
| "answered … delivered", answered in chat | green |
| Withdrawn, read, removed (handled lines and done list) | dim |
| Band: "N to answer", "N waiting" | amber |
| Band: "N to read" | none (the current accent goes) |
| Band: "N problem(s)" | red |
| Buttons, focus, selection | none of the above: bold or inverse plus a marker glyph; Buttons plain |

- **V-16** Hence one open answer row shows amber (kind) and red (blocks) on different elements; a read item row has no colour except dim metadata. The band has no "blocking" count (D4).
- **V-17** With colours stripped (`--format text`), the pane still tells blocked from not blocked, recommended from not, waiting from delivered, error from ok, by words and position.
- **V-18** Structure (headings, code, bold, table) is carried by weight, shape and position, never by the four meaning colours.

### US5: The list groups and stays short
- **V-19** Group order (blocking, other open, answered-waiting) and oldest-first inside a group (B-06) stay; each row shows kind and what it blocks per V-15; the heading keeps its counts.
- **V-20** Each group (and the done list, newest first) shows at most 7 rows then a row `+N more` that, when activated (a key or button the Designer names), expands the group in place to all its rows. Edges: 7 items show no fold; 8 show 7 and `+1 more`; 12 blocking + 9 other show 7 and `+5 more`, 7 and `+2 more`. The heading counts and the band never change by folding. Blocking items past the seventh are folded, not lost.
- **V-21** The band keeps its counts (V-15 colours) and an Open inbox button on one line, at 80 and at 40 columns (the button label may shorten, the counts stay). **Exception (v3.1):** only when the counts cannot fit one row at 40 columns even with the shortest labels (for example four kinds at once with two-digit counts, or 120 to answer + 15 waiting + 3 problems), the band wraps to two rows with every count present; counts are never cut.

### US6: Narrow panes stack
- **V-22** Under 60 columns (the existing compact cut-off) everything stacks in one column: header values, options, table rows, controls. Nothing is clipped or overlaps; every option and the answer controls are reachable. Tested at 60 and 59 columns (the boundary), 40 and 30. **30 is the smallest width where V-22 holds;** below it nothing crashes and the text stays readable.
- **V-23** Wide panes (60+) show the same content and order as narrow ones; side-by-side options only if the Designer's design shows them and V-01 still holds.

### US7: Handled items and the done list
- **V-24** Answered, waiting, answered-in-chat, withdrawn and read items keep today's words (QA takes baseline captures of today's build first) and gain the colour of V-15.
- **V-25** The done list shows each outcome word in its V-15 colour, order unchanged. *Should-have: the Tech Lead may drop it as the one droppable ticket.*

### US8: Nothing breaks
- **V-26** The text the PO answers with reaches the Manager byte for byte as before; rendering never changes stored text or an answer (B-14, B-23). After answering, the PO's answer is **shown back plain and verbatim**; markdown in it is not rendered (A1).
- **V-27** Every drawn string, including each new styled element (headings, table cells, code, tags), stays sanitised (control characters, bidi): ESC / OSC / U+202E in title, body, option text, rec and table cell draws none.
- **V-28** Hostile bodies (empty, only `|`, 10,000 characters on one line, 5,000 nested `**`, unclosed fence) open within 2 seconds without crash or hang; the item shows, as plain text where it cannot be structured (V-07), and other items still show. A malformed or hand-edited file shows its error row (B-35) in red, naming file and row.
- **V-29** The po-inbox AC B-05..B-07, B-09..B-17, B-32, B-33, B-35, B-36 still pass (QA blackbox walks them by hand; the full B-01..B-36 re-run is QA whitebox's suite).
- **V-30** (A5) Keys to open, pick, type, submit and go back stay as today, except those the Designer lists in `ui-design/` under "Keys" (QA reads that text).

## Defaults I took (the PO may object; none change the goal)

- **D1** Only four colours carry meaning (PO's palette); "to read" loses its accent.
- **D2** Reads are uncoloured: reading is neither pass nor fail.
- **D3** No new `squad-inbox add` field and no change to `agents/manager.md`: the recommended option comes from the key the Manager already writes in `--rec` (table V-11). E2 allowed new fields; none are needed.
- **D4** The cap of 7 applies per group and to the done list; blocking items past the seventh are folded behind `+N more` (counts never fold). The band shows no "blocking" count: that is the list's job.
- **D5** The markdown subset is fixed (V-05); extending it is a new scope.
- **D6** The Designer decides the exact look (glyphs, spacing, code and table treatment, side by side or not); V-nn say what must be true.

## Out of scope

HTML/pages and anything outside the TUI; new item kinds or fields; the collapsed add row; `squad-board`; markdown beyond V-05; theming or user-set colours; surfaces other than the terminal (po-inbox ruling).

## Agreement with QA blackbox

QA blackbox reviewed 2026-10-16 (`evidence/qa-b-spec-review.md`): 11 rewrites R1-R11 and 6 additions A1-A6, all taken into v2 above (R1→V-01, R2→V-05, R3→V-06, R4→V-07, R5→V-09, R6→V-10, R7→V-11/12, R8→V-15, R9→V-20, R10→V-22, R11→V-28, A1→V-26, A2→V-08, A3→V-14a, A4→V-15, A5→V-30, A6→V-29). Where I changed their proposal: the band shows no "blocking" count (D4); the done list is capped like the groups (V-20). **AGREED by QA blackbox on V-01..V-30 (v2), 2026-10-16**, accepting both changes. **v3 (BA, after their baseline finding that the pane shows about 7 rows at 24 terminal rows, `evidence/baseline/README.md`): V-01 and V-02 now ask for kind, blocks, title and the recommended answer in the first viewport, the rest by scrolling; V-12 allows the one-row pointer. QA blackbox re-agrees V-01, V-02, V-12 and the reference sizes; every other AC is unchanged.** **v3.2 (BA, Tech Lead's correction from QA whitebox's live read): 6 content rows at 24 terminal rows, not 7; V-01/V-02/Terms reworded; QA blackbox to confirm.** **v3.1 AGREED by QA blackbox 2026-10-16 on V-03 (handled-item order), V-05 (glyphs: `•` depth 0, `◦` depth 1, `▪` depth 2 and deeper, 2 cells of indent per depth; the removed `-`/`*` are syntax characters under V-07), V-15 ("blocks X" red while open or answered-waiting, dim once released; tested on E11 vs E13 and the done list) and V-21 as widened (one row for ordinary counts; two rows only when counts do not fit with the shortest labels of the band ladder in `ui-design/IV-04.md`, tested with 120/15/3); the age, "Picked: none yet", group-total and amber-waiting changes are fine while V-04, V-10 and V-15 hold.** **AGREED by QA blackbox on V-01, V-12 and the reference sizes 2026-10-16; V-02 reworded to their text (hard bar: kind, blocks, title; body start where there is room) and AGREED with that wording.** A taller pane (the mod growing the viewport while an item is open) is welcome if the Tech Lead finds it cheap, never required. Conditions (full text at the end of `evidence/qa-b-spec-review.md`):
- Colour and weight are judged against the Designer's named theme tokens and per-element treatments in `ui-design/`; if missing, V-05, V-15 and V-18 are FAIL "could not test".
- V-01 at 40x24 with the E1 item is tight and stays a hard bar; the Designer confirms it fits.
- QA blackbox takes baseline captures of today's build before the first handed-in ticket (V-24, V-29).

## Open points for the PO

None blocking. D1, D3 and D4 are the ones to look at in the check-in.

## Lasting business rules and glossary (for `promote.md`)

- Glossary: **Structured body**, **Recommended option**, **Colour meaning** in `CONTEXT.md`.
- Rule: in the inbox each colour has one fixed meaning (green pass/recommended, red blocks/fails, amber warning/waiting, dim metadata); meaning is never by colour alone.
- Rule: rendering never drops or changes the Manager's or the PO's text; unknown markup shows as plain text.
- Rule: an option is marked recommended only when the recommendation starts with exactly one existing option key; otherwise no option is marked.
- ADR candidate: none unless the Tech Lead's parser choice (own subset parser vs library) is lasting.
