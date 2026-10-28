Status: done
Blocked by: none
Task ID: RB-04
Files touched: `CONTEXT.md`, `docs/adr/0001-*.md` .. `0004-*.md` (Status line only), `docs/adr/0009-board-removed.md` (new)

# RB-04: Promotion: CONTEXT.md and ADR 0009

**Done when the glossary and the ADRs say the board is gone, with exactly the wording in `$SCOPE_DIR/promote.md`.** This is the scope's promotion task (`process.md` → Promotion): copy the wording, do not reword it. Edit through `/domain-modeling` as `project.md` requires. Requirement: `spec.md` R-10, R-11, R-12.

## What to build
1. `CONTEXT.md`: apply `promote.md` items P1-P3 (delete the "Squad board" section; keep **Home** and **Receipt** under a heading that still exists; drop Bar, Status, Needs-you, Recorder, Replay).
2. `docs/adr/0009-board-removed.md`: item P4 verbatim, `Status: accepted (remove-board)`.
3. ADRs 0001-0004: item P5 (replace only the `Status:` line; the bodies stay as history).
4. ADR 0007 is **not** edited (BA R-11); 0009's Consequences carries the correction.
5. Not in this ticket: `project.md` rows (the Manager edits them, P6) and `README.md` (RB-02).

## Technical AC
1. `git diff --stat` shows only the files above; ADR 0001-0004 diffs are one line each.
2. Every relative link and every `docs/adr/NNNN-` name in `CONTEXT.md` and `docs/adr/*.md` resolves (`for` loop over the links, output in `dev-evidence.md`); no link points at a deleted file other than as a quoted path inside ADR 0001-0004 and 0009.
3. `git grep -niw board CONTEXT.md` is empty (the word does not appear in the file at all).
4. 0009 has the sections the other ADRs have (title, `Status:`, `**Decision:**`, `**Why:**`, `**Consequences:**`) and numbers 0009.
5. Glossary terms in the `PO inbox` and `Work` sections are unchanged (`git diff` shows no line there).

## Comments
