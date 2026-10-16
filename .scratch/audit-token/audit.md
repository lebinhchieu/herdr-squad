# AT-01 Token audit

**No fix is "real" yet.** Of $297.17 spent, the two largest quantified candidates (manager on Sonnet: up to $20.27 = 6.8%; QA-side effort `medium`: about $12.5 = 4.2%) pass the 2% bar on paper but have no RS-3 evidence, so both are **unproven**. The other three drivers are **minor** or counter-productive. Existing work already halved the share of spend in contexts over 120k (59% to 26%).

- Command: `python3 -I .scratch/audit-token/scripts/audit.py --until 2026-10-16T02:00:00Z` (writes `audit-tables.md` and `audit-tables.json`, next to this file). Run twice: byte-identical (B6).
- Selftest: `python3 -I .scratch/audit-token/scripts/audit.py --selftest`: PASS, output in `evidence/AT-01/selftest.txt` (fixture `scripts/fixtures/session-fixture.jsonl`: id `msg_A` on 3 lines, max-fold gives out 90 not 10+40+90).
- Every table below is copied from `audit-tables.md` (section names in brackets). Denominator is the **total spend $297.17** unless a column says otherwise.
- Message-level evidence for two real samples: `evidence/AT-01/sample-idle-manager.txt` (6 messages, `aa3c4b35-…`), `evidence/AT-01/sample-long-manager.txt` (299 messages, `47e728f8-…`). Command: `... --show-session <id>`.

## Baseline (AT-01-B1, T5)

| Item | Value |
|---|---|
| Cutoff | 2026-10-16T02:00:00Z (live sessions keep growing; a later cutoff gives larger totals by design) |
| Date range of usage | 2026-10-11T14:15:45Z .. 2026-10-16T01:59:39Z |
| Transcript files | 488 found in `~/.claude` and `~/.claude-2`; **244 distinct** after `realpath` (240 sessions + 4 subagent files). The symlink would double every number |
| Sessions with usage before cutoff | 227 (13 have none: the audit-token pod, started at the cutoff; ids in `evidence/AT-01/missing-transcripts.txt`) |
| Messages | 10,287 distinct ids from 19,331 lines; 15 `<synthetic>` ids skipped |
| Squads in | `plugin`, `squad-board`; live and `_done`. 9 scopes with spend; `plugin/remove-board` has no usage before the cutoff |
| Out | other projects' folders (E1); `wpw-squad` |
| Missing | rosters/usage-events name 153 session ids; 2 have no transcript (`sid-d2`, `sid-m`: test placeholder rows, `missing-transcripts.txt`) |
| Cross-file duplicates | 136 ids appear in two files (resumed/forked copies); counted once, a per-file sum would add $9.78 |
| Naive-sum inflation (T2) | session `47e728f8-…`: 553 usage lines, 299 ids, $23.17 naive vs $12.53 deduped (1.85x); all files 2.00x ([Naive-sum inflation]) |
| Pricing cross-check | Claude Code's own `cost-state.totalCostUSD`, 224 sessions: $306.91, script $293.87 for the same sessions; the $9.78 duplicates explain the gap (cost-state counts resumed copies, is not cutoff-aware) |

Price table ($ per million): sonnet-5-5 in 2 / out 10 / cache read 0.10 / write 5m 2.50 / write 1h 4; opus-5-5 4 / 20 / 0.20 / 5 / 8; haiku-5-5 0.10 / 0.50 / 0.01 / 0.125 / 0.20 (over 100K prompt: 0.50 / 2.50 / 0.05 / 0.625 / 1). Source: vendor page `platform.claude.com/docs/en/about-claude/pricing`, fetched 2026-10-16. The `claude-api` skill's cached table says Sonnet 5.5 cache read $0.20; the vendor page says $0.10 and matches `cost-state` (a fit over 182 sonnet-only sessions gave 0.096), so the vendor page is used. No unpriced model. The Opus price rests on the vendor page alone (no cross-check; within 6% of cost-state). `thinking_tokens` is inside `output_tokens`, not added. `speed`: 10,365 `standard`, 44 lines with no field, none other.

## Attribution (T6)

| Category | Sessions | $ | Share of total |
|---|---|---|---|
| attributed to a scope | 178 | 231.19 | 77.8% |
| non-squad, no `agent-name` (PO / manual) | 27 | 33.13 | 11.1% |
| non-squad, test / probe names | 19 | 4.76 | 1.6% |
| unattributed: squad-level manager (name `manager`, no scope) | 3 | 28.09 | 9.5% |

Roster rows hold a session id for only 66 of 227 sessions; a roster-only attribution would miss **113 of 178** attributed sessions (respawned roles). Transcript names disagree with roster / usage-events 0 times. Role comes from `agent-setting` (`squad:dev` etc.), scope from the roster, else the name pattern ([Attribution coverage]).

## Spend per role, phase, token type, model (AT-01-B2)

| Role | Phase | Sessions | $ | Share of total |
|---|---|---|---|---|
| dev | build | 82 | 97.07 | 32.7% |
| manager | coordination | 18 | 62.23 | 20.9% |
| qa-whitebox | QA | 29 | 35.98 | 12.1% |
| tech-lead | plan | 27 | 33.39 | 11.2% |
| no squad role | none | 33 | 33.15 | 11.2% |
| qa-blackbox | QA | 21 | 24.96 | 8.4% |
| ba | plan | 11 | 8.13 | 2.7% |
| token-coach | retro | 5 | 1.54 | 0.5% |
| designer | plan | 1 | 0.72 | 0.2% |

Phase = role (plan: ba, tech-lead, team-lead, designer; build: dev; QA: qaw, qab; retro: coach; coordination: manager), so it is approximate. By phase: build 32.7%, coordination 20.9%, QA 20.5%, plan 14.2%, none 11.2%, retro 0.5%.

| Token type | Tokens | $ | Share of total |
|---|---|---|---|
| cache read | 1,063,714,540 | 118.36 | 39.8% |
| output (incl. thinking) | 7,009,349 | 76.66 | 25.8% |
| cache write 1h | 14,713,264 | 64.20 | 21.6% |
| cache write 5m | 13,769,085 | 37.90 | 12.8% |
| input, uncached | 22,998 | 0.05 | 0.0% |

Model: sonnet-5-5 81%, opus-5-5 19%, haiku-5-5 0.0% (38 messages, one non-squad session). Opus is the manager ($40.54) and non-squad sessions ($15.38); every other role runs sonnet. Subagents (T3): 40 messages, $1.61 (0.5%), 4 files, all under manager or non-squad sessions; `bin/squad-usage` skips them, so its table misses that sliver ([Subagents]).

## Spread across scopes (T8)

| Scope | Status | Sessions | $ | Share |
|---|---|---|---|---|
| squad-board/board | closed | 79 | 104.64 | 35.2% |
| plugin/po-inbox | closed | 29 | 46.22 | 15.6% |
| plugin/refine-process | closed | 27 | 29.00 | 9.8% |
| squad-board/squad-tabs | live | 18 | 26.31 | 8.9% |
| plugin/board-flakes | closed | 12 | 13.08 | 4.4% |
| squad-board/add-ui-ux-design | closed | 6 | 6.68 | 2.2% |
| squad-board/generic-rules | closed | 4 | 3.21 | 1.1% |
| squad-board/guide | closed | 2 | 1.54 | 0.5% |
| plugin/audit-token | live | 1 | 0.50 | 0.2% |

All scopes: min $0.50 / median $13.08 / max $104.64 (n=9). Closed scopes: min $1.54 / median $13.08 / max $104.64 (n=7). One scope (`board`, 35%) dominates; per session (n=227): min $0.00 / median $0.92 / max $12.53.

## Existing work (T7)

`.scratch/token-coach/spec.md` shipped model per role, the Stop hook, the Coach and the 120k/100k rules. Dates from `git log` (UTC): Token Coach `67a19b6` 2026-10-12T10:32Z; absolute limits `155b5db` 2026-10-14T15:58Z. Measured effect on spend in messages with context over 120k ([Existing work]):

| Window | Messages | $ per 1000 messages | Spend in messages over 120k |
|---|---|---|---|
| before Token Coach | 1,204 | 53.4 | 59.3% |
| Token Coach, percent rules | 5,382 | 26.5 | 39.8% |
| absolute 120k rule | 3,701 | 24.4 | 26.2% |

Not a controlled before/after: later windows hold different tasks and the first window is the board scope's start. Still 39.9% of all spend ($118.58) sits in messages over 120k, so the rule is not obeyed everywhere (manager sessions: 689 such messages, peak context 458k in `47e728f8-…`).

## Top 5 cost drivers (AT-01-B3, B4, T7)

Ranked by the pool each driver touches, as a share of the $297.17 total. "Saving" is a ceiling before the extra cost; the bar is $5.94 (2%) net.

| # | Driver | Pool | Saving ceiling | Net | Class |
|---|---|---|---|---|---|
| 1 | Context carried above 120k | cache read 39.8% / messages over 120k 39.9% | $21.47 (7.2%) | **-$10.15** | minor |
| 2 | Output and thinking | output $76.66 (25.8%), thinking $21.09 (7.1%) | $12.5 (4.2%) | unknown | unproven |
| 3 | 1h cache writes | $64.20 (21.6%) | $24.07 | **-$119.02** | minor (harmful) |
| 4 | Session startup (first 10 messages) | $60.34 (20.3%) | $6.66 (2.2%) | not shown | unproven |
| 5 | Manager on Opus | $40.54 (13.6%) | $20.27 (6.8%) | unknown | unproven |

### 1. Context above 120k: minor

- **Number:** messages with context over 120k cost $118.58 (24.1% for 120-200k, 15.8% over 200k; [Cost by message context size]). Only the *excess* read tokens above 120k would go: $21.47 (7.2%) ([D1]).
- **Fix:** respawn at 120k (the rule exists). The respawns cost $31.62 (sum of floor(peak/120k) per session x the role's mean startup of $0.22-0.43), so net is **-$10.15** over all roles. Only the manager is positive: excess $8.36, respawns $5.21, net **+$3.15 (1.1%)**.
- **Class:** minor (below 2%). The manager part costs no code: process.md Cost rules 2 already says the manager is not exempt; compliance, not a change. Files: none.
- **Metric to move:** manager messages over 120k (689 now), read from `audit-tables.md` [D1].

### 2. Output and thinking: unproven

- **Number:** output $76.66; of it thinking $21.09 (7.1%). Dev at effort `medium` writes 521 output tokens per message against 997 at `high` (same role, same model, 2,462 vs 1,508 messages; task mix differs) ([D5b]). Tech-lead, qa-whitebox, qa-blackbox, ba run `high` on every message ([D5]).
- **Fix:** `effort: medium` for those four roles. Ceiling: their output $26.25 x (1 - 521/997) = **$12.5 (4.2%)**. Net tolerance: it stays a real saving unless extra rework or returns cost more than $6.6.
- **Class:** unproven. RS-3 not shown: QA at `medium` may miss findings. Measure: replay one closed scope's QA task (e.g. `plugin/po-inbox` QA whitebox) at `medium` and compare findings against the `high` run's `qa-w.md`; track first-pass QA PASS rate and QA returns per scope.
- **Files if built (AT-01-B4):** `agents/tech-lead.md`, `agents/qa-whitebox.md`, `agents/qa-blackbox.md`, `agents/ba.md` (`effort:` line). **Role-instruction change: needs PO approval.**

### 3. 1h cache writes: minor, do not build

- **Number:** 1h writes $64.20 (21.6%). At the 5m price the same tokens cost $40.12 (-$24.07), but 503 messages read the cache after a 5-60 minute gap and would rewrite their prefix: +$143.10 ([D3]). Net **-$119.02**.
- **Class:** minor, and counter-productive. Keep the 1h TTL. Whether Claude Code lets the squad choose the TTL was not measured. Files: none.

### 4. Session startup: unproven

- **Number:** the first 10 messages of every session cost $60.34 (20.3%); dev $21.60 (7.3%), mean $0.26 per session ([D2]). 72 dev successor sessions exist; in 25 of them the previous dev session ended **under 100k** context, their startup cost $6.66 (2.2%) ([D2b]). Qa-whitebox: 4 sessions, $0.89; qa-blackbox 3, $0.65; tech-lead 2, $0.54.
- **Fix:** keep a dev on the next ticket of the area (process.md Task lifecycle (3) already says so; wording only). Ceiling $6.66, minus the carried context's re-reads (one read $0.16, more each turn).
- **Class:** unproven: the ceiling is borderline against $5.94 and the cause of the 25 early respawns (ticket area change, machine restart, step-up) is not in the data. Measure: `messages.jsonl` HANDIN / FAIL times against respawn times for those 25 sessions. Files: none (wording in `templates/squad/process.md` only if confirmed).

### 5. Manager on Opus: unproven

- **Number:** manager messages on Opus: 856, $40.54. The same tokens at Sonnet 5.5: $20.27 (-$20.27 = **6.8%**) ([D4]). `agents/manager.md` sets Opus, effort `medium`.
- **Net:** passes RS-2 unless the Sonnet manager adds more than $14.3 (about 70% more tokens) in extra turns or returns.
- **Class:** unproven. RS-3 not shown. Natural experiment in the data: `plugin/po-inbox` (58 Sonnet manager messages) and `squad-board/add-ui-ux-design` (32) ran part of their manager on Sonnet ([D4b]); QA returns of those scopes (`messages.jsonl` lines containing `"FAIL`: 30 and 0) were not compared with Opus-managed scopes. Measure: FAIL count and respawn count per scope by manager model.
- **Files if built:** `agents/manager.md` (`model:`). **Role-instruction change: needs PO approval.**

## Not covered (decisions for Phase B)

- A Haiku fan-out candidate needs the subagent row: only $1.61 (0.5%) of spend is subagent today, so a shift there is a new cost, not a saving (AT-02).
- `squad-usage` skips sidechain lines and roster-less sessions; its table undercounts by the 113 respawned sessions above.
- Non-squad sessions are 12.7% of spend (no scope); out of reach of `process.md`.
