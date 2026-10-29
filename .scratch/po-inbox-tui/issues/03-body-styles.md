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
(Developer writes here before building.)

## Verification (no QA)
Before HANDIN: (1) run the `mattpocock-skills:code-review` skill on your branch since its base and fix every finding it confirms; (2) write `## Review` in this file: findings, what you fixed, what you left and why; (3) run only the test files you touched plus the `grep -rl` hits (CLAUDE.md); do NOT run the full suite (PO: full suite only once, at the end, by QA whitebox on the final integrated sha); (4) save real-pane evidence per the AC in `evidence.md` and check it with `squad-evidence check`. HANDIN names the branch, sha, evidence sha and the `## Review` path. The Manager confirms; no QA runs.
