# Tickets without a Duties line block squad-spawn --task

Status: wontfix

Source: upstream-proposals retro (iterations/1.md, 1.summary.md Friction), 2026-11-24.

## Problem
`squad-spawn --task` refused the tickets in `.scratch/upstream-proposals/`, which have no Duties line. The duties went into `tasks/NN.md` instead.

## Proposed fix
Either the ticket template gets a Duties line, or `--task` reads `tasks/NN.md`.

## Comments
- 2026-11-25: superseded by 12 (scope po-clarity, iteration 3).
