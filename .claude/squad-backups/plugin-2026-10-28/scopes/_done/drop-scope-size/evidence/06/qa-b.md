# QA blackbox, task 06 (handin ebe85ec, branch squad/plugin/drop-scope-size/plugin-dev-dsz-06)

Scratch homes (`none`; `qa-white, qa-black`; L; L without qa-black; M+designer; M+architect; qa-white; qa-black; blank team); `squad-process compose` for 7 roles; `squad-process who`; `squad-process lint`. Branch is on base 6ec3a75 plus 06 only, so rules of 05 (sizes.md) and 07/08 are still old text here; I judged only this ticket's files (who, starting, files, goal, promotion, closing, notes, iterations, agents/*.md). CLI only.

| Check | Saw | Result |
|---|---|---|
| Compose, 9 teams x 7 roles | exit 0 everywhere | PASS |
| Word "size" in prose of 06's files and `agents/*.md` | none (only `[SIZE-n]` references to rule IDs) | PASS |
| `[if ... size` or `qa-b` in blocks of 06's files | none | PASS |
| WHO-1a..1e, WHO-2d.. | rule appears only for the team that has the duty owner (`business-ac = ticket` shows WHO-1d, `= ba` shows WHO-1c, `plan-owner = team-lead` WHO-1e); WHO-1b says "Every checker on the team (`duties:`); with none, the Manager confirms the Developer's evidence and review" | PASS |
| START-1, START-3, START-19 | "team's Done rule", "propose the team", "write the confirmed `team:` into `scope.md` ... When unsure, add the role"; goal Manager proposes each scope's team | PASS |
| FILE-5a, FILE-9, FILE-11, PROMO-3a | resolve by duty owner (`plan-owner`, `promote-owner`); no absent role named as actor in S | PASS |
| `squad-process lint` | exit 0 | PASS |

Notes (not 06 failures):
1. `squad-process who <ID>` still prints rows labelled S / M / L (and for WHO-1c "S: acts: manager, ba, tech-lead"), not the team shapes. AC 15/29 `who` output is ticket 12's.
2. Left in composed text, owned by 05/07/08: `[if size ...]`, `qa-b` and "size" prose in SIZE-/REV-/EVID-/MSG-/SPAWN- blocks of this branch; START-5 "Lifetimes" table names Team Lead, Tech Lead, QAs generically as lifetimes (not as actors).
3. AC 1-6 need the live Manager run (step L).

## Re-check on final code sha bd361cf (LC-3b: ITER-3b, team-lead card, changed rules)

Same scratch homes (9 shapes); `squad-process compose` for 7 roles x 9 shapes; `lint`.

| Check | Saw | Result |
|---|---|---|
| Compose, all roles, all shapes | exit 0 (role name for Developer is `dev`) | PASS |
| `squad-process lint` | exit 0 | PASS |
| ITER-3b "Pod summary, Manager" | In M and QB (no Team Lead): Manager gets "When you own the plan (the Team Lead is not on the team), write `iterations/<n>.summary.md` ... at most 40 lines". L, Lnob (Team Lead on team): Manager has no ITER-3b, Team Lead has ITER-3. | PASS |
| Team-lead card | "You exist only when the scope's team lists `team-lead`; without you the Manager holds the plan"; no word "size" | PASS |
| Word "size" / `[if ... size]` / `qa-b` in blocks of 06's files (WHO, START, FILE, GOAL, PROMO, CLOSE, NOTE, ITER) | only `[SIZE-n]` rule IDs and the file name `qa-b.md` in FILE-9 | PASS |
| `agents/*.md` | no "size" | PASS |

Note (non-blocking): in the S shape (`team: none`) the Manager text still points at `[ITER-3]` (messages list) with no ITER-3 block attached; no pod, so no summary is due. Remaining old text lives in 05/07/08 blocks (not 06).
