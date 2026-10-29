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
(Developer, 2026-10-29)
- core.ts: `heightTier(bodyRows)` -> short (<=8) | tall (>=9).
- markup.ts: `itemTitle(body,title)` + `bodyBlocks` apply the P6 rule (80-char title, first line starts with it).
- draw.tsx: chips without padding; `drawBody` plan gets `tall` (blank row above headings) and returns `hiddenRows`; `drawOptions` becomes pickable `○/●` Button rows (`optionRows`).
- ui.tsx: `itemScreen` rebuilt as an ordered list of row segments; the hint is computed from where Note/Send/Context end vs `bodyRows`. Row 1 layout drops: hint, `blocks` clip, age, header to row 2.
- actions.ts/types: only the rename `expanded` -> `detail` (agreed with QA whitebox, T12).
- Choices: header = `id · [kind if not answer] · blocks X · age` for all item types; cut title with body fully shown: Details button on the last row; read item short tier folds at FLOOR_READ rows, tall tier shows all; second Mark read always drawn.
- Risk: Button with a two-row child in the tall tier (checked on a real pane).

## Technical AC (QA whitebox, proposed 2026-10-29; Developer: object by `ASK 01` or accept by copying this section into the ticket on your branch)
T1. **Tier helper.** `core.ts` exports one pure function mapping `bodyRows` to `short` (`<= 8`) or `tall` (`>= 9`). Unit test at 0, 6, 8, 9, 11, 33. No other height constant derived from terminal rows; every layout test mounts with `bodyRows` 6, 11 and 33 (and 8/9 for the boundary), never a fixed terminal size.
T2. **First viewport is asserted.** At `bodyRows` 6, a 3-option item: rows 0-5 hold, in order, Back+header, title, three option rows, Note. At 11: same plus Send. Assert text and order only; no colour or glyph-colour asserts (REV-18a belongs to QA blackbox).
T3. **Hint.** Table test for the computed hint at scroll 0: `↓ note, send`, `↓ send`, `↓ context`, `↓ more below`, none. One case per branch.
T4. **Each AC 2-8 has a test at both tiers.** AC3: no pick + note sends `{id, text}` via `submitAnswer`; no pick and no note shows the existing notice and runs nothing. AC4: PageDown on Details; `b` returns to Decide with pick and note intact.
T5. **Hotkeys vs Input.** On the Decide page, typing `b`, `m` and digits in Note must not navigate or act (test types them). `b` works only on Details; `m` works on a read item and a handled item has no Mark read.
T6. **State table.** One test per row of item.md section 8: sending (option and Send presses ignored), send failed (pick and note stay), item changed while open, `cell-not-written`, 1 option, 6+ options (PageDown reaches Note and Send), very long option (short 1 row, tall 2 rows, `…`), no body (no Context, no Details), no recommendation, `--rec` with no key, `--rec` naming a key not in options, unparseable options (3-row clip in short tier), 3+ row title, free-text item.
T7. **Row counts agree with the drawing.** Each drawn node reports `rows` from `rowsFor`; fold text `… N more rows` is N = hidden rows exactly (test with a body that has headings in tall tier, so blank rows are counted). Titles and options with wide characters (CJK, emoji) at 80, 60, 47 columns never exceed their row cap. `rowsFor`, `cellWidth` and `clipRows` bodies are unchanged (`git diff` shows no edit in them).
T8. **Title rule P6** (`markup.test.ts`): 80-char title + body first line starting with it → line becomes the title and leaves the body; title shorter than 80 and equal first line → old behaviour; 80-char title, first line does not start with it → untouched; body is that single line → body empty, no Context; CRLF body; leading blank line. The existing equal-line test stays.
T9. **Chips and headings.** Code span draws exactly its text, no padding (assert the span string, not its colour); table cells and code blocks unchanged. Blank row above a heading: tall tier only, never above the first block, counted in `rows`.
T10. **Narrow drop order** (section 13): test at a width where each step triggers, in order hint, `blocks …`, age, header to row 2. Back and Mark read are present in every case.
T11. **Dead code gone.** `Select` import, the top `pointer()` use when options exist, `showAll`/`show-all` key, `ui.expanded` for items: removed, not left unused (`grep` clean). List `more` expansion still works. No `.skip`, `.todo` or deleted test without a replacement; the old tests listed in the ticket (AC 10) are updated, not dropped.
T12. **Contract unchanged.** `actions.ts` has no diff; V-26 tests and the argv/stdin tests pass untouched. `listScreen` and `doneScreen` are byte-identical to main. No new dependency, no new file outside the Touches list, evidence and `.scratch/po-inbox-tui/`.
T13. **Real samples** (REV-4). The Developer's captures include the idle/constant cases: handled item, item with no body, and a read item; plus E1 and R2 at 24 and 40 rows and 80/60/47 columns. QA whitebox repeats one live run read-only.
T14. **ADR 0007.** Only the two lines named in item.md section 12 change; the rest of the file is byte-identical. If a glossary term is added (for example Details page), name it in `evidence.md` so `promote.md` can carry it.
T15. **Receipt of the grep rule.** `evidence.md` lists the `grep -rl` command, its hits, and that every hit was run and green. Full suite is mine, on the final sha.
