# AT-02 dev evidence

Base sha: 39ab34af35654aa1bc758b4d80723013e4752bb9 (main at spawn). Run date 2026-10-16.

## Commands
```
python3 -I .scratch/audit-token/scripts/selftest_checks.py
python3 -I .scratch/audit-token/scripts/ab.py run <receipt|usage|usage2|repoq|repoq2> <haiku|sonnet> 2   # from /tmp
python3 -I .scratch/audit-token/scripts/ab.py rescan; ... report
```

## Checks self-test (good passes, bad fails)
```
receipt: good->[] bad->['wrong_sha_match', 'wrong_ok_line', 'wrong_verdict'] OK
repoq: good->[] bad->['false_caller', 'missed_caller', 'wrong_timeout'] OK
repoq2: good->[] bad->['false_caller', 'missed_caller', 'wrong_timeout'] OK
usage: good->[] bad->['wrong_top_role', 'wrong_total'] OK
usage2: good->[] bad->['wrong_top_role', 'wrong_top_role_cost'] OK
```

## sha order (T2)

- aae7b52 AT-02: fixtures and checks (with self-test) before any arm run
- 1c4675d AT-02: ab.py runner
- bdb44fc AT-02: harder fixtures usage2 and repoq2 with checks and self-test,...
- efa0f6c AT-02: arm outputs, run records, haiku.md

## Per-run defect table (ab.py report)

| candidate | arm | run | model id (transcript) | in | cache_r | cache_w | out | cost USD | defects |
|---|---|---|---|---|---|---|---|---|---|
| receipt | haiku | 1 | claude-haiku-5-5 | 4 | 9457 | 3482 | 408 | 0.00100 | none |
| receipt | haiku | 2 | claude-haiku-5-5 | 4 | 9461 | 3490 | 445 | 0.00102 | none |
| receipt | sonnet | 1 | claude-sonnet-5-5 | 4 | 8683 | 2712 | 174 | 0.01433 | none |
| receipt | sonnet | 2 | claude-sonnet-5-5 | 4 | 8683 | 2712 | 174 | 0.01433 | none |
| repoq | haiku | 1 | claude-haiku-5-5 | 4 | 9388 | 3711 | 556 | 0.00111 | none |
| repoq | haiku | 2 | claude-haiku-5-5 | 6 | 16243 | 4199 | 657 | 0.00133 | none |
| repoq | sonnet | 1 | claude-sonnet-5-5 | 4 | 8608 | 2509 | 174 | 0.01351 | none |
| repoq | sonnet | 2 | claude-sonnet-5-5 | 4 | 8608 | 2546 | 170 | 0.01361 | none |
| repoq2 | haiku | 1 | claude-haiku-5-5 | 8 | 23389 | 4325 | 653 | 0.00143 | none |
| repoq2 | haiku | 2 | claude-haiku-5-5 | 8 | 23395 | 4331 | 657 | 0.00143 | none |
| repoq2 | sonnet | 1 | claude-sonnet-5-5 | 6 | 14648 | 3327 | 438 | 0.02063 | none |
| repoq2 | sonnet | 2 | claude-sonnet-5-5 | 6 | 14673 | 3347 | 561 | 0.02194 | none |
| usage | haiku | 1 | claude-haiku-5-5 | 4 | 9435 | 3741 | 1804 | 0.00175 | none |
| usage | haiku | 2 | claude-haiku-5-5 | 4 | 9435 | 3741 | 1797 | 0.00174 | none |
| usage | sonnet | 1 | claude-sonnet-5-5 | 4 | 8657 | 2963 | 611 | 0.01970 | none |
| usage | sonnet | 2 | claude-sonnet-5-5 | 4 | 8657 | 2963 | 611 | 0.01970 | none |
| usage2 | haiku | 1 | claude-haiku-5-5 | 4 | 9443 | 4091 | 2690 | 0.00226 | none |
| usage2 | haiku | 2 | claude-haiku-5-5 | 4 | 9441 | 4087 | 2759 | 0.00229 | none |
| usage2 | sonnet | 1 | claude-sonnet-5-5 | 4 | 8663 | 3309 | 1053 | 0.02551 | none |
| usage2 | sonnet | 2 | claude-sonnet-5-5 | 4 | 8663 | 3309 | 1101 | 0.02599 | none |

study total cost USD: 0.2046 over 20 runs

Defects: none in any of the 20 runs; per-run lists in runs/*.json.

## Total study cost

$0.2046 over 20 runs (12 + 8 approved by the Manager).

## Notes
- First pass of ab.py mis-located 3 transcripts (temp dir name encoding); fixed by finding the transcript by session id, then `rescan`. No re-runs, no cost double counted.
- 20 transcripts remain under ~/.claude/projects/-tmp-at02-*-work for QA to verify; temp work dirs removed. Read-only.

## git diff --stat 39ab34a..HEAD
```
 86 files changed, 1017 insertions(+)
only paths under .scratch/audit-token/ (checked: 0 others)
```
