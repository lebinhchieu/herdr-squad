# AT-02 Haiku study

Status: measured on 6 fixtures, 24 runs. **Haiku 5.5 scored 0 defects in 12 of 12 runs, same as Sonnet 5.5, at 7-10% of Sonnet's cost per run.** No Haiku failure occurred, so no guard case exists. RS-2 (share of total spend) from AT-01's `audit.py` at commit def08da (until 2026-10-16T02:00:00Z, total $297.17): only read-only fan-out subagents (0.5%) fall under 2% and are minor.

**Caveats:** n=2 per arm per fixture is small. The fixtures are deterministic and short; a spotless score here says Haiku handles this kind of step, not that it handles every QA or Coach task. Run cost is dominated by Claude Code's own ~13-23k cached prompt tokens, so the real saving on larger sessions is not measured here.

## Method (T1, T3, T4, T5)

- Run date 2026-10-16. Runner `scripts/ab.py`; commands from any directory outside the repo:
  `python3 -I .scratch/audit-token/scripts/ab.py run <candidate> <haiku|sonnet> 2` (3rd arg after candidate and alias is n; optional 5th = first run index), `... rescan`, `... report`. Checks self-test: `python3 -I scripts/selftest_checks.py`.
- Each run: fresh temp dir outside the repo with a copy of `fixtures/<c>/input/`, `fixtures/<c>/prompt.md` on stdin, `claude -p --model <alias> --tools Read,Grep,Glob --allowedTools Read,Grep,Glob --setting-sources "" --strict-mcp-config --disable-slash-commands` (Claude Code 2.1.301, OAuth login, no squad hooks, settings, MCP or skills). Temp dirs removed after each run; only the run's own PID was ever waited on or killed.
- Resolved model ids (from `message.model` in the transcript): alias `haiku` = `claude-haiku-5-5`, alias `sonnet` = `claude-sonnet-5-5`.
- Tokens and cost: read from each run's transcript, deduped by `message.id` (max per field over its lines), subagent files included (none occurred). **The code is a copy of the AT-01 rules, not an import** (AT-01's script is not available to this branch): same dedupe, own price table. Prices USD per 1M tokens, source AT-01's `audit.py` `PRICES` (vendor pricing page, fetched 2026-10-16; the claude-api skill table said 0.20 for Sonnet cache read, so the first scoring was re-run with `ab.py rescan`): Sonnet 5.5 in 2.00 / out 10.00 / cache read 0.10; Haiku 5.5 in 0.10 / out 0.50. **Assumed, not in the table:** Haiku cache read 0.01 (0.1x), cache write 5m 1.25x, 1h 2x of input for both. Haiku's 0.10/0.50 holds for prompts up to 100K tokens; all runs are under it. When AT-01's table differs, re-run `ab.py rescan` after editing `PRICES`.
- Quality: only `fixtures/<c>/checks.py`; no judge-LLM. Per-run defect lists are in `runs/<c>-<arm>-<n>.json` (field `defects`); outputs in `outputs/<c>/<arm>-<n>.txt`; prompt and input in `fixtures/<c>/`.
- Order (T2): `checks.py` for receipt, usage, repoq committed in `aae7b52`; `ab.py` in `1c4675d`; `checks.py` for usage2, repoq2 in `bdb44fc`; all arm outputs are committed after `bdb44fc` (the commit that adds `outputs/` and `runs/`). `checks.py` for receipt2 (good receipt) in `406d441`, before its 4 runs.
- Budget (T8): 12 runs, then +8 and +4 with the Manager's OK (cap 24). Total cost of the study: **$0.2240** (24 runs; `ab.py report`).

## Results (n=2 per arm per fixture)

Cost = cost-weighted USD per run. Defects = checks failed.

| Fixture | Candidate it stands for | Haiku cost (run1, run2) | Sonnet cost (run1, run2) | Haiku / Sonnet | Defects Haiku | Defects Sonnet |
|---|---|---|---|---|---|---|
| receipt | QA receipt check, bad receipt (sha differs, tail FAILED) | 0.00100, 0.00102 | 0.00100, 0.00102 | 0.01346, 0.01346 | 7% | 0, 0 |
| receipt2 | QA receipt check, good receipt (sha equal, clean=yes, tail OK; decoy test names with "FAIL") | 0.00146, 0.00114 | 0.01334, 0.01334 | 10% | 0, 0 | 0, 0 |
| usage | Token Coach / board summary arithmetic (6 roles, 24 rows) | 0.00175, 0.00174 | 0.00175, 0.00174 | 0.01884, 0.01884 | 9% | 0, 0 |
| usage2 | same, harder: 40 rows, top role by cost differs from the largest-token role | 0.00226, 0.00229 | 0.00226, 0.00229 | 0.02464, 0.02512 | 9% | 0, 0 |
| repoq | read-only fan-out subagent (repo question) | 0.00111, 0.00133 | 0.00111, 0.00133 | 0.01264, 0.01275 | 10% | 0, 0 |
| repoq2 | same, decoys: alias import, `reload`, docstring, scripts/, stale docs | 0.00143, 0.00143 | 0.00143, 0.00143 | 0.01917, 0.02048 | 7% | 0, 0 |

Token detail per run: `ab.py report` output in `evidence/AT-02/dev-evidence.md`. Spread between the two runs of an arm is under 5% of cost on every fixture except repoq/haiku (20%: the second run read more files) and repoq2/sonnet (6%).

## Candidates and verdicts

Share column: from AT-01's `audit.py` at def08da (baseline until 2026-10-16T02:00:00Z, total $297.17), tables "Spend per role" and "Subagents". AT-01 gives shares per role, not per activity, so a role share is an upper bound for a candidate that is one activity of that role; only the fan-out and Token Coach rows are measured under 2%. A candidate under 2% of total spend is "minor" and not a go whatever the A/B says. RS-1: measured (above). RS-3: no QA-AC loss on the fixtures. If AT-01's table changes after its own QA, re-check this column.

| Candidate | AT-01 share | Tested by | n per arm | Verdict | Saving per run, fixture (AT-01 unit USD) |
|---|---|---|---|---|---|
| QA receipt checks | QA roles 20.5% of spend (qa-whitebox 12.1% + qa-blackbox 8.4%); the receipt check is a part of that, not isolated | receipt, receipt2 | 2 + 2 | **go**: 0 defects both arms on a bad and a good receipt, so neither always-FAIL nor always-PASS passes; n=2, no clean=no case | 0.0122 |
| Read-only fan-out subagents | 0.5% (Subagents table, all roles; $1.61 of $297.17) | repoq, repoq2 | 2 + 2 | **minor**: under 2% of spend, so not a go whatever the A/B says (A/B: 0 defects both arms) | 0.0115 / 0.0184 |
| Board / log summaries (arithmetic and "top driver" questions) | manager 20.9% of spend; the summary part is not isolated by AT-01 | usage, usage2 | 2 + 2 | **go**: arithmetic over 40 rows correct in both Haiku runs | 0.0171 / 0.0226 |
| Token Coach (full role: ranked process.md proposals) | 0.5% (token-coach role) | not tested | 0 | **minor**: under 2% of spend; also untested (judgement is not checkable by a deterministic check) | n/a |
| Dev / QA whitebox code review | dev 32.7%, qa-whitebox 12.1% | not tested | 0 | **no-go**: nothing tested, so nothing supports a switch | n/a |

**No-go list (AT-02-B4):** none; Haiku got nothing wrong in 12 runs.
**Haiku's limit:** no Haiku failure was found, so this study cannot show where Haiku stops being good enough.
**Guard (AT-02-B3, T6):** no Haiku failure occurred in any run, so a "go with guard" is neither claimed nor proven. These verdicts are "go" on n=2 and zero defects; a "go" rests on two runs per fixture and across five fixtures, which the Manager asked to be flagged as small.

## What is open

- Per-activity shares (receipt checks, summaries) need AT-01 to split a role's spend by activity; not available.
- A harder fixture that Haiku fails would give the guard case; none of the five did.
- Not done: tool calls beyond Read/Grep/Glob (Bash, Edit) and long inputs (the squad's real receipts and transcripts, kept out by T10).
