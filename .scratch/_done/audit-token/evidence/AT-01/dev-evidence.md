# AT-01 dev evidence

- Base sha: 39ab34af35654aa1bc758b4d80723013e4752bb9 (QA: `git diff --stat 39ab34a..HEAD` shows only `.scratch/audit-token/`)
- Command: `python3 -I .scratch/audit-token/scripts/audit.py --until 2026-10-16T02:00:00Z` (twice, byte-identical `audit-tables.md` and `audit-tables.json`)
- Selftest: `evidence/AT-01/selftest.txt` (SELFTEST PASS)
- Suite: `python3 tests/run_suite.py --receipt .scratch/audit-token/evidence/AT-01 --if-changed 39ab34a`: 1136 tests OK; browser files skipped (no browser test or watched source changed). Receipts `suite-default.txt`, `suite-tz.txt`. No `tests/` change.

## git diff --stat 39ab34a..HEAD (before this file)
```
 .scratch/audit-token/audit-tables.json             | 224 ++++++
 .scratch/audit-token/audit-tables.md               | 268 +++++++
 .scratch/audit-token/audit.md                      | 141 ++++
 .../evidence/AT-01/missing-transcripts.txt         |  17 +
 .../evidence/AT-01/sample-idle-manager.txt         |   8 +
 .../evidence/AT-01/sample-long-manager.txt         | 301 ++++++++
 .scratch/audit-token/evidence/AT-01/selftest.txt   |   7 +
 .../audit-token/evidence/AT-01/suite-default.txt   |  50 ++
 .scratch/audit-token/evidence/AT-01/suite-tz.txt   |   2 +
 .scratch/audit-token/scripts/audit.py              | 766 +++++++++++++++++++++
 .../scripts/fixtures/session-fixture.jsonl         |   8 +
 11 files changed, 1792 insertions(+)
```

## Five numbers to spot-check (all in `audit-tables.md`; per-message rows via `--show-session <id>`)
| # | Number | Where | Raw lines |
|---|---|---|---|
| 1 | Total $297.17, 10,287 ids, 19,331 lines | Baseline | all 244 files under `/home/chieule/.claude/projects/-home-chieule-workspace-squad*/` (glob `-home-chieule-workspace-squad*`), `*.jsonl` incl. `<session>/subagents/*.jsonl` |
| 2 | Long session 47e728f8-9cab-47fb-aa7d-6ce6b65d435f: 553 lines, 299 ids, $12.53; naive $23.17 | Naive-sum inflation; `sample-long-manager.txt` | `/home/chieule/.claude/projects/-home-chieule-workspace-squad/47e728f8-9cab-47fb-aa7d-6ce6b65d435f.jsonl`; first id and last id in the sample file (msg_011Cfzvpr... ends it) |
| 3 | Idle manager aa3c4b35-9038-4e63-8d2e-2b36399ca7e5: 6 ids, $0.4235 | `sample-idle-manager.txt` | `/home/chieule/.claude/projects/-home-chieule-workspace-squad/aa3c4b35-9038-4e63-8d2e-2b36399ca7e5.jsonl`; ids msg_011Cfxnwaz... to msg_011CfxnyyK... |
| 4 | Manager Opus messages 856, $40.54 (D4) | D4 table | sessions with `agent-setting squad:manager`, model claude-opus-5-5 |
| 5 | Messages over 120k context: $118.58 (24.1% + 15.8%); dev role $97.07 (32.7%) | Cost by message context size; Spend per role | rows with ctx = input + cache read + cache write > 120000 |

Dedupe check: msg ids on several lines (553 lines for 299 ids in #2); `scripts/fixtures/session-fixture.jsonl` msg_A has 3 lines, max-fold out 90.
