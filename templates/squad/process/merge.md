# Merging

## MRG-1 Merge only on the PO's request
roles: manager
topic: merge

- Only the Manager merges into the PO's branch, and only when the PO asks in the Manager's own session, for a named branch or scope. A passed branch, a green suite or an approved check-in is not a request.
- Do not offer to merge in place of asking the PO: name the branch or sha (checked) and let them say so.
- Take each task's passed sha and checkers from `iterations/<n>.summary.md` or the task files, never from messages.
- Merge only what the PO names, into the branch checked out in the project root; never switch branches.
- Run `squad-merge-check <branch>` first; it prints the merge rules.

## MRG-6 Main moved before the merge
roles: manager
topic: merge
phase: merge

Before [MRG-2]: `git merge-base --is-ancestor main <sha>` true needs no check. Else compare `git diff --name-only <base> main` with `... <base> <sha>` (`base` = `git merge-base main <sha>`). No shared file and no shared `grep -rl` test hit: merge, note "main moved, N files, none related" ([MRG-4]).

## MRG-6b Main moved, related changes
roles: manager
aware: team-lead, qa-whitebox
topic: merge
phase: merge

Related changes: ask the Team Lead for a Developer to merge `main` into the branch, run the shared tests and hand in ([REV-14a]); a conflict goes to the Developer ([MRG-3]). Then merge.

## MRG-2 Before the merge
roles: manager
topic: merge
phase: merge

Check the target as in [GOAL-7] and that both checkers passed the sha, or the evidence sha after it (a later sha whose diff to the passed sha touches only a ticket's `<stem>/evidence.md` and `img/`, as `squad-evidence check --base` shows). Refuse, with the reason, if the project root has uncommitted changes or the sha is neither. Use `git merge --no-ff`.

## MRG-3 Conflict or failure
roles: manager
topic: merge
phase: merge

`git merge --abort`, then tell the PO the files in conflict. The Manager never resolves a conflict itself; it uses `--force`, `rebase`, `reset --hard` or `push` only as [SAFE-1b] allows.

## MRG-4 After the merge
roles: manager
topic: merge
phase: merge

Quote `git log --oneline -1` and the result to the PO; note it in the iteration file. The hook records `merged`; for a ticket it did not record, run `squad-task merged NN`.

## MRG-5 Untracked files before the merge
roles: manager
topic: merge
phase: merge

Before a merge, run `git status --porcelain --untracked-files=all` in the project root and tell the PO about every untracked file outside `.claude/squads/` (a draft that was written there, [FILE-11]); `squad-close --scope` prints the same list.
