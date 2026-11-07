# 0021: Task state is an event file in the squad folder, not lines in the ticket file

Status: accepted

## Context
The board showed a wrong stage, owner and last active, because state was read from one scope's `messages.jsonl` only and nothing recorded claim, passed or merged. A first plan wrote `Status:`, `Owner:`, `Branch:`, `Sha:` and `Updated:` lines into the ticket file.

A ticket file lives in three places: a gitignored draft in the scope folder, a copy in the Developer's worktree, and a tracked file in the main checkout (`.scratch/<slug>/issues/`) that the board reads. A hook that writes the tracked copy dirties the PO's `main`. A hook in a worktree writes a copy the board never reads.

## Decision
- Record facts as append-only events in `$SQUAD_DIR/task-events/<ticket folder slug>.jsonl` (gitignored with the squad folder). One writer module, `bin/squadtask.py`, behind the `squad-task` command and the hooks. Events: `claim`, `handin`, `pass`, `fail`, `blocked`, `decision`, `merged`. Format version `v: 1`; readers skip bad lines.
- Words (`todo`, `in progress`, `checking`, `returned`, `blocked`, `passed`, `merged`, `sha changed after PASS`) are derived at read time and never stored. The board folds the events and falls back to the ledger of every scope with the same ticket folder.
- No confirmer. A task is `passed` when every non-retired QA on the roster sent `PASS` for the current sha. A `PASS` from any other role is a warning and is not counted. A team with no QA has one slot, `evidence`, filled when the `HANDIN` hook runs `squad-evidence check` on the ticket's evidence folder and it exits 0 (no `--base`).
- `merged` is derived from git first (the recorded branch is reachable from `main`), then recorded by the Manager's Bash hook `bin/squad-merge-record`, then by hand with `squad-task merged NN`.
- The claim comes from `squad-spawn --task NN` (dev role only); `--task` is removed before the runtime is started.
- Gates warn, never block. Every hook and command exits 0; the warning goes back to the sender in `additionalContext` and is saved in the event's `warn`.
- After a task has passed, commits that touch only its evidence folder keep `passed` on the board; any other path shows `sha changed after PASS`.

## Consequences
- The ticket's `Status:` line stays a plan label that people write.
- State survives a scope close and is shared by every scope that uses one ticket folder.
- One more store to keep. A squad pinned to an older plugin writes no events; the board then shows ledger state as before.
- Reversible: delete the folder; nothing else reads it.
