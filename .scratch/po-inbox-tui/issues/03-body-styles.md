# Task 03: Body styles in the pane (callout, diagram, badges, links)

Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=dev, business-ac=ticket, code-check=dev (self-review, Manager confirms), behaviour-check=dev evidence (Manager confirms), handin-target=manager, suite-owner=qa-white (at the end only), promote-owner=dev, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Team: no QA (PO decision 2026-10-29). Branch from the passed sha of task 01 (it also edits `draw.tsx` and `markup.ts`). Runs in parallel with 02 (no `ui.tsx`). Hand in to the Manager. `BLOCKED 03` on a risk flag or doubt.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`. Spec: `.scratch/po-inbox-tui/spec.md`.
Design: ui-design/body-styles.md (sections 1-9; 9 is the colour and relationships addendum; picture `ui-design/body-styles-colour.html`)
Depends: 01.

## What
Build `ui-design/body-styles.md` (Status: final), sections 1-5, 7 and 9 (build order: P1 callouts and diagram with relationships, P2 badges, P3 URL links): callout lines `[decision] [warning] [info]` (P1), the `diagram` code block that stays aligned and is never wrapped (P1), badges `[ok] [fail] [warn] [skip]` (P2), links `[label](url)` and bare URLs drawn as `label <url>` (P2). Section 9: highlights are filled chips (`inverse` + theme `color`, short label only, never a whole line); diagram connectors drawn `permission` blue, names plain, optional tags as chips, auto legend row. Plus the table rule in section 8: aligned columns at `cols >= 40` (was 60), so a docked pane (~47 cols) keeps table shape. Anything the parser does not know stays plain text (never drop a word).

## Touches (confirmed before AC)
`hooks/po-inbox/core.ts` (`ACCENT`, `QUIET`, pure `chipProps`, `diagramRuns`, `legendTags`; section 9.8), `core.test.ts`, `hooks/po-inbox/markup.ts` (`Span` link/badge, `Block` callout, `parseInline`, `parseBody`, `spansText`/`plainOf`), `draw.tsx` (`drawBlock`, `drawSpans`, `drawCode` diagram path, `drawTable` per-cell Text and the `tableLayout` threshold, `spansText`/`drawnText`/`plainText`), `markup.test.ts`, `core-visual.test.ts`, `item.test.ts` goldens that draw a body, `fixtures/visual.ts`. `item.test.ts` line 838 colour allow-list gains `permission` and `inactive`. Not touched: `ui.tsx`, `testkit.ts`, `rowsFor`, the band, the CLI, `list --json`. No new dependency.
Run `grep -rl '<changed string>' tests/ hooks/po-inbox/` before HANDIN and run every hit (CLAUDE.md); the V-22 table tests change with the threshold.

## AC
1. Built UI matches the design: every form, tone, short and tall drawing, fallback and state (sections 3-5).
2. Callouts: exact tags only (`[decision]`, `[warning]`, `[info]`) drawn as `◆ decision:` bold, `⚠ warning:` amber, `› info:` dim; near-miss tags stay plain text.
3. Diagram block: no `│` gutter, never wrapped; too wide is cut with `›` and a footer row; fits whole otherwise.
4. Badges (`[ok] [fail] [warn] [skip]`) keep their colour inside table cells; links drawn `label <url>`, bare URLs recognised, no OSC 8 escapes.
5. Parse is linear on hostile input (5,000 `[`, 10,000 chars) and `plainOf` keeps every word on all fixtures.
6. `tableLayout` aligns columns at `cols >= 40`; the existing fit test still guards overflow; V-22 tests updated.
7. Section 9: chips use the exact props of 9.1; connectors `{ color: 'permission' }`; no `backgroundColor` anywhere; legend row only when a tag exists; `diagramRuns` widths sum to the input and stay linear on a 10,000-char line (9.8 tests).
8. Fixtures: the two example bodies of section 6 (E1 answer item, R1 check-in), `diagramWide`, `tags`, `links`, `badges`, `relations`, `chips`; they parse and draw as the design shows.
9. Evidence: real-pane captures (`claude plugin test`, fixtures) at 24 and 40 rows and 80/60/47 columns for both example bodies and the wide diagram, and on a dark AND a light theme at 80 and 47 columns for a callout, a badge table and the relations diagram (section 9.5); in `issues/03-body-styles/evidence.md`. Targeted tests green.

## Design notes
Written before building (dev 3). Section numbers are `ui-design/body-styles.md`.
- **core.ts (pure):** `ACCENT='permission'`, `QUIET='inactive'` (not in `TONE`, its test stays exact). `CHIPS` maps each badge/callout word to `{tone, glyph}`; `chipText(word)` gives U+00A0 + glyph + U+00A0 + word + U+00A0; `chipProps(tone)` gives `{inverse, bold, color}` (9.1). `diagramRuns(line)`: one pass, flags connector chars (box U+2500-257F, arrows U+2190-21FF and `▲►▼◄`, runs of 2+ `-`/`=`, `->`, then `>` after a connector and `<` before one), then tags (`[ok]` etc. only when alone between spaces or line edges); runs are merged by kind, widths sum to the input. `legendTags(lines)` returns present tags in order ok, warn, fail, skip. `tableLayout` threshold 60 -> 40.
- **markup.ts:** `Span` + `link {text,url}` (empty text = bare url), `badge`; `Block` + `callout {tone,spans,indent?}`. `parseInline` finds `[` and `http(s)://` with cached `indexOf` (same trick as `**`/backtick): `]`, `(`, `)`, space and the next `[` are each searched from a monotone position, so 5,000 `[` stay linear. A label may not hold `[` or `]`; the url must start with `http://` or `https://`, hold no space, and close with `)` before the next space. Anything else keeps its characters as text. `parseBody` reads the three callout tags next to `[rec]` (same rule: tag + space or end). `spansText`/`plainOf`: link = `label url` (or url), badge = word, callout = spans only. `spansText` is exported so `draw.tsx` stops keeping a copy.
- **draw.tsx:** `drawnText` counts chips and `label <url>`. `drawSpans`: link (label underlined + dim `<url>`; bare url underlined), badge chip. Callout = one wrapping `Text`: pad, chip, space, spans (`bold` for decision); rows = `rowsFor` of the same string. Table: widths from `drawnText`; aligned rows are one `Text` per row holding per-cell spans plus pad strings; stacked records draw the value spans. `isDiagram(b)` (lang word `diagram` or any box-drawing char); diagram path: 2-space indent, tabs to 4 spaces, trailing spaces trimmed, never wrapped; wider than `W=cols-2` -> lines over `W` are cut to `W-1` + `›`, footer row; caption dim italic; runs from `diagramRuns` on the drawn (cut) text; legend rows packed greedily so each part is exactly one row (the first-block row clip counts parts).
- **Tests:** `core.test.ts` (diagramRuns, chipProps), `markup.test.ts` (tags, links, badges, linear, oracle skips the callout tag word), `core-visual.test.ts` (threshold, chips, connectors, no `backgroundColor`, legend, rows at 80/47), `item.test.ts` allow-list + a body golden, new fixtures (`guideE1`, `guideR1`, `diagramWide`, `tags`, `links`, `badges`, `relations`, `chips`).
- **Open choices made:** the badge/callout chip glyph table is in `core.ts` so tests and draw share one source; a non-`diagram` fence with a box character shows its language word as the dim caption (no word lost).

## Verification (no QA)
Before HANDIN: (1) run the `mattpocock-skills:code-review` skill on your branch since its base and fix every finding it confirms; (2) write `## Review` in this file: findings, what you fixed, what you left and why; (3) run only the test files you touched plus the `grep -rl` hits (CLAUDE.md); do NOT run the full suite (PO: full suite only once, at the end, by QA whitebox on the final integrated sha); (4) save real-pane evidence per the AC in `evidence.md` and check it with `squad-evidence check`. HANDIN names the branch, sha, evidence sha and the `## Review` path. The Manager confirms; no QA runs.

## Review
Skill `mattpocock-skills:code-review`, since base `4a818d6`, two sub-agents (Standards, Spec). No hard violation on either axis. Findings and what I did:

| # | Axis | Finding | Action |
|---|---|---|---|
| 1 | Standards | `draw.tsx` header said colour is `TONE` or weight only | Fixed: comment names `ACCENT`, `QUIET` and 9.5 |
| 2 | Standards | `/^diagram(\s\|$)/` twice, magic `slice(7)` | Fixed: one `DIAGRAM_LANG` |
| 3 | Standards | `BadgeWord` and `DiagramTag` were two lists of one vocabulary | Fixed: `DIAGRAM_TAGS` in `core.ts`; `markup.ts` reuses it |
| 4 | Standards | A test named "permission only on chips and connectors" did not assert that | Fixed: renamed to what it checks |
| 5 | Standards | Legend row packing sits inline in `drawDiagram`; `lay.rows` of `tableLayout` unused by `drawTable`; `findOpen`/`findNextOpen` and the two space finders duplicate a call | Left: each is small, tested through the drawn output, and the finders must be separate (a finder only moves forward; the comment says so) |
| 6 | Spec | A caption longer than 2 rows ended in `…` (words lost) | Fixed: caption wraps whole; test added |
| 7 | Spec | A whole tag ending exactly at the cut lost its chip (`[ok]›`) | Fixed: tags are read on the typed line, then the runs are cut; a cut tag is plain, a whole one keeps its chip; test added |
| 8 | Spec | `-->>` coloured both `>` | Fixed: one `>` after a connector run, one `<` before it; test added |
| 9 | Spec | Legend can use several rows when it does not fit (spec says one row) | Left: at 47 columns the four entries need 66 cells; one row would drop words. Each part is one row, so the row count stays exact |
| 10 | Spec | `drawTable` draws one `Text` per row with per-cell spans, not one `Text` per cell | Left: same text, same colours, same widths; tests read the drawn cells |
| 11 | Spec | Not asked for: a bare url after a letter stays text (`xhttp://a.b`); a link label may not hold `[`; `parseInline` now uses cached finders; a non-`diagram` fence with a box character shows its language word as caption | Left: each keeps the parser total and linear, or keeps a word on screen; all are in the design notes and tests |
| 12 | Spec | Ticket AC2 still says `◆ decision:` with a colon | Left: section 9 wins (filled chip, no colon); the AC text is stale, the Manager may edit it |

Tests: `claude plugin test .` (the mod suite only, 585 pass, 0 fail) plus `tests/test_promotion_0_6_0.py` and `tests/test_old_language_inventory.py` (the `grep -rl` hits). Also run: `tests/test_po_inbox_mod.py` (validate + plugin test, 585 pass), `tests/test_squadinbox.py`, `tests/test_processlint.py`, `tests/test_squadreport_embed.py`, `tests/test_manager_m_l.py` (hits of `markup` and `stacked`, unrelated words): all pass. Full suite not run (PO rule).

Differences from the final design that the Manager should rule on (LC-19b): legend may use several rows (design: one row; rows 9); caption wraps whole (design: one row; row 6); `drawTable` one `Text` per row, not per cell (row 10); a non-`diagram` fence with a box character shows its language word as caption (row 11); ticket AC2 still says `◆ decision:` with a colon (row 12).
