# QA blackbox, task 05 (code sha 6d33099, handin 9ffa44f, branch squad/plugin/drop-scope-size/plugin-dev-dsz-5)

Scratch homes with a hand-made `scope.md` per shape; `squad-process compose <role> --home D --plugin-root <worktree> --out F` for manager, dev, team-lead, qa-whitebox, qa-blackbox, ba, tech-lead. Looked at the SIZE-/TEAM- rule blocks (this ticket's files). CLI only, no screenshots. Verdict waits for the Tech Lead's final sha (REV-3).

| AC / check | What I did | What I saw | Result |
|---|---|---|---|
| All shapes compose | S, M, L, L no qa-black, M+designer, M+architect, qa-white alone, qa-black alone, tech-lead+qa-black, undecided; 7 roles each | exit 0 everywhere | PASS |
| Word "size" in SIZE-/TEAM- prose (AC 29, 04a) | `grep -iw size` on those blocks, all roles | only rule IDs (`SIZE-n`); no prose use, no `[if ... size` in these blocks | PASS |
| `qa-b` in sizes.md / teams.md | grep | 0 hits | PASS |
| Proposal rule, a row per role (AC 1) | SIZE-1 in Manager text | table: BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect, each with propose-when and silent default; unsure -> add; task count loses; nothing spawned before PO confirms; one table per goal scope; risk flags; PO may override, logged | PASS |
| Signals for AC 2-5 | read SIZE-1 | screen/flows -> Designer; data model, new dependency -> Architect; QA blackbox "no observable change"; QA whitebox out only for the five conditions; risk flags -> Tech Lead + QA whitebox | PASS (live Manager run still owed, step L) |
| Done per shape (AC 13, 14) | Manager text per team | both QAs: SIZE-2 "QA whitebox PASS and QA blackbox PASS ... One PASS is never enough"; qa-white only: TEAM-1; qa-black only: TEAM-2 (PASS + `## Review` confirmed); none: TEAM-3 (Developer's checks, `evidence.md`, `## Review`, Manager confirms); no shape gets another shape's text | PASS |
| Behaviour check without qa-black (AC 13) | qa-whitebox text, qa-white only | TEAM-4: checks Developer's `## Behaviour` against business AC | PASS |
| BA alone, Tech Lead without qa-white | TEAM-5, TEAM-6 | TEAM-5: QA whitebox checks `## Behaviour` against the BA's AC; TEAM-6: Tech Lead confirms the Developer's `## Review` | PASS |
| `duties:` line, shapes of AC 9 | Manager header | S: manager/dev/dev/ticket/manager/manager/manager; M: qa-white, qa-black checks, hand-in qas; L: team-lead, tech-lead, ba; L no qa-black: behaviour qa-white, ui manager; M+designer: ui qa-black; M+architect: choice architect; matches today's SIZE-22/22a | PASS |
| SIZE-22 chains | read table | each chain ends at Manager, Developer or ticket; Architect folded in; PO decides irreversible choices | PASS |
| Team change: SIZE-13, 14, 16, TEAM-7 | read | late signal -> role; Designer/Architect wait for PO's yes; Handover; respawn; log; remove only at iteration boundary with PO's OK; passed tasks stay passed | PASS |
| Tombstones (G5) | `_removed.md` | removed SIZE IDs carry `why:` and `replaced_by:` | PASS |
| `squad-process lint` | run on the branch | exit 0, no output | PASS |

Notes (not 05 failures):
1. `squad-process who SIZE-22` / `who TEAM-3` still print S/M/L preset rows; `who` rewrite is a later ticket (AC 29 `who` check).
2. Composed text from rules of tickets 06-08 still has `[if size ...]`, `qa-b`, and "size" prose; Dev rules still carry both Manager and QA whitebox HANDIN lines for every team and compose to 7.5-9.4 KB (AC 24 limit 5120): tickets 06-08, 11. Dev said the 2 `test_qab_optional` tests wait for 07.
3. SIZE-18 "when the scope is large" reads like a size notion. Optional reword.
4. AC 1-6 still need the live Manager run (step L).
