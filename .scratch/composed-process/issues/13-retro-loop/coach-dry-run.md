# Coach cur, iteration 1

Evidence: `scopes/cur/usage.md` (2 rows). `usage-events.jsonl` absent. `process-log.md` absent, so "already logged" unchecked. `squad-usage` not in this session.

## Proposals (ranked by saving)

1. **Dev respawn at 100k, not 120k**
   - Evidence: `usage.md` row `t-dev-cur-1 | dev | opus | 131k | 3 | 80`. Peak 131k is over the 120k threshold; 3 cache expiries in 80 turns.
   - Cited backlogs (ITER-13, 2 scopes): `scopes/_done/alpha/iterations/1.coach.md` and `goals/_done/g1/coach/g1.coach.md`, both "Dev idles at 120k context before respawn; lower COST threshold to 100k for dev".
   - Rule change (overlay, `upstream: proposed`). Threshold rule ID not in scope files; Manager to fill `<ID>`:
     ```
     upstream: proposed
     rule: <ID of dev context-respawn threshold>
     change: 120k -> 100k (dev only)
     ```
   - Saving: each expiry re-caches the full prefix. At 100k cap, prefix is 31k smaller than at 131k peak (31/131 ≈ 24%). 3 expiries × 31k ≈ 93k tokens less cache-write on dev. Upper bound: assumes each expiry re-caches peak context.

## Not proposed (evidence too thin)

- QA `t-qa-cur-1` (sonnet, 60k, 1 expiry, 30 turns): under all thresholds, no waste row.
- Dev 3 expiries vs 1h TTL: cannot tell whether TTL is wrong without `ts` in `usage-events.jsonl`. Need that file to tune 1h.
- Dev on opus: no default model in scope files to compare against.

## Plugin proposals

- `squad-usage` not available in this session; the table was read directly. Check the tool is wired for Token Coach sessions. Evidence: START-17 step 2 and the Manager's note.

## Backlog
