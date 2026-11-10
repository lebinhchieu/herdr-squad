# 0024: The check table lives in the scope's evidence folder and replaces the SQ-2 trace

Status: accepted

## Context
Each ticket needed a trace from every AC to the test or capture that proves it. The overlay rule SQ-2 asked for it in `## Review`, and a QA refused a `HANDIN` that lacked a line. QAs cannot write to the Developer's worktree (SAFE-4), so they could not add to a table kept there.

## Decision
- The working table is `$SCOPE_DIR/evidence/<NN>/checks.md`: one row per AC, columns Dev, QA whitebox and QA blackbox. Each role fills only its own column, with a command and its result, never code.
- After every checker passed, the Developer embeds it with `squad-evidence add --heading Checks`. It rides the existing evidence-only commit, so the merge check needs no new path.
- `squad-evidence checks <file>` checks the table (header, duplicate row ids, empty or `-` Dev cell). `squad-evidence checks --template` prints the empty table, so the Developer rule is one line. `squad-evidence check` requires every QA cell once `## Checks` is in `evidence.md`.
- With `tech-ac = dev` and a QA blackbox, the Developer assembles the evidence and the Manager accepts the commit (`when: tech-ac = dev and qa-black = yes`, no new fact key).
- The table replaces the overlay rule SQ-2. The Manager removes SQ-2 from `process.local.md` after the re-pin (WHO-6).

## Consequences
- Old evidence without `## Checks` passes unchanged.
- A cell that holds `|` breaks the row-width check (recorded as a follow-up).
- A table that names code in the QA blackbox column is a review finding, not a checker rule.
