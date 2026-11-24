# 05 Inbox item shows its plan row

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md` · Blocked by: 04

## Problem

An inbox item says what it wants, but not where it sits in the plan. To answer "erd13 passed: confirm close", Chieu has to remember what erd13 is and what comes next.

## Change

When an item is added with `--blocks <scope>` (already an option), the inbox pane and the board's inbox panel draw one grey line under the title. It comes from the same reader as ticket 04:

```text
┌ E23  erd13 passed: confirm close ─────────────┐
│ scope 13 of 15 · ERD v12 rewritten · next:    │
│ promotion                                     │
│                                               │
│ [decision] Close erd13? ...                   │
└───────────────────────────────────────────────┘
```

In a scope home, `--blocks NN` names a task and the line reads `task 10 of 11 · step 4 · no flaky timing · next: 11`. If `--blocks` names nothing in the plan, the line is left out. The Manager writes nothing new.

## AC

- AC1: an item with `--blocks erd13` on the fixture goal shows "scope 13 of 15 · … · next: …".
- AC1b: in a scope home, an item with `--blocks 10` shows the task's step, aim and next task.
- AC2: an item with no `--blocks`, or one with an unknown scope, shows no plan line and no error.
- AC3: the po-inbox pane test and the board inbox panel test each cover AC1.

## Comments
