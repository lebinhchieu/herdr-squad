# QA blackbox, INT3 (HANDIN 32aa75b, branch squad/plugin/drop-scope-size/plugin-dev-dsz-int3: 07 + 08 on fed0c95)

Method: CLI only. Scratch homes (`scope.md` with `plugin: 0.6.0 abc1234`, `team:`), `squad-process compose` for 9 roles, `lint`, `squad-team add|remove` with respawn list vs composed-text change per role (script `/tmp/qabint2.scripts/try.sh`). 08's f041603 is in the branch.

| Check | Saw | Result |
|---|---|---|
| Compose 9 roles x 12 team shapes (none, qa-white, qa-black, both, team-lead, team-lead+qa-white, tech-lead, ba, designer+QAs, architect+QAs, full L, team-lead+tech-lead+qa-white+ba) | no compose failure | PASS |
| `lint` per shape | empty | PASS |
| `squad-team add` qa-white / tech-lead / team-lead / designer / architect | respawn list = Manager, Developer, plus every other on-team role whose composed text changed (e.g. add tech-lead to team-lead,qa-white: manager, team-lead, qa-whitebox, dev); added role spawned | PASS |
| `squad-team remove` qa-black / tech-lead / team-lead | without flags rc=2 "only at an iteration boundary with the PO's OK"; with `--at-boundary --po-ok` retire + respawn list equals on-team roles with changed text | PASS |
| 07 + 08 together | 08's SUITE-2f, COST-4c present as on 08 branch; owner pairs and suite owners unchanged by the merge | PASS |
| Word `size` vs INT2, full L, per role | drops from 85/29/33/38/31/16/68/17/14 to 44/1/7/5/5/8/38/3/3 lines (manager/dev/team-lead/qa-w/qa-b/ba/tech/designer/architect); the rest are SIZE-n rule ids, CORE-3 "scope size" and the WHO-1 text, owned by tickets 11/12 | not 07/08's |

Findings: none for INT3. Verdict waits for the Tech Lead's final sha (REV-3).

## Re-check, 90be196 (delta from 32aa75b)
Diff: tests/test_squadruntime.py (+5) and the ticket evidence.md note only. Compose of 9 roles on 5 shapes (none, both QAs, tech-lead, full L, 4-role) byte-identical to 32aa75b; lint empty. Findings: none. Verdict waits for the Tech Lead final sha.
