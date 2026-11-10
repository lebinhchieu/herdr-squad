# 05: `squad-review-pack`, one review file per HANDIN
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Cite: [REV-15] report deliverable: copy it to `$SCOPE_DIR/evidence/<task>/` at the sha handed in.
Lane: A (after 04)
Files: new `bin/squad-review-pack`, new test file; evidence path rule in `templates/squad/process/review.md` only if needed (REV-15 copy for QA blackbox)
Source: idea 6. QA blackbox must stay blind to code (SAFE-10).

## Business AC
1. `squad-review-pack NN [--sha S]` writes `$SCOPE_DIR/evidence/NN/pack.md`: the task's AC, `git diff --stat` of the task base..sha, the changed hunks (capped, with a note when capped), test commands from the task file, the evidence path.
2. A second file `pack-blackbox.md` has the AC, behaviour commands and evidence path and no code or diff.
3. It reads, never writes outside `evidence/NN/`. A missing task file gives a clear error and exit 2.
4. Tests: pack for a small fake task has all sections; blackbox pack contains no hunk lines.
