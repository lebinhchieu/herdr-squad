Status: needs-triage
Type: task
Task ID: 10
Touches: decided when filled (test files and small fixes only; never product behaviour)
Harness: the test files each follow-up names
Blocked by: 01-09 passed

# 10: Batch of QA follow-ups (droppable)

**Done when every item listed below is fixed or the Team Lead drops the ticket.** `qa: light` (PO: internal tool, QA checks primary features): test-strength gaps from `qa-w.md` / `qa-b.md` marked "follow-up" (not a defect) are batched here by the Tech Lead after tickets 01-09 pass, then this ticket is issued with a file list, AC and harness. If the list is empty the ticket is dropped. Dropping it blocks nothing: 11 and 12 do not depend on its content.

## Items
(filled by the Tech Lead from `evidence/*/qa-w.md` follow-ups)
- 07: `--top 0` / negative silently falls back to 5: reject with exit 2 or honour it (query module + test).
- 07: `blocks` cap is per segment, not per agent sum (fine while 03 segments reconcile): add a test that pins it.
- 03: legacy alias task ids show as separate rows on old scopes (QAW, evidence/03/qa-w.md): merge or label them.
