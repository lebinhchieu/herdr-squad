# Task 13: GOAL-6b says the suite owner runs the full suite, with no ask

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (this scope's own rule; the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`.

Status: handed in
Source: QA whitebox follow-up on task 12; it contradicts the policy of task 12.
Files: templates/squad/process/goal.md (GOAL-6b only), tests that quote GOAL-6b or pin its byte budget (grep)
Ticket: commit this file's content as `.scratch/process-fixes/issues/13-goal-6b-ask.md` in your first commit.
Base: the head of this worktree (1fc0022). Reuse the worktree. No merge.

## AC
- AC1 GOAL-6b ends: the suite owner then follows [SUITE-1] (targeted by default, a full run only after Chieu's yes) instead of "runs the full suite after". Change that clause only; at most 1 line changed.
- AC2 `grep -rn 'full suite' templates/` shows no other rule that runs it without the ask (list the hits in `## Review`; fix only a real contradiction, else `BLOCKED 13`).
- AC3 Touched tests plus grep hits pass; pinned byte budgets updated if needed. No full suite.

## Review

See `13-goal-6b-ask/evidence.md` (AC trace first).
