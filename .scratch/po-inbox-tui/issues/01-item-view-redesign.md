# Task 01: Item view redesign (decision first, Details page)

Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Team: designer (retired), qa-white, qa-black. Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` (CLAUDE.md Running tests); full suite by QA whitebox on the final sha. Branch from repo HEAD (main). Hand in to both QAs. A risk flag, user-visible change or business doubt found: `BLOCKED 01`.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`. Spec: `.scratch/po-inbox-tui/spec.md`.
Design: ui-design/item.md
First action: commit the drafts from `$SCOPE_DIR/tasks/` (spec.md, issues/01-*.md, issues/02-*.md) to `.scratch/po-inbox-tui/` in your first commit.

## What
Build `ui-design/item.md` (Status: final): answer item "Decide" page, Details page, read item, handled item, body drawing (P7 chips, P8 headings), title rule (P6), the one-row hint, narrow-width drop order. Also add the shared height-tier helper (`bodyRows <= 8` short, `>= 9` tall) in `hooks/po-inbox/core.ts`, exported for ticket 02.

## Touches (confirmed before AC)
`hooks/po-inbox/ui.tsx` (`itemScreen`, `answerForm`, `handledBlock`), `draw.tsx` (`drawOptions`, `drawBody`), `markup.ts` (`bodyBlocks` title rule), `core.ts` (tier helper only), `item.test.ts`, `ui.test.ts`, `markup.test.ts`, `docs/adr/0007-inbox-sits-on-escalations.md` (the two consequence lines, item.md section 12). Not touched: `listScreen`, `doneScreen` (ticket 02 owns them).
Tests/harness: `hooks/po-inbox/testkit.ts`, fixtures in `hooks/po-inbox/fixtures/`. Run `grep -rl '<changed string>' tests/ hooks/po-inbox/` before HANDIN and run every hit (CLAUDE.md).

## AC
1. Built UI matches the design: every screen and state (item.md sections 3-8, 13).
2. Answer item: Back + header + hint on one row; title (max 2 rows, `…` + Details when cut); options as pickable `○`/`●` Button rows (Select removed); recommendation shown once (short tier `✓ rec` tag, tall tier reason row; no top pointer row when options exist); Note; Send; then Context. At 24 rows (6 body rows) the title, all options of a 3-option item and Note are in the first viewport.
3. Nothing pre-picked. A note with no pick is sent as a free reply (`submitAnswer` unchanged). Nothing picked and nothing typed shows the existing notice.
4. Details page: whole body, PageDown scroll, `b` hotkey back to Decide, pick and note kept.
5. Read item: `Mark read (m)` on row 1, a second Mark read at the end; short tier folds with Details.
6. Handled item: state lines first, then answer, options with `●`, Context with Details.
7. Body: inline code chips without padding spaces; blank row above headings in the tall tier only.
8. Title rule P6: 80-char stored title whose full text starts the body shows the first body line as title and drops it from the body.
9. Heights come from `scroll.bodyRows`; `rowsFor` unchanged; ADR 0007 consequence lines amended as item.md section 12 says.
10. Pick/send paths into the CLI (argv, stdin, V-26 tests) unchanged; old tests that expect Select, pointer row, show-all, `Options` heading are updated.
11. Evidence: real-pane captures (`claude plugin test`, fixtures) at 24 and 40 rows and 80/60/47 columns for E1 (answer), R2 (read), a handled item; saved with `![](img/...)` or text blocks in `issues/01-item-view-redesign/evidence.md` (EVID-1). Targeted tests green.

## Design notes
(Developer writes here before building: files, approach, risks.)
