# Task 15: COST-8 says the Manager reads the line column

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Source of the change: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. No version bump in this task (it rides the last task of the goal's last scope, SQ-5).

Status: ready-for-agent
Source: finding 2 of the review. The Manager's Stop hook skips it, so it reads its line itself.
Files: templates/squad/process/cost.md (COST-8 only), tests that quote COST-8 (grep `tests/` for `COST-8`)
Ticket: commit this file's content as `.scratch/process-fixes/issues/15-cost8-line-column.md` in your first commit.
Base: your worktree after task 14. No merge.

## AC
- AC1 COST-8 tells the Manager to read the `line` column of its `squad-usage` row and to act when `last ctx` passes it. At most 2 added lines; keep every other COST-8 sentence.
- AC2 `squad-process lint` passes; tests that quote COST-8 or the whole of cost.md pass.

- T1-T6 agreed with QA whitebox (evidence/15/qa-w.md).

## Design notes
- One new paragraph in COST-8 (a separate paragraph keeps the 60-word lint per paragraph). It uses the column names `line` and `last ctx` that task 14 prints and adds no number. COST-8b and every other rule are untouched.
