Status: ready-for-agent
Type: task
Task ID: 03
Touches: `bin/squadreport_tasks.py` (new), `tests/test_squadreport_tasks.py` (new); adds fixtures to `tests/report_fixtures.py` only as new functions in a block at the end (02 owns the file; no edit of existing lines)
Does not touch: `bin/squadreport.py`, `bin/squad-report`, `templates/`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_tasks test_squadreport_collect`. Builds on 02's `Collected`; start when 02's interface is committed (Handover → Order).
Blocked by: 02 (interface only; may start on 02's first commit)

# 03: Tasks: aliases, attribution, returns, rework, review wait, PO wait, iterations

**Done when `fill(data, collected)` completes `data.json` (everything 02 leaves out) and task rows match hand-computed values.** Spec: Technical → "Task context (attribution)", "Returns, rework, review wait"; business AC2.1-2.5, 3.1-3.3, 3.5, S4 (AC4.1-4.3, 4.5-4.6 data side).

## Public interface
`fill(data:dict, c:Collected, redact:bool=False) -> None` mutates `data` in place. Fields it owns: `tasks[]`, `iterations[]`, `matrix[]`, `scope.iterations`, `totals.{attributed,returns,tasks_passed,cost_per_passed_task_usd,po_wait}`, `agents[].segments` (replaces 02's raw list: split at task changes, merged, segments `< min_segment_s` absorbed, display only; 5 elements `[start_s,end_s,"w|a|b|i",task|null,on]`, offsets from `window.start`, adjacent blocking segments merge only if `on` equal), `agents[].events`. `redact=True` drops ticket and escalation titles and `returns_list[].reason`.

## What
- Task id of a message = the token after its type (never the hook's `task` field). Canonical id: `NN` or `NN-slug` map to ticket `NN` when `.scratch/*/issues/NN-*.md` exists (the feature dir is the one whose slugs match most tokens; none = no titles, still works); `X (Y)` merges aliases; `STATUS`, `squad-*` and agent names are not tasks. New scopes follow the `process.md` Task ID rule (ticket number alone); aliases are the fallback for old scopes.
- Attribution layers per second: `message` (sticky: last task token the agent sent or received), `branch`/roster `Owns` (a Developer's `ticket NN`), else `overhead` (task null). `attributed.time_pct` = attributed non-idle s / non-idle s; `cost_pct` likewise; `layers` in non-idle seconds. Cost goes to the task in force at the turn's second.
- Returns = deduped FAIL messages (the same ts window as 02); `returns_list[]` has `fail_at, fail_by, handin_at, reason` (reason = text after `FAIL <task>`, whitespace collapsed, cut at 200 chars; `fail_by` = sender); `flag` at >= 3. Rework = FAIL to the task's next HANDIN (time and cost). Review wait = HANDIN to the last PASS/FAIL before the task's next HANDIN (`verdict` PASS|FAIL|none). `cycle_s` = first mention to PASS. `iteration` from the message's `iteration` field.
- PO wait from `escalations`: `count,total_s,longest_s,pct_of_elapsed,items[]`; an unanswered one runs to the window end and has `answered_at` null. The PO is never an agent row.

## Technical AC
1. Fixture scope (hand-computed): two tasks, one with 2 FAILs (reason text cut and whitespace-collapsed, one FAIL copied to 3 roles counted once), alias merge `07-slug (T0)`, a leftover alias row, overhead work, a Developer on `Owns: ticket NN` with no message, two iterations, an unanswered escalation. Task rows, `returns`, `rework_s`, `review_waits`, `cycle_s`, `attributed.*`, `po_wait` equal the hand-computed values.
2. Invariants on every fixture (also on 02's): task `cost_usd` sum + overhead == `totals.cost_usd`; `matrix` cost/time sums == totals; `% attributed` denominator is non-idle seconds (idle excluded); every returns_list item has its `handin_at` or null and `fail_at`; every closed review wait has `verdict_at`; `tasks_passed` == tasks with a PASS.
3. `redact=True`: no title and no reason anywhere in the dumped `data`; counts, ids, roles, times unchanged. Without redact, titles are cut at 120 chars.
4. Canary: a planted string in a non-FAIL message body appears nowhere in the output; the only message text present is the FAIL reasons.
5. Legacy: transcripts with no `origin` (harness_origin false) still produce tasks (gaps classify idle) and set `partial_reasons` entry `no_origin`.
6. Field shape: see 04 AC9 (full build output); here every task row and `returns_list[]` item produced by `fill` has the spec's fields on the fixtures above.
7. **Segments reconcile with buckets (defect class from 04's FAIL):** on every fixture and on the full build output, per agent and per bucket, the sum of `segments` durations equals `agents[].buckets_s` up to the seconds of absorbed short segments (the test computes that difference and asserts it equals the absorbed total, never more), no segment crosses a respawn hole or an idle gap (its bucket would not be the record-classified one), and every `blocks[]` / `longest_block` duration is <= the bucket total it is drawn from. Short-segment absorb must never merge across a different bucket or a hole. Regression test: respawn hole between two short working segments (the 10 h vs 39 s case).
8. Primary behaviour only (qa: light).
