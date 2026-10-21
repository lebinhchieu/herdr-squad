# Merging

## MRG-1 Merge only on the PO's request
roles: manager
topic: merge

- Only the Manager merges into the PO's branch, and only when the PO asks in the Manager's own session, for a named branch or scope. A passed branch, a green suite or an approved check-in is not a request.
- Do not offer to merge in place of asking the PO: name the branch or sha (checked) and let them say so.
- Take each task's passed sha and checkers from `iterations/<n>.summary.md` or the task files, never from messages.
- Merge only what the PO names, into the branch checked out in the project root; never switch branches.

## MRG-2 Before the merge
roles: manager
topic: merge

Check the target as in [GOAL-7] and that both checkers passed the sha, or the evidence sha after it (a later sha whose diff to the passed sha touches only `*.evidence/` folders, as `squad-evidence check --base` shows). Refuse, with the reason, if the project root has uncommitted changes or the sha is neither. Use `git merge --no-ff`.

## MRG-3 Conflict or failure
roles: manager
topic: merge

`git merge --abort`, then tell the PO the files in conflict. The Manager never resolves a conflict and never uses `--force`, `rebase`, `reset --hard` or `push`.

## MRG-4 After the merge
roles: manager
topic: merge

Quote `git log --oneline -1` and the result to the PO; note it in the iteration file.
