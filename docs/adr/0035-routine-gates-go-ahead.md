# 0035: Routine gates go ahead with a notice

Status: accepted. Changes how the Manager uses ITER-4 for two gates; ITER-5 (merge, push, deploy) is unchanged.

## Context
On guardian `clarify` (22-23 Oct), 8 of 24 inbox items were yes-questions Chieu always answered yes: "passed: confirm close" (6), "start the next scope" (2).

## Decision
- ITER-19 lists the routine gates: close a passed scope with 0 open findings; start the next scope already in the agreed plan. They go ahead, and the Manager sends one `read` item with `[info] <scope> closed; say undo` (or `started`).
- The full `--tz` suite is asked non-blockingly: the item has no `--blocks`, the work goes on and the scope may close before the answer.
- Merge, push, deploy and any team, plan or scope change still ask, as before.
- Undo is the Manager's, on Chieu's word "undo" in chat: a close moves `scopes/_done/<scope>` back and respawns what is needed; the notice says what `squad-close` removed and undo does not bring back (worktrees).
- With `away` set nothing here changes ([ITER-17]).
- Rejected: ask every time (status quo, the 8 items); a per-project switch (more settings for two gates).

## Consequences
- A close or a start can be wrong once before Chieu sees it; the notice and undo bound the cost.
- Check-in and merge items carry `[warn] full suite: not answered` while the answer is missing.
