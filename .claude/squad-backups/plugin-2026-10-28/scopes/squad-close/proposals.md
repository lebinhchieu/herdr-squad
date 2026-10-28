# Coach proposals: squad-close (M, iteration 1)

**Verdict:** little waste. No expiries, no compactions, peak ctx ≤ 87k (all under the 100k/120k thresholds), no rule value to tune. Two plugin-level findings, no rule overlay (no evidence row supports one). No earlier `*.coach.md` backlogs exist ([ITER-13]), so nothing recurs yet.

Usage table (squad-usage):

| agent | model/effort | turns | peak ctx | out | exp | compact |
|---|---|---|---|---|---|---|
| plugin-mgr-squad-close | sonnet-5-5/high | 55 | 87k | 24k | 0 | 0 |
| plugin-dev-squad-close-2 | sonnet-5-5/medium | 58 | 82k | 20k | 0 | 0 |
| plugin-qaw-squad-close | sonnet-5-5/high | 52 | 68k | 24k | 0 | 0 |
| plugin-coach-squad-close | sonnet-5-5/high | 5 | 35k | 1k | 0 | 0 |

## Process proposals
None.

## Plugin proposals (role-card findings, ranked by saving)

### 1. Manager: settle the QA set with the PO before spawning the Dev (saves ~35k tokens per occurrence)
- **Evidence:** `iterations/1.md` Log: Dev plugin-dev-squad-close-2 spawned for task 03; next PO line "qa-b: no for the scope's remaining work… Dev respawned so its composed rules match." `usage-events.jsonl` ts 2026-10-22T18:20:27Z (dev-1, rule `fresh`) shows the earlier Dev already ended through the fresh rule. The table lists only dev-2 (the respawn), so the first spawn's cold start was spent and thrown away.
- **Change:** Manager card: on a task added mid-scope, ask the PO the QA set (qa-b yes/no, scope.md `qa`) in the same message that proposes the task, and spawn the Dev only after the answer, since the composed rules depend on it.
- **Saving:** one avoided cold start ≈ 35k ctx (coach row: 5 turns, 35k ctx = the base load of rules + card). Estimate; the retired Dev's own row is not in the table.

### 2. Manager: spawn the Token Coach only at close (saves ~35k tokens per occurrence)
- **Evidence:** `iterations/1.md` Log: "Token Coach spawned then retired unused (runs at close)". The same card load as the live coach row (35k ctx at 5 turns) was spent with no output.
- **Change:** Manager card: spawn the Token Coach in the closing step, never at scope start or on a task addition.
- **Saving:** ≈ 35k ctx, same estimate as above. Only one occurrence so far; it becomes a standing backlog item if it recurs.

## Backlog
Both plugin proposals are drafted as tasks/04 and tasks/05 (ITER-15); none became a rule overlay.
