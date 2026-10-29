# Task 02: List and Done list redesign (one row per item)

Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Team: designer (retired), qa-white, qa-black. Suite: as task 01. Branch from the passed sha of task 01 (it adds the shared tier helper and also edits `ui.tsx`). Hand in to both QAs. `BLOCKED 02` on a risk flag or doubt.
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
(Developer writes here before building.)
