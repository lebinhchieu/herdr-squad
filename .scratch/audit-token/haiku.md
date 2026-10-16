# AT-02 Haiku study

Status: measured on 5 fixtures, 20 runs. **Haiku 5.5 scored 0 defects in 10 of 10 runs, same as Sonnet 5.5, at 7-10% of Sonnet's cost per run.** No Haiku failure occurred, so no guard case exists. RS-2 (share of total spend) from AT-01's `audit.py` at commit def08da (until 2026-10-16T02:00:00Z, total $297.17): only read-only fan-out subagents (0.5%) fall under 2% and are minor.

**Caveats:** n=2 per arm per fixture is small. The fixtures are deterministic and short; a spotless score here says Haiku handles this kind of step, not that it handles every QA or Coach task. Run cost is dominated by Claude Code's own ~13-23k cached prompt tokens, so the real saving on larger sessions is not measured here.

## Method (T1, T3, T4, T5)

- Run date 2026-10-16. Runner `scripts/ab.py`; commands from any directory outside the repo:
  `python3 -I .scratch/audit-token/scripts/ab.py run <candidate> <haiku|sonnet> 2` (3rd arg after candidate and alias is n; optional 5th = first run index), `... rescan`, `... report`. Checks self-test: `python3 -I scripts/selftest_checks.py`.
- Each run: fresh temp dir outside the repo with a copy of `fixtures/<c>/input/`, `fixtures/<c>/prompt.md` on stdin, `claude -p --model <alias> --tools Read,Grep,Glob --allowedTools Read,Grep,Glob --setting-sources "" --strict-mcp-config --disable-slash-commands` (Claude Code 2.1.301, OAuth login, no squad hooks, settings, MCP or skills). Temp dirs removed after each run; only the run's own PID was ever waited on or killed.
- Resolved model ids (from `message.model` in the transcript): alias `haiku` = `claude-haiku-5-5`, alias `sonnet` = `claude-sonnet-5-5`.
- Tokens and cost: read from each run's transcript, deduped by `message.id` (max per field over its lines), subagent files included (none occurred). **The code is a copy of the AT-01 rules, not an import** (AT-01's script is not available to this branch): same dedupe, own price table. Prices USD per 1M tokens, source AT-01's `audit.py` `PRICES` (vendor pricing page, fetched 2026-10-16; the claude-api skill table said 0.20 for Sonnet cache read, so the first scoring was re-run with `ab.py rescan`): Sonnet 5.5 in 2.00 / out 10.00 / cache read 0.10; Haiku 5.5 in 0.10 / out 0.50. **Assumed, not in the table:** Haiku cache read 0.01 (0.1x), cache write 5m 1.25x, 1h 2x of input for both. Haiku's 0.10/0.50 holds for prompts up to 100K tokens; all runs are under it. When AT-01's table differs, re-run `ab.py rescan` after editing `PRICES`.
- Quality: only `fixtures/<c>/checks.py`; no judge-LLM. Per-run defect lists are in `runs/<c>-<arm>-<n>.json` (field `defects`); outputs in `outputs/<c>/<arm>-<n>.txt`; prompt and input in `fixtures/<c>/`.
- Order (T2): `checks.py` for receipt, usage, repoq committed in `aae7b52`; `ab.py` in `1c4675d`; `checks.py` for usage2, repoq2 in `bdb44fc`; all arm outputs are committed after `bdb44fc` (the commit that adds `outputs/` and `runs/`).
- Budget (T8): 12 runs, then +8 with the Manager's OK (cap 20). Total cost of the study: **$0.1947** (20 runs; `ab.py report`).

## Results (n=2 per arm per fixture)

Cost = cost-weighted USD per run. Defects = checks failed.

| Fixture | Candidate it stands for | Haiku cost (run1, run2) | Sonnet cost (run1, run2) | Haiku / Sonnet | Defects Haiku | Defects Sonnet |
|---|---|---|---|---|---|---|
| receipt | QA receipt check | 0.00100, 0.00102 | 0.00100, 0.00102 | 0.01346, 0.01346 | 7% | 0, 0 |
| usage | Token Coach / board summary arithmetic (6 roles, 24 rows) | 0.00175, 0.00174 | 0.00175, 0.00174 | 0.01884, 0.01884 | 9% | 0, 0 |
| usage2 | same, harder: 40 rows, top role by cost differs from the largest-token role | 0.00226, 0.00229 | 0.00226, 0.00229 | 0.02464, 0.02512 | 9% | 0, 0 |
| repoq | read-only fan-out subagent (repo question) | 0.00111, 0.00133 | 0.00111, 0.00133 | 0.01264, 0.01275 | 10% | 0, 0 |
| repoq2 | same, decoys: alias import, `reload`, docstring, scripts/, stale docs | 0.00143, 0.00143 | 0.00143, 0.00143 | 0.01917, 0.02048 | 7% | 0, 0 |

Token detail per run: `ab.py report` output in `evidence/AT-02/dev-evidence.md`. Spread between the two runs of an arm is under 5% of cost on every fixture except repoq/haiku (20%: the second run read more files) and repoq2/sonnet (6%).

## Candidates and verdicts

Share column: AT-01 spend row `pending` for every row (AT-01's script is not merged here). A candidate under 2% of total spend is "minor" and not a go whatever the A/B says. RS-1: measured (above). RS-3: no QA-AC loss on the fixtures.

| Candidate | AT-01 share | Tested by | n per arm | Verdict | Saving per run, fixture (AT-01 unit USD) |
|---|---|---|---|---|---|
| QA receipt checks | pending | receipt | 2 | **go (RS-2 pending)**: 0 defects both arms, n=2 and the checks are a pass/fail on a planted sha mismatch and a "FAILED" tail | 0.0133 |
| Read-only fan-out subagents | pending | repoq, repoq2 | 2 + 2 | **go (RS-2 pending)** for fixed-answer lookups only; no Haiku failure, so no guard needed | 0.0124 / 0.0195 |
| Board / log summaries (arithmetic and "top driver" questions) | pending | usage, usage2 | 2 + 2 | **go (RS-2 pending)**: arithmetic over 40 rows correct in both Haiku runs | 0.0180 / 0.0234 |
| Token Coach (full role: ranked process.md proposals) | pending | not tested | 0 | untested: not a go (judgement quality is not checkable by a deterministic check; the usage fixtures cover only its arithmetic step) | n/a |
| Dev / QA whitebox code review | pending | not tested | 0 | untested: not a go | n/a |

**No-go list (AT-02-B4):** none; Haiku got nothing wrong in 10 runs.
**Guard (AT-02-B3, T6):** no Haiku failure occurred in any run, so a "go with guard" is neither claimed nor proven. These verdicts are "go" on n=2 and zero defects; a "go" rests on two runs per fixture and across five fixtures, which the Manager asked to be flagged as small.

## What is open

- Fill the share column and apply RS-2 once AT-01's script is merged; any candidate below 2% flips to minor. The saving per run in the last column is per fixture run, not per squad: the AT-01 unit conversion needs AT-01's per-role session counts.
- A harder fixture that Haiku fails would give the guard case; none of the five did.
- Not done: tool calls beyond Read/Grep/Glob (Bash, Edit) and long inputs (the squad's real receipts and transcripts, kept out by T10).
