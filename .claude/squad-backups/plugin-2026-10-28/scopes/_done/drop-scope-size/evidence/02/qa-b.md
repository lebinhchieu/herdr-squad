# QA blackbox, task 02 (code sha 08ecf4f, branch squad/plugin/drop-scope-size/plugin-dev-dsz-2)

Scratch homes = temp dirs with a hand-made `scope.md`; command `squad-process compose <role> --home D --plugin-root <worktree>`. CLI only, no screenshots. Verdict waits for the Tech Lead to name the final sha (REV-3).

| Case (`team:` line) | Saw | Result |
|---|---|---|
| `ba, tech-lead, qa-white` | exit 0; header `team: ba, tech-lead, qa-white`; `duties:` line present | PASS |
| `none` | exit 0; header `team: none` | PASS |
| blank / no `team:` line | exit 0; header `team: undecided` | PASS |
| trailing note `ba, qa-white (PO ..., no tech)` | exit 0; tokens `ba, qa-white` | PASS |
| CRLF file | exit 0; tokens parsed | PASS |
| unknown `wizard` | exit 2, `scope.md:3: unknown team token 'wizard' (allowed: ...)` (AC 30) | PASS |
| duplicate `ba, ba` | exit 2, `scope.md:3: team token 'ba' listed twice` (AC 30) | PASS |
| `qa-whitebox` / `qa-blackbox` | exit 2, `... is a role name; write 'qa-white'` / `'qa-black'` (AC 27) | PASS |
| `qa-b` | exit 2, unknown token (AC 27) | PASS |
| `manager, ba` | exit 2, `'manager' is always on the team` | PASS |
| `team: ba` + `size: M` / `qa-b: no` | exit 2, `scope.md:N: old line ... beside team:; the team line decides, delete the old line by hand`, no adopt pointer (dev's case) | PASS |
| hostile `qa-white; touch /tmp/PWNED` | exit 2 unknown token; `/tmp/PWNED` not created | PASS |
| legacy `size: M` only | still composes, header `size M` (transitional) | as expected, see below |

`duties:` line (Manager rules) for the six shapes of the spec reference vs today's SIZE-22/22a, checked by eye:
- none (S), `qa-white, qa-black` (M), `ba, team-lead, tech-lead, qa-white, qa-black` (L): owners match today's table. For S, code-check and behaviour-check read `manager` (Manager confirms the Developer's evidence, as AC 13).
- L without qa-black: behaviour-check `qa-white`, ui-check `manager`.
- M + designer: ui-check `qa-black`. M + architect: choice-owner `architect`.
- The `duties:` line has the 13 duties only; AC 9 also names an "Architecture" owner with an Architect. Not on the line: QA whitebox asserts the exact table. I report it, not a FAIL for 02.

Not yet true, by design (rules retarget in 04a-06; Tech Lead accepted as transitional): composed rules for a decided-team home still carry `[if size ...]` blocks (AC 11b) and legacy `size: M` homes still compose (AC 26 comes with 04). These are open ACs, not 02 failures.
