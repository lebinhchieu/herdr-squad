# QA blackbox, INT4 (HANDIN 964c443, branch squad/plugin/drop-scope-size/plugin-dev-dsz-int4: 11 + 14 on 90be196)

Method: CLI only. `git archive 964c443` to scratch; scratch homes (`scope.md` with `plugin: 0.6.0 abc1234`, `team:`); `squad-process compose` for 9 roles; `lint`; 512-compose Developer sweep; composed text diffed against 90be196 and ca53ba7 (11 final).

| Check | Saw | Result |
|---|---|---|
| Compose 9 roles x 12 team shapes (as INT3) | 0 compose failures | PASS |
| `lint` per shape | empty | PASS |
| AC 24 sweep, 128 teams x goal x qa | 512/512 OK, max Developer file 5034 B, 0 over 5120 | PASS |
| 11 content kept | REV-22a "Give the review subagent ... to check the diff conforms."; EVID-2b "After all `PASS`:"; changelog rows for both | PASS |
| 14 content kept | SAFE-10 "no setting enforces this", SAFE-11 "Scratch dirs: `mktemp -d` only" in qa-blackbox/dev files; changelog rows for SAFE-10, SAFE-11 | PASS |
| INT4 vs ca53ba7 composed text | only the SAFE-10 / SAFE-11 lines differ (14's change) on 3 shapes | PASS |
| Changelog v9 merge | rows of 11 and 14 both present, no conflict markers | PASS |

Findings: none. Verdict waits for the Tech Lead's final sha (REV-3).

## Re-check, 2175bd2 (delta from 964c443)
Diff: tests/test_team_lead_perms.py (+1) and the ticket evidence.md only. Compose of 9 roles on 3 shapes (none, tech-lead+qa-white, full 7-role team): bodies byte-identical to 964c443 (header scope name and timestamp excluded); lint empty. Saved composes: /tmp/qab-int4-composes/. Findings: none. Verdict waits for the Tech Lead's final sha.
