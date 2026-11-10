# 09: One check table per ticket
Status: blocked (waits for tickets 02 and 04; Tech Lead added first, SIZE-13)
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: after wave 2
Files: `templates/squad/process/review.md` + `evidence.md`, `$SQUAD_DIR/process.local.md` (SQ-2; Manager edits, WHO-6), a small checker in `bin/squad-evidence` or new, tests
Source: idea 2.

## Business AC
1. One table per ticket (`NN/checks.md`): rows = AC; columns = Dev test or capture (a command), QA whitebox check, QA blackbox check. Each role fills only its own column. Columns name commands, not code (SAFE-10).
2. It replaces the SQ-2 trace; `## Review` points at the table. `squad-evidence check` fails on an empty Dev cell.
3. SQ-2 text in the overlay is removed in the same change (log in `process-log.md`).
4. Tests: empty cell fails; full table passes.
