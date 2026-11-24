# Task 11: Worktree reuse rule (SPAWN-5a)

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (this scope's own rule; the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`.

Status: handed in
Source: Chieu E11 (approve): sequential tasks of a scope reuse one Developer worktree; clean merged worktrees (the Manager did the cleaning).
Files: templates/squad/process/spawning.md, tests that quote SPAWN-5a or its text (find with grep)
Ticket: commit this file's content as `.scratch/process-fixes/issues/11-worktree-reuse.md` in your first commit.
Base: `squad/plugin/qa-shots-first/plugin-dev-qsf-09` (8bbfb57; your worktree already starts there). No merge.

## AC
- AC1 SPAWN-5a (Manager plans) says: a Developer's next task in the same scope, with no parallel task running, reuses the previous Developer's worktree: `squad-spawn dev <name> --scope <scope> --repo <repo> --worktree <previous worktree>` (same branch). Only a task that runs in parallel gets a new worktree. At most 3 added lines.
- AC2 SPAWN-5b (Team Lead plans) says the same, in the same words where possible.
- AC3 Check that `squad-spawn --worktree` really accepts a dev role this way (read `bin/squad-spawn` usage lines 24-25, 68; run `squad-spawn --help`); if it does not, `BLOCKED 11`.
- AC4 Touched tests plus grep hits pass.
