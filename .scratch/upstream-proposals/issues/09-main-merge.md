# 09 Merge main into the 08 branch (SQ-7b)

Status: handed in (Developer, 2026-11-24)

Spec: `.scratch/upstream-proposals/spec.md`. Base: 932420a (08 passed at 495e865).

## Change

Main moved to 7fc9119 (a `CONTEXT.md` glossary change: Finding, Follow-up). SQ-7b: merge `main` into the 08 branch before the PO merge. Merge commit 4e7d547, no conflict.

## Acceptance criteria

- AC1: the merge adds only `CONTEXT.md`: `git diff 932420a 4e7d547 --name-only` prints `CONTEXT.md` and nothing else.

## Comments

- QA whitebox PASS on 4e7d547 (`evidence/09/qa-w.md`). Only QA whitebox checks 09 (Manager DECISION 08).
