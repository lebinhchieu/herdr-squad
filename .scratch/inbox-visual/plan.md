# inbox-visual plan (Tech Lead, size M)

**Ready now, in parallel, no shared files: IV-01 and IV-02 (pure code, no design needed). UI tickets IV-03 (item screen), IV-04 (list and band), IV-05 (done list, droppable) start when their `ui-design/IV-0n.md` is `Status: final` and IV-02 has passed QA whitebox. IV-06 integrates, IV-07 promotes.** Design: `design.md`. Tickets: `issues/`. Fixtures: `hooks/po-inbox/fixtures/visual.ts` (IV-01).

| Task | What | Blocked by | Files | UI | State |
|---|---|---|---|---|---|
| IV-01 | Markdown-subset parser | none | `markup.ts`, `markup.test.ts`, `fixtures/visual.ts` | no | ready |
| IV-02 | Pure helpers (rec key, widths, table layout, cap, tones), `testkit.ts`, `InboxUi.more` | none | `core.ts`, `core.test.ts`, `testkit.ts`, `actions.ts` (2 spots), `types/index.d.ts` | no | ready |
| IV-03 | Item screen | IV-01, IV-02, design final | `ui.tsx` (item functions), `draw.tsx`, `item.test.ts` | **yes** (`ui-design/IV-03.md`) | waits for design |
| IV-04 | List and band | IV-02, design final | `ui.tsx` (band, list), `list.test.ts` | **yes** (`ui-design/IV-04.md`) | waits for design |
| IV-05 | Done list (droppable) | IV-02, design final | `ui.tsx` (`doneScreen`), `done.test.ts` | **yes** (`ui-design/IV-05.md`) | waits for design |
| IV-06 | Integration, full suite `--tz`, live drive | IV-01..05 | merges, `plugin.json` | no | blocked |
| IV-07 | Promotion | IV-06 | `CONTEXT.md`, `docs/adr/` | no | blocked |

## Order and Developers (cap 3)
1. Start IV-01 and IV-02 now (two Developers). Spawn the Designer now: it designs IV-03 first (the V-01 bar at 40x24 with E1 is the hard part), then IV-04, then IV-05.
2. IV-03 and IV-04 run in parallel on `ui.tsx` (different functions, git merges cleanly; each has its own test file). A third Developer takes IV-05 after IV-04, or IV-05 is dropped.
3. Base for IV-03..05: the last sha that passed QA whitebox for IV-01 and IV-02 (merge both).
4. IV-06 on the last passed sha, IV-07 last.

## Checkers
QA whitebox on each ticket's technical AC (`design.md` common AC + the ticket's). QA blackbox on the business AC V-nn named in the ticket; baseline captures of today's build before the first hand-in (BA condition 3). V-01 at 40x24 is checked by QA blackbox in a real pane; a miss is FAIL.

## Size check
Seven tickets: two pure builds, three UI (one droppable), integration, promotion. One repo, no risk flag, no migration. Stay M.

## Risks
- V-01 v3.2: the first viewport is 6 content rows at 24 terminal rows (QAW live read) (host-set, the mod cannot raise it); the Designer must show the top block (back, kind + blocks, title, rec pointer) fits 7 rows at 40 columns and how the PO sees "more below", before IV-03 starts; options without borders at narrow width.
- Row estimates (`rowsFor`) differ from the terminal's wrap: QA blackbox checks in a real pane.
- Button colour (`variant="primary"`) may carry a meaning colour: the Designer confirms with a pane read in `--format ansi`.

## Follow-ups for the last droppable ticket (Tech Lead, 2026-10-16)
- F1 (QAB, IV-04): at 30 columns the band with four kinds wraps between a count and its word (`12 answer 3 read 1` / `problem`). Keep each number with its word on every rung; below the 40-column reference, so not a return. Candidate for IV-05's slot or a small IV-08 if the PO wants it.
- F2 (QAW, IV-03): the `fitCap` floor and the notice cap differ only below `bodyRows` 5; no test pins it. Droppable.
