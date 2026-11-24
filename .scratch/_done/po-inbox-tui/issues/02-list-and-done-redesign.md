# Task 02: List and Done list redesign (one row per item)

Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=dev, business-ac=ticket, code-check=dev (self-review, Manager confirms), behaviour-check=dev evidence (Manager confirms), handin-target=manager, suite-owner=qa-white (at the end only), promote-owner=dev, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Team: no QA (PO decision 2026-10-29). Branch from the passed sha of task 01 (it adds the shared tier helper and also edits `ui.tsx`). Hand in to the Manager. `BLOCKED 02` on a risk flag or doubt.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`. Spec: `.scratch/po-inbox-tui/spec.md`.
Design: ui-design/list.md, ui-design/done.md
Depends: 01 (same file `ui.tsx`; tier helper in `core.ts`).

## What
Build the list (`list.md`) and the Done list plus the done item rules (`done.md`): short tier one row per item with right-aligned short age; tall tier unchanged two-row item; heading row carries `[ Done (N) (d) ]` and the `↓ N more` hint; Done list with Back and heading on one row, reason folded out of the row; done item outcome line first and never cut.

## Touches (confirmed before AC)
`hooks/po-inbox/ui.tsx` (`listScreen`, `heading`, `group`, `row`, `subLines`, `doneScreen`, the outcome-first order in `handledBlock` for done kinds), `core.ts` (use the tier helper; no new constants), `list.test.ts`, `done.test.ts`, `ui.test.ts` where they cover these screens. Not touched: `itemScreen`, `answerForm`, `draw.tsx`, `markup.ts`.

## AC
1. Built UI matches the design: every screen and state (list.md sections 2-3, 7; done.md sections 2-3).
2. Short tier (`bodyRows <= 8`): one row per item (`1: E1  answer  title …  8h`); the "Answered, waiting" group keeps its sub-row; at 24 rows the seeded list shows 3 items (was 2).
3. Tall tier: item rows unchanged (two rows); only the heading row changes.
4. Heading row: `Inbox · N to answer · M to read`, `[ Done (N) (d) ]`, dim `↓ N more` (N = items below); the bottom Done button is removed. Drop order at narrow widths per list.md section 7.
5. Done list: Back + heading on one row; short age; short tier one row per item; tall tier a sub-row only for a withdrawn item with its reason clipped to one row.
6. Done item: outcome line directly under the title, outcome colour, wraps up to 4 rows, never cut by the 6-row window; then answer, options with `●`, Context.
7. `GROUP_CAP` 7-row fold and hotkeys 1-9 unchanged; band unchanged.
8. Evidence: real-pane captures at 24 and 40 rows and 80/60/47 columns for list, Done list, done item (withdrawn with a long reason); in `issues/02-list-and-done-redesign/evidence.md`. Targeted tests green.

## Design notes
Written by dev-2 before building. Code stays in `ui.tsx`; no new constants in `core.ts`; the tier is `heightTier(bodyRows)`.
- **Row geometry.** A row is a plain `Button`: `n: ` (3 cells the engine draws), `E1`, 2 spaces, kind word, 2 spaces, title, then in the short tier (done list: both tiers) padding and the dim short age. Padding = `cols - used - ageWidth`, at least 2. The title is clipped to `cols - prefix - 2 - ageWidth` (floor 10, as today). No age: the title takes the width.
- **Short tier list.** One row per item. The waiting group keeps its `(your answer sent …)` sub-row and shows no age on the row. Tall tier: rows as today.
- **Heading row** is a `Box` row: counts text, `[ Done (N) (d) ]`, dim hint. Layouts tried in the drop order of list.md section 7: (A) long words + button + hint, (B) long words + button, (C) short words + button, (D) short words, button on its own row. Long words only from 60 columns (the existing rule). The hint is only in A. No done items: no button, same order.
- **`↓ N more`**: while building I count rows. N = items whose first row lies below `bodyRows`, plus the hidden count of a `+N more` fold that lies below. No such item: no hint. Design example says "3" for 2 remaining items; the AC says items, so N is items.
- **Done list.** Row 1 = Back + heading (`Done · newest first (N)`); narrow: count dropped, then heading under Back. Tall tier: sub-row only for a withdrawn item with a reason, clipped to one row (`withdrawn: reason…`), dim. Short tier: no sub-rows. Short age on the right in both tiers.
- **Done item.** The outcome line is already right after the title (ticket 01). New: in the Decide page the line is cut at `min(4, max(2, bodyRows - row1 - titleRows))` rows with `…`, and a `… full text [Details]` row follows; the Details page now also draws the handled block (it was missing for handled items), so Details shows the whole text.
- **Tests.** `list.test.ts`, `done.test.ts` updated (hotkey order now `d` first, done sub-rows, clipping); new tests for the short tier, hint, narrow heading, done list and outcome. `ui.test.ts`/`item.test.ts` only if they break.

## Verification (no QA)
Before HANDIN: (1) run the `mattpocock-skills:code-review` skill on your branch since its base and fix every finding it confirms; (2) write `## Review` in this file: findings, what you fixed, what you left and why; (3) run only the test files you touched plus the `grep -rl` hits (CLAUDE.md); do NOT run the full suite (PO: full suite only once, at the end, by QA whitebox on the final integrated sha); (4) save real-pane evidence per the AC in `evidence.md` and check it with `squad-evidence check`. HANDIN names the branch, sha, evidence sha and the `## Review` path. The Manager confirms; no QA runs.

## Review

Skill `mattpocock-skills:code-review`, since 4a818d6, effort high. Standards: no hard violation (CONTEXT.md terms, ADR 0007, CLAUDE.md test rules respected). Spec: AC 2-5 and 7 found implemented and tested.

**Fixed**
- Test gap (spec a3): `done.test.ts` now has "a 4-row outcome stays whole; a longer one keeps 3 rows and a Details row" (no `…`/`full text` at 4 rows; at more, the line ends `…`, at most 3 rows, `full text` row follows).
- Design note said `… full reason [Details]`; the code and evidence say `full text`. The note now says `full text`.

**Left, and why**
- AC6 "never cut by the 6-row window" (spec a2): a cut outcome keeps 3 rows (2 after a 2-row title) so the Details row fits in the 6-row window. A 4-row outcome with a 1-row title stays whole. This is the design note's own rule (cap `min(4, max(2, room))`); Details shows the whole text.
- `itemScreen` touched (spec b1): the ticket's own design notes ask for the handled block on the Details page and the Details row. Accepted, not scope creep.
- The 4-row cap also applies to `answered-waiting` (spec b2): same `handledBlock`; its outcome lines are short, so no visible effect. Left.
- ADR 0007 edited (spec b3): one sizing line, as the design needs.
- No hint at docked width (spec c1): follows the drop order of list.md section 7 (the hint is dropped first). Accepted deviation; the hint shows from the width where it fits.
- Hint at a visible `+N more` fold (spec c2): a visible fold shows its own count; the hint counts items below the window only. Left.
- Withdrawn outcome colour (spec c3): `dimColor` is the existing `outcomeTone`; unchanged by 02.
- Smells (standards, all judgement calls): the default body-rows expression appears 3 times; the title/age row layout appears in `listScreen` and `doneScreen`; bare gap literals; `headingRow` takes 7 parameters. Left: they match the file's current style, and a refactor now would widen the diff of a ticket other tickets (03) also edit in `ui.tsx`. Note for a later cleanup.
- Pre-existing: the "Details" page line ends `..` when a withdrawal reason ends with a full stop (`handledLines`). Left.
- Accepted deviations: the hint counts items (the design example said 3 for 2); the Done gap on the list heading is 2 spaces so the docked 47-column heading fits one row.
- No glossary term added by 02.
