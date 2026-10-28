# Closing

## CLOSE-1 Close a scope
roles: manager
topic: closing

- The PO confirms the close at a check-in. The Manager proposes it with evidence links once both checkers have passed every task, makes sure the promotion task passed ([PROMO-4]), and runs the Token Coach if [ITER-6] says so.
- It tells the PO which branches are unmerged, resolves or withdraws (`squad-inbox withdraw E<n> --reason "<why>"`) every open inbox item, tells the PO of any still unanswered, then runs `squad-close <squad> --scope <scope>` as its last action. After it the Manager is gone, so it says everything first.

## CLOSE-2 What squad-close does
roles: manager
topic: closing

`squad-close` retires the scope's agents (its Manager last), removes worktrees whose branch is merged and clean, reports every branch (never deletes one), moves the folder to `scopes/_done/` and closes the Manager's pane.

## CLOSE-3a Close in a goal, Tech Lead
roles: tech-lead
when: goal = yes
topic: closing

When your scope is passed, before the pod is retired: write `$GOAL_DIR/shared/summaries/<scope>.md` (outcome, passed branch and commit, open items; no decisions or domain facts) and append the goal-wide decisions to `$GOAL_DIR/shared/decisions.md`, one bullet each, keeping it under 80 lines.

## CLOSE-3b Close in a goal, goal Manager
roles: manager
when: goal = yes
topic: closing

With the PO's confirmation at an iteration check-in, update the `goal.md` table, run `squad-close <squad> --scope <scope>`, then update your notes and `squad-respawn $SQUAD_NAME`: a goal Manager resets after every scope close.

## CLOSE-4 Close a goal
roles: manager
when: goal = yes
topic: closing

A goal closes once every scope is closed and the promotion passed. Run the Token Coach ([ITER-6]), tell the PO which branches are unmerged, and run `squad-close <squad> --goal <goal>` last: it retires the goal Manager, closes its pane and moves the folder to `goals/_done/`; it refuses while a scope is open.

## CLOSE-5 Close a squad
roles: manager
topic: closing

`squad-close <squad>` archives everything, evidence included, to `.claude/squads/_done/<squad>/`.
