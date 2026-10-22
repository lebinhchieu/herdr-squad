# T4 · other role files address the Team Lead in M and L
Status: ready-for-agent
Type: task
Blocked by: none
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches (and no others)
`agents/dev.md`, `agents/qa-whitebox.md`, `agents/qa-blackbox.md`, `agents/ba.md`, `agents/tech-lead.md`, `agents/designer.md`, `tests/test_pod_contact_routes.py` (new). Not `team-lead.md`, `manager.md`, `token-coach.md`.

## Do
- Every line containing "Manager" in these six files is either a legitimate path (an "Always goes to PO" item, a size change, a dispute outside plan and assignment, the fallback when the env is empty, "the Manager's briefing") or becomes "the Team Lead" in M and L (S keeps the Manager or Tech Lead). Examples: `dev.md` "tell the Team Lead and wait; the Manager will retire you" → "the Team Lead retires you (S: the Manager)"; Gaps "Plan or order → the Team Lead"; HANDIN copy line names the Team Lead (M, L). `qa-*`: PASS/FAIL copy the Team Lead (M, L). `tech-lead.md`: "In S and M you also own the plan" → S only; in M and L hand the plan and `## Handover` to the Team Lead; "Help the Team Lead plan (L)" → "(M, L)"; escalations still via the Manager. `ba.md`: "tell the Team Lead" for blocked work stays; escalate via the Manager only goal change, scope cut. `designer.md`: briefing sentence only.
- `squad-process show` fallback sentences and the `OUTSIDE_VIEW` lists in `tests/test_instructions.py` stay true: do not edit that test; do not add a `process.md →` citation outside a role's view.
- S text paths stay present: Tech Lead review (`tech-lead.md`), the Developer handing in to the Tech Lead in S.

## Technical AC
AC-4.2 to AC-4.6. `tests/test_pod_contact_routes.py`: for each of the six files, every line containing `Manager` is in an allow-list inside the test, so a future edit that re-adds a Manager route fails; pins the S paths.

## Business AC
B3, B12, B2 (role-file side), B6 (no routine Manager route).
