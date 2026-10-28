# QA blackbox, INT2 integration (handin fed0c95: 04 b2dcc52 + 10 d792d78 + 06 bd361cf onto 6389642; 07 and 08 not in)

Method: scratch homes (scope.md with `plugin: 0.6.0 abc1234` + `team:`), the branch's `squad-process`, `squad-team`, `squad-spawn --dry-run`, `squad-log-message`. CLI only, no code read.

| Check | Saw | Result |
|---|---|---|
| Compose, 9 teams (none; qa-white,qa-black; team-lead; team-lead,qa-white; full L; qa-white; qa-black; designer+QAs; blank) x 9 roles | exit 0 everywhere | PASS |
| `squad-process lint`, each team | no output | PASS |
| `squad-process team --home` | prints the team; `undecided` when blank, `none` when none | PASS |
| `squad-team` refusals (task 10) | `add designer` w/o `--po-ok` waits for PO; unknown role, `dev`, already-on-team, `remove` w/o `--at-boundary`, `size:` scope (adopt pointer), blank team: exit 2, scope.md unchanged; `--dry-run` leaves file unchanged | PASS |
| `squad-team add|remove` (10) | 10 add/remove runs rc 0; prints `spawn:`/`retire:`/`respawn:` and duty moves | PASS |
| Spawn gate (04) | `size: M` -> exit 2 adopt pointer; `team: team-lead, qa-white`: manager, dev ok, ba and qa-blackbox exit 1 "not on the team"; blank team: ba refused, manager ok; hostile `team: ba; touch HOST` exit 2, file not created | PASS |
| Hook (04) | 3 HANDIN/FAIL pairs (7-hex shas) with `team: qa-white` -> only 3rd FAIL prints `hookSpecificOutput.additionalContext` ... to Manager [LC-7c] | PASS |

## Not judged here (known, by design)
- Respawn-list accuracy of `squad-team` (does it equal the roles whose composed text changes): the merged branch still holds size-keyed lifecycle/review rules (07 excluded; dev text is the same for `team: none` and `team: qa-white`). Judge on INT3 (07 0f1dc44 + 08) and live run L.
- Rules of 07/08 files.

Findings: none. Verdict waits for the Tech Lead's final sha.

Verdict: PASS on fed0c95 (Tech Lead final). Developer plugin-dev-dsz-int2 unreachable; told Team Lead.
