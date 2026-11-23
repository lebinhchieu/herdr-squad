# 04 Integration and merge by relation

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Problem

- In task-claim-gates, sibling branches 02, 03 and 06 were merged without ever being tested together. GOAL-6a plans integration only in a goal.
- Other scopes merge to main while a scope runs. MRG-2 does not check whether those changes touch the scope.

Files: `templates/squad/process/goal.md`, `templates/squad/process/merge.md`, `bin/squadmergecheck.py` and `bin/squad-merge-check` (comments and one reason string, no behaviour change), `tests/test_squad_merge_check.py` (comments).

Duties: `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`, plus every `grep -rl` hit of GOAL-6a, GOAL-6d, GOAL-6e, GOAL-6f, MRG-6, MRG-6b in `tests/`. Rule text says "the PO", never a name.

## Change

Source text: plugin overlay SQ-6, SQ-6b, SQ-7 and SQ-7b (`.claude/squads/plugin/process.local.md`).

- **Integration (GOAL-6a/6b, lone scope too):** when the last task passes, the Team Lead checks the passed branches.
  - If each is an ancestor of the last (`git merge-base --is-ancestor`), no integration is needed.
  - Siblings are related when they change the same file, share a `grep -rl` test hit, or one writes what the other reads.
  - The Developer of the last dependent task merges related siblings and runs the targeted tests. With no such task, the Team Lead asks the Manager to add one integration task.
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
- AC4: new IDs GOAL-6e, GOAL-6f, MRG-6, MRG-6b; MRG-6 sits before MRG-2 and prints in `squad-merge-check` output; GOAL-6a and GOAL-6d lose `when: goal = yes`; no `SQ-6`/`SQ-7` left in `bin/`.
- AC5: no rule of this ticket attaches to `dev`; the worst no-designer, no-architect Developer team stays at its base size.
- AC6: `upgrade --check` output quoted; each source op SQ-6, SQ-6b, SQ-7, SQ-7b shows as `add` or `stale`, and Comments name the replacing rule (GOAL-6e, GOAL-6f, MRG-6, MRG-6b).

## Comments
- Replacements: SQ-6 -> GOAL-6e, SQ-6b -> GOAL-6f, SQ-7 -> MRG-6, SQ-7b -> MRG-6b (squads drop the overlay ops after re-pin).
