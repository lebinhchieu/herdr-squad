# 04 Integration and merge by relation

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Problem

- In task-claim-gates, sibling branches 02, 03 and 06 were merged without ever being tested together. GOAL-6a plans integration only in a goal.
- Other scopes merge to main while a scope runs. MRG-2 does not check whether those changes touch the scope.

## Change

Source text: plugin overlay SQ-6, SQ-6b, SQ-7 and SQ-7b (`.claude/squads/plugin/process.local.md`).

- **Integration (GOAL-6a/6b, lone scope too):** when the last task passes, the plan owner checks the passed branches.
  - If each is an ancestor of the last (`git merge-base --is-ancestor`), no integration is needed.
  - Siblings are related when they change the same file, share a `grep -rl` test hit, or one writes what the other reads.
  - The Developer of the last dependent task merges related siblings and runs the targeted tests. With no such task, the plan owner adds one integration task.
  - Unrelated siblings need no integration.
- **Main moved (new MRG rule, before MRG-2):**
  - If `main` is an ancestor of the sha, there is nothing to check.
  - Otherwise compare the files changed `<base>..main` with `<base>..<sha>`.
  - No shared file and no shared test hit: merge, and note "main moved, N files, none related".
  - Related: a Developer merges `main` into the branch, runs the shared tests and hands in (a diff check, REV-14a). Then the Manager merges.

## AC

- AC1: a lone scope with only ancestor branches needs no integration task under the rules.
- AC2: the merge rule names both git commands and the note text.
- AC3: `python3 bin/squad-process lint` exits 0.

## Comments
