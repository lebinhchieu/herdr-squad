# QA blackbox, task 07 (HANDIN 426706d, branch squad/plugin/drop-scope-size/plugin-dev-dsz-07)

Method: scratch homes (`plugin: 0.6.0 abc1234` + `team:`) for 9 teams (none; qa-white,qa-black; L; L without qa-black; M+designer; M+architect; qa-white; qa-black; blank), `squad-process compose <role> --home D --plugin-root <worktree>` for 9 roles, `squad-process lint`. Judged only 07's files (lifecycle.md, review.md, evidence.md); the other files on this branch still hold old size text until 05/06/08 merge. CLI only, no code read.

| Check | Saw | Result |
|---|---|---|
| Compose, 9 teams x 9 roles | exit 0 everywhere | PASS |
| `squad-process lint` | no output | PASS |
| Word "size" / `[if ...` / `qa-b` as a key in LC-, REV-, EVID- blocks of decided teams | none (hits are `[SIZE-2]` rule references and the file name `qa-b.md`) | PASS |
| `when:` lines of the three files | team facts only (`plan-owner = ...`, `design = yes`, `handin-target = qas`) | PASS |
| AC 12/14: both QAs, with Team Lead and without | Dev: `REV-13b Hand in, both QAs`; `LC-20b Done, Team Lead` / `LC-20a Done, Manager`: "Done when every checker sent PASS. Tell the Team Lead|Manager" | PASS |
| AC 12 3 returns | no Team Lead: `LC-7a Three returns, Manager` (3rd failing checker sends the Manager `BLOCKED NN: 3 returns`); Team Lead: `LC-7b`; QA: `LC-7c` to the plan owner | PASS |
| AC 13 no QA blackbox | `qa-white` only / L without qa-black: Dev `REV-19b Hand in, QA whitebox alone`; QA whitebox `REV-20 Behaviour check`: "There is no QA blackbox: ... check each business AC against the Developer's ## Behaviour ... Your PASS is Done" | PASS |
| AC 13 no QA | `team: none`: Dev `REV-13a Hand in, Manager`; Manager `REV-1 Confirmation` (open evidence.md, confirm `## Behaviour` and `## Review`, your PASS) and `EVID-3a Review record without a QA` | PASS |
| qa-black alone | Dev `REV-13d Hand in, QA blackbox alone`; Team Lead `EVID-8 Reviewer file, QA blackbox alone` | PASS |
| Reviewer file rules | both: `qa-w.md and qa-b.md are the reviewer files`; whitebox alone: "qa-w.md is the only reviewer file; no qa-b.md is expected" | PASS |
| Blank team (undecided) | composes; `[if` tags allowed there | PASS |

Not checked (not mine): 5 KiB Dev-rules tests (Dev says red on base, ticket 11); `[if size` in other files (05/06/08).

## Findings
None. Verdict waits for the Tech Lead's final sha (REV-3).

## Re-check on c5dd6ce (diff 426706d..c5dd6ce; lifecycle.md, review.md)

Method: 10 scratch homes (scope.md `team:` none / qa-white,qa-black / team-lead / team-lead,qa-white / full L / L without qa-black / qa-white / qa-black / tech-lead / blank), `squad-process compose <role> --home D --plugin-root <worktree>` for dev, manager, team-lead, qa-whitebox, qa-blackbox, tech-lead; `squad-process lint`.

| Check | Saw | Result |
|---|---|---|
| Compose, 10 teams x 6 roles | exit 0 everywhere | PASS |
| `lint` | no output, rc 0 | PASS |
| Three returns, no QA (`none`, `tech-lead`) | Manager gets `LC-7a Three returns, Manager` ("you step in; your own 3rd FAIL counts"); no `BLOCKED` sender line | PASS |
| Three returns with Team Lead | Manager `LC-7b [aware]`, Team Lead `LC-7b`; no LC-7a | PASS |
| Three returns with QAs | both QAs `LC-7c`: 3rd failing QA sends the plan owner `BLOCKED NN: 3 returns` (also with qa-white alone, qa-black alone) | PASS |
| Done: no QA/no TL | Dev only `LC-20a`: "Done when the Manager sent PASS" | PASS |
| Done: any QA | Dev only `LC-20b Done, QAs`: "every checker sent PASS. Tell the plan owner" | PASS |
| Done: `team-lead` alone | Dev only `LC-20e`: "Done when the Team Lead sent PASS" | PASS |
| Hand-in rules unchanged | `REV-13a` none/tech, `REV-13c` tl, `REV-13b` both QAs, `REV-13d` qb, `REV-19b` qw | PASS |
| REV-14a diff check | Dev, all teams: "...; with QAs on the team, tell the plan owner after every checker passes it" | PASS |
| REV-3b Final sha `[aware]` | Manager sees it when no Tech Lead (all teams but `tech-lead`); QAs see it, Manager-aware tag present | PASS |
| Blank team | composes; `[if handin-target = ...]` tags kept (undecided) | PASS |
| Word `size` / `[if size` in LC/REV/EVID | none in 07's three files (hits only COST-/ITER-/SIZE- rules of tickets 08/06) | PASS |

Findings: none. Verdict waits for the Tech Lead's final sha (REV-3).

## Correction (after Tech Lead DECISION 07)
My c5dd6ce re-check marked "Three returns" PASS too early. My own compose output showed it: for `qa-white, qa-black`, `qa-white` and `qa-black` (QAs, no Team Lead) `manager` listed only `REV-3b`; no three-returns rule, although `LC-7c` sends it `BLOCKED NN: 3 returns` (AC 12). Same for `tech-lead`-less QA teams. c5dd6ce is not final. Re-test on the new sha: compose manager for `qa-white, qa-black` and `qa-white`/`qa-black`, with and without `team-lead`.

## Re-check on 0f1dc44 (diff c5dd6ce..0f1dc44)

Method: 15 scratch homes (none; tech-lead; team-lead; team-lead,qa-white; team-lead,qa-black; team-lead,qa-white,qa-black; qa-white; qa-black; qa-white,qa-black; tech-lead+QAs; designer+QAs; architect+qa-white; full L; L without qa-black; blank), `squad-process compose` for dev, manager, team-lead, qa-whitebox, qa-blackbox, tech-lead; `lint`.

| Check | Saw | Result |
|---|---|---|
| Compose 15 teams x 6 roles | exit 0 everywhere; lint rc 0, no output | PASS |
| AC 12 Manager three-returns, QAs and no Team Lead (`qa-white,qa-black`, `qa-white`, `qa-black`, +designer / architect / tech-lead) | Manager has `LC-7a Three returns, Manager`: "you step in; with QAs on the team the 3rd failing QA sends you `BLOCKED NN: 3 returns`, and your own 3rd FAIL counts" | PASS |
| Same with Team Lead (`team-lead,qa-white,qa-black`, `team-lead,qa-black`, L) | Manager `LC-7b [aware]`, Team Lead `LC-7b`; no LC-7a | PASS |
| No QA (`none`, `tech-lead`) | Manager `LC-7a` | PASS |
| QA side | both QAs `LC-7c`: 3rd failing QA sends the plan owner `BLOCKED NN: 3 returns` | PASS |
| REV-3b | QAs: "final sha is the one in the Developer's latest HANDIN, unless [REV-3] names another ... each QA sends a single verdict"; Manager no longer sees it (aware tag removed) in any shape; blank team keeps `[if handin-target = qas]` | PASS |
| Earlier rows (LC-20a/b/e, REV-13a-d, REV-19b, REV-14a) | unchanged per shape | PASS |
| `size` / `[if size` in 07's LC/REV/EVID rules | none (hits only SUITE/COST/ITER/NOTE rules of other tickets) | PASS |

Findings: none. Verdict waits for the Tech Lead's final sha.
