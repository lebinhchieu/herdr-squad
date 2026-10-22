Status: done
Blocked by: 07
Task ID: PI-08
Files touched: `CONTEXT.md`, `docs/adr/0007-inbox-sits-on-escalations.md` (new), `.scratch/po-inbox/` status lines

# PI-08: promotion: glossary and ADR

**Done when the lasting facts of `$SCOPE_DIR/promote.md` are in `CONTEXT.md` and `docs/adr/`.** Follow `project.md`: use the `/domain-modeling` skill; do not hand-edit CONTEXT.md or an ADR without it. Wording is in `promote.md` (exact text).

## Technical AC
1. `CONTEXT.md` has **Inbox**, **Item** (read item, answer item) and the changed **Escalation**, with `_Avoid_` lines, in the file's style; its Relationships list gains the inbox-escalation line.
2. `docs/adr/0007-inbox-sits-on-escalations.md` has Status, decision, why, consequences, the rejected alternatives (replace, separate), in the ADR style of 0001–0006.
3. A grep for each of the glossary terms in `agents/*.md` finds no contradiction; `tests/test_instructions.py` green; suite green with a receipt.

4. **Added (QAB after PI-07 PASS):** three phrases in the `agents/manager.md` Inbox bullets, pinned like the AC9 phrase in the test that pins it: (M1) one `squad-inbox add` per Bash call (a compound call with two heredocs shows the first body in ctrl+o); (M2) chat carries only the printed line, no recommendation or body restated; (M3) run `squad-inbox list` before recording a chat answer, to get the id. The Manager shows the PO these phrases with the rest of the wording (PO approval, role instructions).
5. ADR 0007 Consequences gets one more bullet: the engine's permission dialog shows the full `squad-inbox add` command including the body unless `squad-inbox add *` is pre-allowed in the Manager's settings (a PO choice, not set by the plugin).
