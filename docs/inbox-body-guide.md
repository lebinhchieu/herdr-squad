# Writing an inbox body

For Managers. The PO reads your inbox item in a small terminal pane. At 24 terminal rows the pane shows 6 body rows. The title, the options and the answer box use most of them. So the body is read on the Details page.

The PO looks at the shape first. A *verdict* is your one-sentence answer or ask. A *callout* is a highlighted line. A *fence* is the line of three backticks that opens and closes a block. A *connector* is a line or arrow in a diagram. Use forms the pane draws: a highlighted verdict, a table, a diagram, a short list. Use prose only for one reason line.

Every form named here is drawn by the pane today. Do not use a form that is not on this page.

## Order of an answer item

1. **Verdict line.** One `[decision]` line. Say what you need from the PO in one sentence. If you recommend an option, name it and give the one fact that decides it.
   - Why: this is the first line the PO reads, and it is the one that stands out.
2. **Options table**, when two or more options differ on facts. Columns like `| Option | Cost | Risk |`. At most 3 columns. Keep each cell short: 24 characters at most. One row per option. Also put the options in `--options`; the table compares them.
   - Why: a table lets the PO compare options in one look.
3. **A diagram or a list** for structure: order, flow, who depends on whom.
   - Diagram: start the fence with `diagram`, then a short caption. The caption says what an arrow means, for example `A ──> B: B waits for A`. Use 44 columns at most and 6 lines at most. Use only ASCII and box-drawing characters (`- | + > v ^ ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`). No emoji, no CJK.
   - You may add a state tag after a node name: `[ok]`, `[fail]`, `[warn]` or `[skip]`, with a space before and after it (a tag followed by a comma is plain text). The pane draws the tag in colour and adds a legend row. The pane also colours the connectors. Do not try to colour anything yourself.
   - List: one fact per bullet.
   - Why: a diagram keeps its shape and the pane never wraps it. A wide drawing is cut and marked.
4. **One prose line** for the reason, such as `Why: ...`. Not a paragraph.
   - Why: long prose is the part the PO skips.
5. **Links last**, each on its own line, as `[label](https://...)`. Only when the PO must open something.
   - Why: links are rarely needed. They must not push the verdict down.

## Order of a read or check-in item

1. `[info]` or `[decision]` verdict line: what happened, and what the PO should do.
2. A table of results. Use the badges `[ok]`, `[fail]`, `[warn]`, `[skip]` in the cells.
3. A `[warning]` line for the one thing that matters most, then a list of what needs attention. Put `[warning]` on its own line: inside a list item it is plain text.
4. One prose line.
5. URL links last, if any.

## Forms the pane draws

| Form | You type | The pane draws |
|---|---|---|
| Callout | `[decision]`, `[warning]` or `[info]` at the start of a line | a filled label, then your sentence |
| Badge | `[ok]`, `[fail]`, `[warn]` or `[skip]` inside a line or a table cell | a filled, coloured chip |
| Table | rows like `\| a \| b \|`, then a `\|---\|---\|` line | aligned columns |
| Diagram | a fence that starts with `diagram` | no wrapping, blue connectors, tag colours, legend row |
| Link | `[label](https://...)` | the label and the address |
| Recommendation | `[rec]` at the start of a line | a green recommendation line |
| Also | headings, `-` lists, `1.` lists, `**bold**`, `` `code` `` | as in markdown |

Anything the pane does not know stays as plain text. No word is ever lost.

## Rules

- Do not repeat the title in the body. The first line is the verdict.
  - Why: the title is already on screen, and rows are few.
- Write a tag exactly: lowercase, at the start of the line (`[decision]`, `[warning]`, `[info]`, `[rec]`).
  - Why: `[Warning]` with a capital letter is shown as plain text.
- Use badges inside a line or a table cell.
  - Why: a badge marks one fact next to the words it describes.
- At most one `[decision]` and one `[warning]` per body.
  - Why: if everything is highlighted, nothing is.
- Say every fact in words. Do not leave a fact only in a diagram or a colour.
  - Why: some terminals show no colour.
- Use a heading only when the body is longer than 15 lines.
  - Why: a heading costs a row, and rows are few.
- Put local paths and commands in `` `code` ``. Do not align text with spaces outside a table or a diagram.
  - Why: code keeps its exact characters, and text lined up with spaces breaks when a line wraps.
- Colour comes only from the tags. Use `[ok]` and `[fail]` for facts, not for decoration. Use at most 4 tag kinds in one diagram.
  - Why: the pane takes the colours from the PO's theme, so they stay readable. A tag used for looks tells the PO something false.
- No HTML except `<br>`, which the pane turns into a line break. No images. Do not use `*italic*`: the stars show as plain text.
  - Why: the pane shows what it does not know as plain text, so the PO would see the raw tags and stars.

## Example 1: an answer item

Command. The body is in the file.

```
squad-inbox add --kind answer \
  --title "Which branch merges first: BRD-01 for BRD-02..06?" \
  --options "(a) PO merges BRD-01 as soon as it passes; (b) Developers stack on squad/dev-board-1; (c) PO merges each passed branch as it passes" \
  --rec "(a), one merge unblocks 5 tickets" \
  --blocks "BRD-02..06" --body-file /tmp/e1-body.md
```

`/tmp/e1-body.md`, exactly:

````
[decision] Merge BRD-01 first (a): one merge unblocks 5 tickets.

| Option | Unblocks | Risk |
|---|---|---|
| (a) merge BRD-01 now | 5 tickets | low |
| (b) stack on dev-board-1 | 5 tickets | needs a spawn option |
| (c) merge each branch | 1 per merge | slow |

```diagram merge order if (a)
BRD-01 ──merge──> spec ──┬─ BRD-02
 (QA ok)                 ├─ BRD-03
                         └─ BRD-04..06
```

[warning] Option (b) needs a `squad-spawn` change outside this scope.

Why: (a) costs one PO merge now; (b) and (c) cost a Manager ping on every branch.

Spec: [BRD-01 plan](https://github.com/acme/squad/pull/42)
````

The pane draws a callout, a table, a diagram, a callout, one prose line and one link, in that order.

## Example 2: a read or check-in item

Command:

```
squad-inbox add --kind read \
  --title "Iteration 1 passed: all 3 tasks" \
  --body-file /tmp/r1-body.md
```

`/tmp/r1-body.md`, exactly:

````
[info] All 3 tasks passed QA whitebox and blackbox. Branches are ready for your review.

| Task | WB | BB |
|---|---|---|
| 01 item view | [ok] | [ok] |
| 02 list and done | [ok] | [ok] |
| 03 body styles | [ok] | [warn] |

[warning] 03 passed blackbox with one note: links over 200 characters wrap.

- Merge in order: `01`, `02`, `03` (all touch `hooks/po-inbox/draw.tsx`).
- Evidence: `tasks/issues/NN-*/evidence.md`.
- Suite: `python3 tests/run_suite.py --tz` [ok] 412 passed, 0 failed.

Next: review and merge; nothing is waiting on you.

[PR 12](https://github.com/acme/squad/pull/12)
````

The pane draws a callout, a table with badges, a second callout, three bullets, one prose line and one link, in that order.

## Kept in step with the pane

Both example bodies are the fixtures `guideE1` and `guideR1` in `hooks/po-inbox/fixtures/visual.ts`. Two tests guard them. `tests/test_inbox_body_guide.py` checks that the examples here are the same text as the fixtures. `hooks/po-inbox/markup.test.ts` parses the fixtures with the real parser and checks the block types. If a form stops parsing as this guide says, a test fails.
