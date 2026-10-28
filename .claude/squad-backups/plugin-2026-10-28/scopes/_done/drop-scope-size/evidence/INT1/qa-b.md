# QA blackbox, INT1 integration (code 8546384, handin e3cc702 / 8fa0aa0, merges 03, 05, 09)

Smoke on the merged branch with scratch homes (`team: none`; `qa-white, qa-black`; `ba, team-lead, tech-lead, qa-white, qa-black`; `qa-white, qa-black, designer`): `squad-process compose` for manager, dev, team-lead, qa-whitebox, qa-blackbox, ba, tech-lead.

| Check | Saw | Result |
|---|---|---|
| Compose, 4 shapes x 7 roles | exit 0 everywhere | PASS |
| `squad-process team --home` | prints each team; undecided when no `team:` | PASS |
| `duties:` line | S: manager/dev/dev/ticket/manager...; M: qa-white, qa-black checks; L: team-lead, tech-lead, ba; with designer ui-check qa-black | PASS |
| Done text | S has TEAM-3 (no QA) | PASS |
| `squad-process lint` | exit 0 | PASS |

Not retested (unchanged by the merge, passed per task): 03 converter, 09 report and rollup (my tasks' evidence). A try of `adopt` on a hand-made fake squad failed on my fake `process.md` (version 1, no line map); my setup, not a product finding.
