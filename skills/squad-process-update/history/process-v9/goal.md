# Inside a goal

## GOAL-1 Scopes of a goal
roles: manager
when: goal = yes
topic: goal

- `goal.md` orders the scopes with their dependencies. The goal Manager makes each scope with `squad-start "<text>" --in-goal <goal> --name <scope> --touches <paths>` (`<goal>` is the last part of `$GOAL_DIR`); its `scope.md` says `goal: <goal>`. Then it spawns the pod with `squad-spawn <role> <name> --scope <scope>`.
- `squad-start` stops on an overlap with an open scope: tell the PO and rerun with `--yes` only on their word.
- Start a scope when everything it depends on is closed, or passed if it only needs the code ([GOAL-5]). Independent scopes may run at once within the Developer cap ([START-2c]).

## GOAL-2 Shared folder
roles: manager
when: goal = yes
topic: goal

Scopes share only through `shared/`, and nothing more:
- `shared/decisions.md`: one `- ` bullet per whole-goal decision or domain fact, under 80 lines, kept by the goal Manager.
- `shared/summaries/<scope>.md`: one page per closed scope: outcome, passed branch and commit, open items, pointers; no decisions or domain facts.
- `shared/contracts/<name>.md`: a contract between scopes ([GOAL-3a]).

## GOAL-3a Contracts, Tech Lead
roles: tech-lead
when: goal = yes
topic: goal

Agree each shared contract with the other scope's contract owner (its Tech Lead, else its Manager) in `$GOAL_DIR/shared/contracts/<name>.md` before either side builds on it.

## GOAL-3b Contracts, QA whitebox
roles: qa-whitebox
when: goal = yes
topic: goal

Before either scope is done, check both sides' code against `$GOAL_DIR/shared/contracts/<name>.md` and record it in `qa-w.md`.

## GOAL-3c Contracts, Manager
roles: manager
when: goal = yes and tech-lead = no
topic: goal

Write each shared contract in `$GOAL_DIR/shared/contracts/<name>.md` before either scope builds on it. With no QA whitebox on the team, have the Developer's `## Review` name both sides' match to it before the scope is done.

## GOAL-4 Lone scope base
roles: manager
when: goal = no
topic: goal

A lone scope builds on the project as the PO left it.

## GOAL-5 Stacked branches
roles: manager
when: goal = yes
topic: goal

- Nothing merges until the PO asks, so a scope that needs an earlier scope's unmerged code builds on its passed branch.
- A task that needs unmerged work is spawned with `--base <passed branch or commit>`. The Manager checks the base ([GOAL-7]) and names it in the iteration file; the spawner passes that base and no other.

## GOAL-6a Integration task, Tech Lead
roles: tech-lead
when: goal = yes
topic: goal

Plan one integration task at the end of the scope: one Developer branches from the scope's base, merges the scope's passed task branches into its own branch and runs the targeted tests. A scope with one task has none: that task's passed branch is its integration branch.

## GOAL-6b Integration task, Developer
roles: manager, tech-lead
topic: goal

An integration task merges the scope's passed branches into the Developer's own branch, runs the targeted tests for the changed files and is handed in; the suite owner runs the full suite after ([WHO-2b], [WHO-2c], [WHO-2f]).

## GOAL-6c Integration task, next scope
roles: manager
when: goal = yes
topic: goal

The next scope builds on the integration branch; the PO merges it.

## GOAL-6d Integration task, Manager
roles: manager
when: goal = yes and tech-lead = no
topic: goal

Plan one integration task for a scope of several tasks, as [GOAL-6b] describes. A scope with one task has none: its passed branch is the integration branch.

## GOAL-7 Check a merge target
roles: manager
topic: goal

Before you name a branch or sha for the PO to merge or a scope to build on, check it: run `git merge-base --is-ancestor <base> <sha>` and `git log --oneline <base>..<sha>` and quote the output, never a ticket list.
