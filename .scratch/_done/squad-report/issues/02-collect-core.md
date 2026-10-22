Status: ready-for-agent
Type: task
Task ID: 02
Touches: `bin/squadreport.py` (new), `templates/report/config.json` (new), `tests/report_fixtures.py` (new), `tests/test_squadreport_collect.py` (new)
Does not touch: `bin/squadtranscript.py` (read only), any other `squadreport_*`, `bin/squad-report`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_collect test_squadtranscript test_windows_safe`. `tests/report_fixtures.py` is the one fixture builder for every later ticket (see Handover → Fixtures).
Blocked by: 01. Parallel with 03 once this ticket's interface (below) is committed.

# 02: Collect core: timeline, buckets, tokens, cost, config, partial states

**Done when `base_data(collected)` returns the scope part of `data.json` (spec → Technical → data.json) for a synthetic scope, with buckets that sum to agent-time to the second.** Spec: Technical → "Time model", "Cost", "Security and data rules"; business AC1.4, AC3.1 (blocking time), AC3.4, AC7.1-7.3, AC1.7.

## Public interface (fixed; 03 and 04 build on it)
```
Msg(ts:int, frm, to, type, token, text, iteration:int|None=None)  # iteration = the messages.jsonl `iteration` field (every row has it; None if absent); type = first word, token = first token after it; text kept in memory only
read_messages(path) -> list[Msg]               # deduped: same (frm, type, token) within 120 s count once; sorted by ts
Escalation(id, title, raised_at, answered_at|None);  read_escalations(inbox_path) -> list     # seen -> answer
Seg(start:int, end:int, bucket, reason, on)    # bucket working|waiting|blocking|idle; reason peer|po|human_input|None; on agent|"PO"|None; epoch s
Turn(ts:int, tokens:{input,cache_read,cache_write,output}, cost:float, model)
AgentTL(name, role, transcript_found, live, sessions:int, segs:list[Seg], turns:list[Turn], cache_expiries:int)
Collected(scope_home, squad, name, size, window:(t0,t1), agents:{name:AgentTL}, msgs, escalations, roster, cfg, sources, partial_reasons)
load_config(plugin_root, squad_dir) -> dict    # templates/report/config.json, shallow-merged with <squad>/settings/report.json
collect(scope_home, squad_dir, plugin_root, final=False, deadline=None) -> Collected
base_data(c) -> dict    # schema keys: schema_version, kind, scope, config, sources, totals (buckets_s, stalled_s, respawn_gap_s, blocking_s, idle_s, tokens, cost_usd, cost_reported_usd, cost_delta_pct, wall_s, agent_s, parallelism), roles[], agents[] (segments raw, task null, events []) 
```
03 fills the remaining keys. `deadline` is a `time.monotonic()` value; exceeding it raises `Deadline` (04 maps it to exit 5).

## What
Implement the spec's classification table: a gap is classified by the record that ends it; `stall_s` (300) flags `stalled`; waiting for `task-notification` and `wait_patterns` commands; blocking only with an **unanswered** ASK/BLOCKED (ends at the first message from the addressee) or an open escalation (a gap straddling an escalation boundary is split at it); idle `peer` / `human_input`; sessions are never bridged (`respawn_gap_s`). Cost per turn = tokens x `config.prices[model]` (1h and 5m cache writes priced apart when `usage.cache_creation` splits them; unknown model uses `prices.default` and is listed in `sources.unpriced_models`); `cost_reported_usd` / `cost_delta_pct` from the last `cost-state` per session. A running scope (`scope.status`) or a missing transcript sets `partial` + `partial_reasons`; a scope with no messages or no tasks builds. Legacy flat squad: raise `Unsupported`. `config.json` defaults: `stall_s` 300, `wait_patterns` ["run_suite.py"], `min_segment_s` 60, `prices` (see AC 7), optional `claude_config_dirs`.

## Technical AC
1. Fixture (hand-computed, in `tests/report_fixtures.py`): one case per row of the time-model table, plus: unanswered vs answered ASK (an old answered ASK must **not** block later gaps: the prototype bug), stalled gap, gap across two sessions, escalation straddling a gap, copies of one HANDIN counted once, 1h/5m cache split, unknown model, `cost-state` delta, running scope, missing transcript, no messages, flat squad refused.
2. Invariants asserted on every fixture: sum of the four `buckets_s` == `agent_s` exactly; per-role buckets sum to the role's agent time; `blocking_s.peer+po == buckets_s.blocking`; `idle_s.peer+human_input == buckets_s.idle`; every Seg has `end >= start` and the fields above.
3. Changing `stall_s` or `wait_patterns` in a per-squad `settings/report.json` changes the result with no code change (AC3.4); the config used is echoed into `data.json.config`.
4. `base_data` is deterministic (two calls equal) and has no absolute path and no message/transcript text: a canary string planted in a prompt, a message body and a tool command appears nowhere in the dumped JSON.
5. Read-only: the test snapshots the roster, messages, inbox and transcript files before and after (bytes equal). No child process, no network (pure Python).
6. Field shape (process.md): every `roles[]` row has every field the spec lists; unknown fields none.
7. `templates/report/config.json` `prices`: calibrate per model family from `cost-state` records on this machine (per-model tokens and `costUSD`), note the date and "edit when list prices change" in a `_note` key; tests use fixture-defined prices, never the shipped table.
8. Primary behaviour only (qa: light).
