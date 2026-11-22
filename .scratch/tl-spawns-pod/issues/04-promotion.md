# 04 Promotion: ADR 0032 and the CONTEXT.md entries
Status: ready-for-agent
Duties: design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: docs/adr/0032-team-lead-spawns-the-pod.md (new), CONTEXT.md (Manager, Team Lead, Coordinator entries; Pod checked)
Depends: 03 (the ADR cites the final behaviour). Base: main at 8d74fcb. Source text: `$SCOPE_DIR/promote.md` (exact wording). Plan: `$SCOPE_DIR/iterations/1.md`.
Evidence: .scratch/tl-spawns-pod/issues/04-promotion/evidence.md

## What and why
PROMO-4: the scope's last task commits `promote.md` to the project docs. This change contradicts ADR 0010 ("the Team Lead spawns and retires Developers only, enforced by its settings") and a sentence of ADR 0030, so it needs an ADR that says so, plus the three CONTEXT.md entries that still say Developers only. Use the `/domain-modeling` skill and the project rule for editing these files (`project.md`).

## Business AC
- AC1 `docs/adr/0032-team-lead-spawns-the-pod.md` exists with the text of `promote.md` section 1 (Status, an `Amends 0010 and 0030` line, Decision, Why, Consequences, Alternatives rejected). `ls docs/adr | grep -c 0032` prints `1` (base: `0`).
- AC2 `CONTEXT.md`: `grep -n "spawns and retires only Developers\|spawns and retires the Developers\|spawns Developers," CONTEXT.md` has no hit (base: 3 hits at the Manager, Team Lead and Coordinator entries); the three entries carry the wording of `promote.md` section 2 and cite ADR 0032. The Pod entry is checked and left alone if it is right.

## Technical AC
- AC3 ADR 0010 and ADR 0030 are not edited (history stays); only 0032 says it amends them. `git diff --stat` for the ticket lists only `docs/adr/0032-...md`, `CONTEXT.md` and the evidence folder.
- AC4 The ADR states what is true after 01-03: `grep -n "squad-respawn" docs/adr/0032-team-lead-spawns-the-pod.md` is not empty, and its Consequences name the name-vs-row check and the pin-must-be-0.10.4-or-later step (the `/squad:squad-process-update` pin move and respawn). Nothing in it contradicts `bin/squad-spawn`, `bin/squad-retire` or `bin/squad-respawn` as merged (QA whitebox reads the three against the ADR).
- AC5 Run `tests/test_old_language_inventory.py` and every hit of `grep -rl "CONTEXT.md\|docs/adr" tests/`; quote the result. SQ-10 needs no run (no `bin/`, printed text or role text is edited).
- AC6 The ADR's Known-limit lines state the two limits of `promote.md` (second copy of a role, Architect before the plan); do not add claims that were not checked.

## Base dry-run (SQ-15, Tech Lead, main 8d74fcb)
- AC1 base: no ADR 0032 (count 0). AC2 base: 3 hits. `test_old_language_inventory` 2 ok on base; `grep -rl "CONTEXT.md\|docs/adr" tests/` has no hit, so no other test file needs a run.
- Known failing on base: none.

## Evidence
`evidence.md` next to the committed ticket. Run `squad-evidence check <evidence folder>` (no `--base`) before HANDIN and quote the exit code (SQ-18).
