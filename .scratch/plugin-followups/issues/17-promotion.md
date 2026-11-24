# 17 Promotion: ADR 0036 and what must outlive the scope

Status: ready-for-agent

Spec: none
Blocked by: 16
Aim: Record the task-id and evidence rules in the project docs
Estimate: 1h
Depends on: 16

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/17.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Same worktree as 16. Commit `$SCOPE_DIR/promote.md` into the project docs: ADR 0036 (task-id grammar; evidence-only rule; no-QA checkers by `team:` tokens); check the number is free on main and on every squad branch first; check the rest of `promote.md` is already in the tree.
Files: `docs/adr/0036-*.md`, `CONTEXT.md` (only if `promote.md` names a term), `tests/test_instructions.py`

## Problem
Iteration 3 decides three things later work builds on: one task-id grammar (`digits | integration | promotion`, rule ids never task events), one evidence-only rule (`<stem>/` or `<stem>.evidence/` with the ticket file present), and no-QA scopes judged by `team:` tokens. They are in tickets and the plan, which close with the scope.

## AC
- AC1: `docs/adr/0036-<slug>.md` exists in the repo's ADR form, states the three decisions with their Why, and its number is unused on main and on every squad branch (`git ls-tree` quoted).
- AC2: nothing in `promote.md` is left out of the tree (each item with the file it went to).
- AC3: if `promote.md` has no glossary term, `CONTEXT.md` is untouched.
- AC4: `test_instructions` and the other two whole-repo files pass.

## Comments
