# QA blackbox, task 10 (HANDIN d792d78, branch squad/plugin/drop-scope-size/plugin-dev-dsz-10)

Method: `bin/squad-team add|remove ROLE --home D` on scratch `scope.md` files (mktemp dir), CLI only, no code read. AC judged: 16(d), 17, 19, 30, 22-style refusals; 16(a-c,e,f) and 18 are Manager steps (live run L).

| AC | Did | Saw | Result |
|---|---|---|---|
| 16(d) | `team: team-lead, qa-white`, `add ba` | `scope.md` team: `ba, team-lead, qa-white`; prints `duty business-ac: ticket -> ba`, `duty doubt-owner: manager -> ba`, `spawn: ba`, `respawn: manager, team-lead`; other scope.md lines (`goal`, `model dev`, `touches`) untouched | PASS (respawn list accuracy: judge in live run L, branch rules are not integrated yet) |
| 17 | `add designer`, `add architect` without `--po-ok` | exit 2 `adding designer waits for the PO's yes; ask the PO, then add --po-ok`; team: unchanged | PASS |
| 17 | `add designer --po-ok` | exit 0, team gains `designer`, `spawn: designer` | PASS |
| 19 | `remove ba` without `--at-boundary` | exit 2 `remove only at an iteration boundary with the PO's OK`; unchanged | PASS |
| 19 | `remove ba --at-boundary` | exit 0, team drops `ba`; prints `duty business-ac: ba -> ticket`, `duty doubt-owner: ba -> manager`, `retire: ba`, respawn list | PASS |
| 19 | `remove qa-white --at-boundary` (team `team-lead`) | each duty it held with new owner (`tech-ac -> dev`, `code-check -> manager`, `handin-target: qas -> team-lead` ...), `retire: qa-whitebox` | PASS |
| 30 | `add wizard`; `add qa-whitebox` (already on team as qa-white); `add dev`; `remove tech-lead` (not on team) | exit 2 each, clear text, unchanged | PASS |
| dry-run | `add ba --dry-run`, `remove team-lead --at-boundary --dry-run` | prints plan + `dry run: scope.md not changed`; file unchanged | PASS |
| 22/26 | `size: L` scope; blank `team:` | exit 2 pointing at `squad-process adopt` / "the team is undecided; the Manager writes the first `team:`" | PASS |
| G7 | `team: ba; touch X` | exit 2 unknown token, X not created | PASS |

Not observed: that the respawn list equals exactly the roles whose composed text changes (the task branch still composes old-size rule text until 06/07/08 merge). Check in live run L on the integration sha.

## Findings
None so far. Verdict waits for the Tech Lead's final sha (REV-3).
