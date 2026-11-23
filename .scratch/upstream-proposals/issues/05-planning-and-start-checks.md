# 05 Planning and start checks

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Change

Source text: plugin overlay SQ-1, SQ-8, SQ-21 and SQ-22.

| Source | Target | Edit |
|---|---|---|
| SQ-1 | LC-14 | One sentence: for each ticket that deletes or moves files, list the tickets that read them; a reader goes before its deleter |
| SQ-8 | New LC rule | A task waits while an open ASK to Chieu changes it. If a PASS lists choices for Chieu, keep the Developer until he answers (45 min at most) |
| SQ-21 | START-18 | Before the first spawn, run `squad-process homes --check`. If this scope's pin is older than the squad's `plugin.pin`, ask Chieu at the plan check-in. Do not grep `_done/` (SAFE-7). A running scope is never re-pinned |
| SQ-22 | SPAWN-9 | The Team Lead spawns both QAs on `team:` before the first Developer. A refused Developer spawn gets one retry once the rows exist. Drop the "pin 0.10.4" text |

## AC

- AC1: each edit lands in the target rule, or in one new rule, and attaches to the roles in the overlay op.
- AC2: no rule text reads `_done/` or names a plugin version.
- AC3: `python3 bin/squad-process lint` exits 0.

## Comments
