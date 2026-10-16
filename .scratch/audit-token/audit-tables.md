## Baseline (until 2026-10-16T02:00:00Z)

- Transcript files found (raw, both config dirs): 488; distinct after realpath: 244 (240 sessions + 4 subagent files)
- Sessions with at least one usage line before the cutoff: 227
- Messages (distinct ids): 10287; lines read: 19331; synthetic ids skipped: 15
- Date range of usage: 2026-10-11T14:15:45.040Z .. 2026-10-16T01:59:39.101Z
- Ids that appear in more than one file (resumed/forked copies), counted once: 136 ($9.78 that a per-file sum would add)
- Total spend (list price, priced models): $297.17; unpriced messages: 0
- Cross-check against Claude Code's own `cost-state.totalCostUSD` (last record of each session, 224 sessions): sum $306.91 vs this script $293.87

### Price table ($ per million tokens)

Source: vendor pricing page platform.claude.com/docs/en/about-claude/pricing, Model pricing table, fetched 2026-10-16. (The `claude-api` skill's cached table lists Sonnet 5.5 cache read at $0.20; the vendor page says $0.10 and agrees with Claude Code's own cost-state totals, so the vendor page is used.) No other model appears in the data.

| model | input | output | cache read | cache write 5m | cache write 1h |
|---|---|---|---|---|---|
| claude-haiku-5-5 | 0.1 | 0.5 | 0.01 | 0.125 | 0.2 |
| claude-opus-5-5 | 4.0 | 20.0 | 0.2 | 5.0 | 8.0 |
| claude-sonnet-5-5 | 2.0 | 10.0 | 0.1 | 2.5 | 4.0 |
| claude-haiku-5-5 (prompt > 100K) | 0.5 | 2.5 | 0.05 | 0.625 | 1.0 |

Unpriced models: none

### Attribution coverage (T6)

attributed = transcript `agent-name` resolved to a scope (roster or name pattern); unattributed = squad role known but no scope; non-squad = test/probe names or no `agent-name` (PO's own sessions).

| category | sessions | spend $ | share of total |
|---|---|---|---|
| attributed | 178 | 231.19 | 77.8% |
| non-squad: no agent-name (PO or manual sessions) | 27 | 33.13 | 11.1% |
| non-squad: test/probe sessions | 19 | 4.76 | 1.6% |
| unattributed: squad-level manager (no scope) | 3 | 28.09 | 9.5% |

Scope resolved by: none: 49, roster: 178

Roster rows give a session id for 66 of 227 sessions; usage-events for 79; a roster-only attribution would miss 113 of 178 attributed sessions (respawned roles). Transcript name vs roster/usage-events name disagreements: 0.

### Spend per role (denominator: total spend)

Includes subagent messages under the parent's role (see the subagent row below). Role = `agent-setting`; `?` = no squad role.

| role | phase | sessions | messages | $ | share of total | in $ | cache read $ | cache write $ | out $ |
|---|---|---|---|---|---|---|---|---|---|
| dev | build | 82 | 3970 | 97.07 | 32.7% | 0.02 | 37.10 | 32.08 | 27.87 |
| manager | coordination | 18 | 1454 | 62.23 | 20.9% | 0.01 | 29.84 | 19.50 | 12.87 |
| qa-whitebox | QA | 29 | 1367 | 35.98 | 12.1% | 0.01 | 13.18 | 13.94 | 8.86 |
| tech-lead | plan | 27 | 1277 | 33.39 | 11.2% | 0.01 | 11.88 | 12.53 | 8.97 |
| ? | ? | 33 | 633 | 33.15 | 11.2% | 0.00 | 12.20 | 12.15 | 8.79 |
| qa-blackbox | QA | 21 | 1172 | 24.96 | 8.4% | 0.01 | 11.01 | 7.78 | 6.17 |
| ba | plan | 11 | 344 | 8.13 | 2.7% | 0.00 | 2.74 | 3.14 | 2.25 |
| token-coach | retro | 5 | 47 | 1.54 | 0.5% | 0.00 | 0.24 | 0.71 | 0.59 |
| designer | plan | 1 | 23 | 0.72 | 0.2% | 0.00 | 0.17 | 0.26 | 0.29 |

### Spend per phase (approximate: phase is derived from role)

Role-to-phase table: plan = ba, tech-lead, team-lead, designer; build = dev; QA = qa-whitebox, qa-blackbox; retro = token-coach; coordination = manager; no-phase = no squad role.

| phase | $ | share of total |
|---|---|---|
| build | 97.07 | 32.7% |
| coordination | 62.23 | 20.9% |
| QA | 60.94 | 20.5% |
| plan | 42.24 | 14.2% |
| no-phase | 33.15 | 11.2% |
| retro | 1.54 | 0.5% |

### Spend per token type (denominator: total spend)

Output includes thinking tokens (not added again): thinking_tokens max-folded = 1,979,776 of the output tokens above.

| type | tokens | $ | share of total |
|---|---|---|---|
| input (uncached) | 22,998 | 0.05 | 0.0% |
| cache read | 1,063,714,540 | 118.36 | 39.8% |
| cache write 5m | 13,769,085 | 37.90 | 12.8% |
| cache write 1h | 14,713,264 | 64.20 | 21.6% |
| output | 7,009,349 | 76.66 | 25.8% |

### Spend per model (denominator: total spend)

| model | messages | $ | share of total | in $ | cache read $ | cache write $ | out $ |
|---|---|---|---|---|---|---|---|
| claude-sonnet-5-5 | 9196 | 241.21 | 81.2% | 0.04 | 94.13 | 83.64 | 63.41 |
| claude-opus-5-5 | 1053 | 55.92 | 18.8% | 0.01 | 24.22 | 18.44 | 13.25 |
| claude-haiku-5-5 | 38 | 0.04 | 0.0% | 0.00 | 0.01 | 0.02 | 0.00 |

### Role x model (denominator: total spend)

| role | model | messages | $ | share of total |
|---|---|---|---|---|
| dev | claude-sonnet-5-5 | 3970 | 97.07 | 32.7% |
| manager | claude-opus-5-5 | 856 | 40.54 | 13.6% |
| qa-whitebox | claude-sonnet-5-5 | 1367 | 35.98 | 12.1% |
| tech-lead | claude-sonnet-5-5 | 1277 | 33.39 | 11.2% |
| qa-blackbox | claude-sonnet-5-5 | 1172 | 24.96 | 8.4% |
| manager | claude-sonnet-5-5 | 598 | 21.69 | 7.3% |
| ? | claude-sonnet-5-5 | 398 | 17.74 | 6.0% |
| ? | claude-opus-5-5 | 197 | 15.38 | 5.2% |
| ba | claude-sonnet-5-5 | 344 | 8.13 | 2.7% |
| token-coach | claude-sonnet-5-5 | 47 | 1.54 | 0.5% |
| designer | claude-sonnet-5-5 | 23 | 0.72 | 0.2% |
| ? | claude-haiku-5-5 | 38 | 0.04 | 0.0% |

Speed field (messages): None: 44, standard: 10243. Anything other than `standard` would be flagged; `None` = older transcript lines without the field.

### Subagents (T3; `bin/squad-usage` skips sidechain lines)

4 subagent file(s) / sidechain lines contribute; messages tagged `subagent` in the rows.

| parent role | messages | $ | share of total |
|---|---|---|---|
| ? | 2 | 0.11 | 0.0% |
| manager | 38 | 1.49 | 0.5% |
| all | 40 | 1.61 | 0.5% |

### Spend per scope (denominator: total spend)

| squad/scope | status | sessions | messages | $ | share of total | first | last |
|---|---|---|---|---|---|---|---|
| squad-board/board | closed | 79 | 3739 | 104.64 | 35.2% | 2026-10-11 | 2026-10-14 |
| plugin/po-inbox | closed | 29 | 1788 | 46.22 | 15.6% | 2026-10-15 | 2026-10-15 |
| plugin/refine-process | closed | 27 | 1259 | 29.00 | 9.8% | 2026-10-14 | 2026-10-14 |
| squad-board/squad-tabs | live | 18 | 1047 | 26.31 | 8.9% | 2026-10-14 | 2026-10-14 |
| plugin/board-flakes | closed | 12 | 567 | 13.08 | 4.4% | 2026-10-14 | 2026-10-15 |
| squad-board/add-ui-ux-design | closed | 6 | 258 | 6.68 | 2.2% | 2026-10-14 | 2026-10-14 |
| squad-board/generic-rules | closed | 4 | 171 | 3.21 | 1.1% | 2026-10-14 | 2026-10-14 |
| squad-board/guide | closed | 2 | 56 | 1.54 | 0.5% | 2026-10-14 | 2026-10-14 |
| plugin/audit-token | live | 1 | 10 | 0.50 | 0.2% | 2026-10-16 | 2026-10-16 |

Spread across all scopes: min $0.50 / median $13.08 / max $104.64 (n=9).
Spread across closed scopes: min $1.54 / median $13.08 / max $104.64 (n=7).

## Driver metrics


### Cost by message context size (context = input + cache read + cache write of that message)

| context band | messages | $ | share of total | cache-read tokens |
|---|---|---|---|---|
| 0k-50k | 1329 | 34.89 | 11.7% | 46,513,323 |
| 50k-120k | 6189 | 143.69 | 48.4% | 503,610,413 |
| 120k-200k | 1962 | 71.72 | 24.1% | 287,023,124 |
| 200k-infk | 807 | 46.86 | 15.8% | 226,567,680 |

- Cache expiries (gap > 1h and cache write >= 10k, same rule as `squad-usage`): 24; the rewrite cost $12.26 (4.1% of total), $11.90 above what a cache read of the same tokens would have cost.
- First 10 messages of every session (startup reading): $60.34 (20.3% of total) over 227 sessions.

### Sessions per (scope, role) = respawn count

| role | sessions | (scope, role) pairs | avg sessions per pair |
|---|---|---|---|
| ba | 10 | 4 | 2.50 |
| designer | 1 | 1 | 1.00 |
| dev | 80 | 8 | 10.00 |
| manager | 8 | 6 | 1.33 |
| qa-blackbox | 21 | 4 | 5.25 |
| qa-whitebox | 29 | 6 | 4.83 |
| tech-lead | 25 | 6 | 4.17 |
| token-coach | 4 | 4 | 1.00 |

Per session (main threads): n=227, min $0.00 / median $0.92 / max $12.53; top 5 sessions: 47e728f8 $12.53, 3de6314e $12.15, ec9cc885 $10.96, 93fb2b33 $10.02, 454e57a4 $9.78.

## Naive-sum inflation (T2)

Session 47e728f8-9cab-47fb-aa7d-6ce6b65d435f (/home/chieule/.claude/projects/-home-chieule-workspace-squad/47e728f8-9cab-47fb-aa7d-6ce6b65d435f.jsonl): 553 assistant usage lines, 299 distinct message ids; summing every line would give $23.17 vs $12.53 deduped (1.85x).
All files: naive per-line sum $613.87 vs per-id max $306.95 before cross-file dedupe (2.00x).

## Driver arithmetic (inputs for audit.md)

### Existing work: context over 120k before and after (denominator: that window's spend)

| window | messages | $ | $ per 1000 messages | spend in messages over 120k | messages over 120k |
|---|---|---|---|---|---|
| before Token Coach | 1204 | 64.25 | 53.4 | 59.3% | 52.1% |
| Token Coach, percent rules | 5382 | 142.75 | 26.5 | 39.8% | 26.0% |
| absolute 120k rule | 3701 | 90.16 | 24.4 | 26.2% | 20.0% |

### D1: cost of context above 120k (excess cache-read tokens x read price) vs the respawns that would cut it

Respawns = sum over sessions of floor(peak context / 120k); respawn cost = respawns x that role's mean first-10-message cost.

| role | messages over 120k | sessions crossing | excess read $ | respawns needed | mean startup $ | respawn cost $ | net $ |
|---|---|---|---|---|---|---|---|
| manager | 689 | 8 | 8.36 | 12 | 0.43 | 5.21 | 3.15 |
| ? | 255 | 5 | 5.15 | 9 | 0.23 | 2.07 | 3.08 |
| dev | 1003 | 36 | 4.36 | 38 | 0.26 | 10.01 | -5.65 |
| qa-whitebox | 316 | 18 | 1.45 | 19 | 0.25 | 4.68 | -3.23 |
| tech-lead | 243 | 18 | 1.17 | 19 | 0.27 | 5.17 | -4.00 |
| qa-blackbox | 234 | 13 | 0.98 | 14 | 0.23 | 3.17 | -2.19 |
| ba | 22 | 6 | 0.01 | 6 | 0.22 | 1.32 | -1.31 |

Total: excess $21.47 (7.2% of total), respawn cost $31.62, net $-10.15 (-3.4% of total).

### D2: first 10 messages of each session, by role (denominator: total spend)

| role | sessions | $ | share of total | mean $ per session |
|---|---|---|---|---|
| dev | 82 | 21.60 | 7.3% | 0.26 |
| manager | 18 | 7.81 | 2.6% | 0.43 |
| ? | 33 | 7.60 | 2.6% | 0.23 |
| tech-lead | 27 | 7.35 | 2.5% | 0.27 |
| qa-whitebox | 29 | 7.14 | 2.4% | 0.25 |
| qa-blackbox | 21 | 4.75 | 1.6% | 0.23 |
| ba | 11 | 2.41 | 0.8% | 0.22 |
| token-coach | 5 | 1.47 | 0.5% | 0.29 |
| designer | 1 | 0.22 | 0.1% | 0.22 |

### D2b: respawns that happened while the previous session was under 100k context

Upper bound of what reuse could save = startup cost of the successor; the carried context would be read again each turn (one read shown).

| role | successor sessions | of which predecessor peak < 100k | their startup $ | one read of carried context $ |
|---|---|---|---|---|
| dev | 72 | 25 | 6.66 | 0.16 |
| qa-whitebox | 23 | 4 | 0.89 | 0.02 |
| qa-blackbox | 17 | 3 | 0.65 | 0.02 |
| tech-lead | 19 | 2 | 0.54 | 0.01 |
| ba | 6 | 0 | 0.00 | 0.00 |
| manager | 2 | 0 | 0.00 | 0.00 |

### D3: 1-hour cache writes

- 1h cache-write spend $64.20 (21.6% of total); the same tokens at the 5m write price: $40.12; difference $24.07.
- Messages that read cache after a gap of 5-60 min (would miss a 5m cache and rewrite those tokens): 503; extra cost $143.10.
- Net if every write were 5m: $-119.02 (-40.1% of total). Whether Claude Code lets the squad choose the TTL is not measured here.

### D4: Opus messages repriced at Sonnet 5.5 (same tokens)

| role | opus messages | opus $ | same tokens at sonnet $ | difference $ | share of total |
|---|---|---|---|---|---|
| manager | 856 | 40.54 | 20.27 | 20.27 | 6.8% |
| ? | 197 | 15.38 | 7.69 | 7.69 | 2.6% |

### D5: output and thinking by role (denominator: total spend)

| role | output $ | share of total | thinking tokens | thinking $ (at output price) | share of total | effort field (messages) |
|---|---|---|---|---|---|---|
| dev | 27.87 | 9.4% | 806,544 | 8.07 | 2.7% | high: 1508, medium: 2462 |
| manager | 12.87 | 4.3% | 208,138 | 3.00 | 1.0% | high: 598, medium: 856 |
| tech-lead | 8.97 | 3.0% | 253,971 | 2.54 | 0.9% | high: 1277 |
| qa-whitebox | 8.86 | 3.0% | 242,980 | 2.43 | 0.8% | high: 1367 |
| ? | 8.79 | 3.0% | 210,784 | 2.47 | 0.8% | high: 374, low: 65, medium: 194 |
| qa-blackbox | 6.17 | 2.1% | 152,900 | 1.53 | 0.5% | high: 1172 |
| ba | 2.25 | 0.8% | 61,035 | 0.61 | 0.2% | high: 344 |
| token-coach | 0.59 | 0.2% | 31,809 | 0.32 | 0.1% | high: 14, medium: 33 |
| designer | 0.29 | 0.1% | 11,615 | 0.12 | 0.0% | high: 23 |

### D5b: developer output per message by effort (same role, same model; task mix differs, so only an upper-bound hint)

| effort | messages | mean output tokens | mean thinking tokens |
|---|---|---|---|
| high | 1508 | 997 | 376 |
| medium | 2462 | 521 | 98 |

### D4b: manager messages and quality signals per scope

| squad/scope | manager messages opus | manager messages sonnet | scope $ |
|---|---|---|---|
| plugin/audit-token | 10 | 0 | 0.50 |
| plugin/board-flakes | 114 | 0 | 13.08 |
| plugin/po-inbox | 49 | 58 | 46.22 |
| plugin/refine-process | 178 | 0 | 29.00 |
| squad-board/add-ui-ux-design | 46 | 32 | 6.68 |
| squad-board/board | 0 | 0 | 104.64 |
| squad-board/generic-rules | 0 | 0 | 3.21 |
| squad-board/guide | 0 | 0 | 1.54 |
| squad-board/squad-tabs | 250 | 0 | 26.31 |
