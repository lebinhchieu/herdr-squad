# Notes plugin-coach-squad-close (Token Coach, scope squad-close, size M)
## Now
Retro done. Proposals written to `$SCOPE_DIR/proposals.md` (path requested by the Manager; ITER-7 names `iterations/1.coach.md`, not created). Manager told: 2 proposals, 0 rule overlays. Nothing open.
## Findings
- Table clean: no expiries, no compactions, peak ctx ≤ 87k (mgr 87k, dev-2 82k, qaw 68k, coach 35k), under the 100k/120k thresholds. No rule value to tune.
- Plugin proposal 1: Manager settles the QA set with the PO before spawning a Dev (Dev respawned for composed rules; ~35k). Evidence: `iterations/1.md` Log, `usage-events.jsonl` ts 2026-10-22T18:20:27Z.
- Plugin proposal 2: Manager spawns the Token Coach only at close (spawned then retired unused; ~35k). Evidence: `iterations/1.md` Log.
- ~35k saving is an estimate (coach row: 5 turns, 35k ctx = base load).
## Backlog for later coaches (not proposed; need a usage row first)
- `squad-close` prints the kept pin twice in scope/goal close (from `1.summary.md`).
- If proposals 1 or 2 recur in another scope, make them standing proposals ([ITER-13]).
- No `_done` scope/goal folders existed, so no earlier backlogs were read.
## Pointers
- Scope folder: `.claude/squads/plugin/scopes/squad-close`
