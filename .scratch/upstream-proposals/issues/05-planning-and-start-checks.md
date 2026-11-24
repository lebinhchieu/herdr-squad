# 05 Planning and start checks

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Change

Source text: plugin overlay SQ-1, SQ-8, SQ-21 and SQ-22.

| Source | Target | Edit |
|---|---|---|
| SQ-1 | LC-14 | One sentence: for each ticket that deletes or moves files, list the tickets that read them; a reader goes before its deleter |
| SQ-8 | New LC rule | A task waits while an open ASK to the PO changes it. If a PASS lists choices for the PO, keep the Developer until the PO answers (45 min at most) |
| SQ-21 | START-18 | Before the first spawn, run `squad-process homes --check`. If this scope's pin is older than the squad's `plugin.pin`, ask the PO at the plan check-in. Do not grep `_done/` (SAFE-7). A running scope is never re-pinned |
| SQ-22 | SPAWN-9 | The Team Lead spawns both QAs on `team:` before the first Developer. A refused Developer spawn gets one retry once the rows exist. Drop the "pin 0.10.4" text |

## AC

- AC1: each edit lands in the target rule, or in one new rule, and attaches to the roles in the overlay op.
- AC2: no rule text reads `_done/` or names a plugin version.
- AC3: `python3 bin/squad-process lint` exits 0.
- AC4: the Developer quotes `squad-process upgrade --check --squad-dir <dir> --plugin-root <worktree>` output; each source op shows as `add` (kept) or `stale`, and Comments list which plugin rule replaces it.
- AC5: no rule text names the PO by name; it says "the PO".

Duties: SQ-10 files (`tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`) plus the `grep -rl` hits of each changed rule ID.

## Comments

- Overlay SQ-1 (reader before deleter) is replaced by plugin rule LC-14 (one added sentence).
- Overlay SQ-8 (hold a task for an open PO ASK) is replaced by new plugin rule LC-28.
- Overlay SQ-21 (scope pin check) is replaced by plugin rule START-18, step 4 (`squad-process homes --check`).
- Overlay SQ-22 (QA rows before the first Developer) is replaced by plugin rule SPAWN-9.
- `upgrade --check` shows SQ-21 and SQ-22 as `review: the plugin changed START-18 / SPAWN-9`, and SQ-1 and SQ-8 unaffected (`add`, kept); the squads drop all four ops by hand after re-pin.
