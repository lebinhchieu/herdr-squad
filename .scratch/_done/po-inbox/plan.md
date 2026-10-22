# po-inbox plan (Tech Lead, size M)

**Ready now, in parallel, no shared files: PI-01, PI-03, PI-05. PI-02 follows PI-01 (same Developer). PI-04 waits for the Designer's final design and PI-03. PI-06 waits for PI-01. PI-07 integrates. PI-08 promotes.** Design: `design.md`. Tickets: `issues/`.

| Task | What | Blocked by | Files (no overlap with a parallel task) | UI | State |
|---|---|---|---|---|---|
| PI-01 | CLI read side: add, list, read, sync, escalation projection | none | `bin/squad-inbox`, `bin/squadinbox.py`, `tests/test_squadinbox.py`, `tests/fixtures/inbox/` | no | ready |
| PI-02 | CLI answer side: answer, withdraw, delivered, Answer-cell writer | PI-01 | same CLI files, `tests/test_squadinbox_answer.py` | no | queued behind PI-01 |
| PI-03 | Mod core: scaffold, spikes S1 S2 S4, polling, delivery, `/inbox` | none | `hooks/`, `types/`, `.claude-plugin/plugin.json`, `tests/test_po_inbox_mod.py`, `tests/test_hooks_json.py` | no | ready |
| PI-04 | UI: band, pane, collapsed tool row | PI-03, design final, spike S3 | `hooks/po-inbox/ui.tsx`, `ui.test.ts` | **yes** (`Design: ui-design/PI-04.md`) | design final; waits for PI-03 |
| PI-05 | `agents/manager.md` instructions | none | `agents/manager.md`, `tests/test_instructions.py` | no | ready; **PO approves the wording** |
| PI-06 | `squad-close` refuses while answer items are open (droppable) | PI-01 | `bin/squad-close`, `tests/test_squad_close.py` | no | queued |
| PI-07 | Integration: merge, contract test, full suite `--tz`, live drive | PI-01..06 | merges, `plugin.json` version, `tests/test_po_inbox_contract.py` | no | blocked |
| PI-08 | Promotion: CONTEXT.md, ADR 0007 | PI-07 | `CONTEXT.md`, `docs/adr/` | no | blocked |

## Order and Developers (cap 3)
1. Start PI-01, PI-03, PI-05 (three Developers). The same Developer takes PI-02 after PI-01, then PI-06 (no respawn).
2. Spawn the Designer now; PI-04 starts when `ui-design/PI-04.md` is `Status: final` and PI-03 has passed QA whitebox (its sha is the base).
3. PI-07 on the last passed sha; PI-08 last.

## Checkers
Each ticket: QA whitebox on the technical AC in the ticket, QA blackbox on the business AC (B-numbers in the ticket). Contract between CLI and mod: `design.md` → The contract; PI-07 AC2 pins both sides. Live checks need the stand-in Manager of `design.md` → Driving the mod.

## Size check
Eight tickets against the M guide of 3 to 6: five are build tickets, one is droppable, one integration, one promotion. One repo, no risk flag, no data migration (additive). Stay M. If the Manager wants fewer, merge PI-01 and PI-02.
