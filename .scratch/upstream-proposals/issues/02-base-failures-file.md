# 02 Squad-wide base failures file

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Problem

The same tests that fail on main are proven again at base in scope after scope:

- guardian: ReviewActionsTest and StreamRevalidate* in cvproduce and cvread.
- plugin watchdog-should: one failing test was listed in 8 scopes.
- plugin remove-jira: AC1 and AC2 could not pass as written; this was found only after the pod spawned.

The proposals put the check on the Manager and grep `_done/`, which breaks SAFE-6 and SAFE-7.

## Change

1. One file, `$SQUAD_DIR/base-failures.md`. Each row holds: the test name, the sha it fails on, a one-line cause, the first scope that saw it, and a fix ticket or Chieu's "keep".
2. Owner: the Tech Lead. Without a Tech Lead, QA whitebox; with neither, the Developer.
3. Before a task's first spawn, the owner runs the task's grep and test AC on the base sha. An AC that cannot pass there is fixed in the ticket first. A test failing on base is added to the file.
4. A Developer or QA checks a failing test name against the file. A listed name is not run on base again and is no `FAIL`. A name that is not listed is run on base once and added.
5. A name that is already in the file from an earlier scope, with no fix ticket and no keep: the Manager raises it at the next check-in.

## AC

- AC1: the rule names `$SQUAD_DIR/base-failures.md`, its columns and its owner chain.
- AC2: no rule text asks the Manager to run tests or read `_done/`.
- AC3: the file is listed in `files.md` with its owner.
- AC4: `python3 bin/squad-process lint` exits 0.

## Comments
