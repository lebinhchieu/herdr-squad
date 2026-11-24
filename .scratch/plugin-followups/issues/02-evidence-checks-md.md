# Evidence assembly deletes checks.md

Status: needs-triage

Source: upstream-proposals retro (iterations/1.md, 1.summary.md Friction), 2026-11-24.

## Problem
Developers 07 and 11 deleted `checks.md` in the ticket folder while assembling evidence. `squad-evidence check` treats other ticket-folder files as outside the evidence.

## Proposed fix
`squad-evidence add` keeps the other files in the ticket folder, or the Developer rule says so.

## Comments
- 2026-11-24, Token Coach plugin proposal 4: third scope with this (watchdog-blind dev-4, dev-5). Fixing it unblocks the SQ-20 `--base` replace held in the coach backlog.
