# QA blackbox, task 12 (HANDIN 1aebbf8, final code sha 309cc49)

Method: CLI only. `git archive 1aebbf8` for the engine checks; for upgrade/overlay the branch merged onto INT4 (e265fd7) in a scratch clone (clean merge), since the branch alone still carries size rules from unmerged tickets. Scratch squads: `scopes/*/scope.md`, `process.local.md`, `plugin.pin`; stub claude/herdr (suite's herdr stub for `squad-start`).

| AC | What I did / saw | Result |
|---|---|---|
| 11a | Overlay rule with `when:` `size = L`, `qa-b = no`, `qa-whitebox = yes`, `ba = maybe`, `foo = yes`: compose rc 2 and lint names `SQ-1` and the key; `ba = yes and qa-white = yes`: lint names the rule ("at most one"), compose rc 0; `qa-black = no`, `ba = yes` compose rc 0 | PASS |
| 11b | Decided team (`qa-white,ba`): 0 `[if ` tags in manager, dev, qa-whitebox, ba. Undecided manager keeps `[if` tags | PASS |
| 15 | Undecided `team:` -> `squad-spawn dev/qa-whitebox/architect` refused, "the team is undecided ... only the Manager can be spawned"; compose of any non-Manager role rc 2; Manager composes | PASS |
| 20 | `adopt` skips pinned scope (`a1`, `size: L`, `plugin: 0.5.2 ...`), file unchanged | PASS |
| 21 | `upgrade --check` prints `size = L -> ba = yes`, `qa-b = no -> qa-black = no`, `size = M -> qa-white = yes`, stale `replace SIZE-2` listed with `--resolve`; every file byte-identical (rc 2). `--apply` without `--yes` and `--apply --yes` with old-language ops: "NOT APPLIED ... nothing written", rc 3. **Missing:** for a rule whose `roles:` is `tech-lead` (also tried `team-lead`, `tech-lead, team-lead`) with `when: size = L`, the report lists only `ba = yes`; the lines offering `team-lead = yes` and `tech-lead = yes` as alternatives (AC 21) never appear (0 matches for "team-lead = yes" in the whole output) | FAIL |
| 22a | `adopt --dry-run` writes nothing and prints: M+qa-b no -> `qa-white`; M+qa-b yes -> `qa-white, qa-black`; L+design -> `ba, team-lead, tech-lead, qa-white, qa-black, designer`; M+architecture -> `qa-white, qa-black, architect`; L+qa-b no -> `ba, team-lead, tech-lead, qa-white`; S -> `none`; blank size -> blank `team:`. After `--yes` none of the four old lines remain (backup `scope.md.pre-team.bak`) | PASS |
| 26 | Unpinned `size: M`, no `team:`: `squad-spawn` manager, dev, qa-whitebox, architect all rc 2: "scope.md:2: old format `size:`; run `squad-process adopt` (dry run first)..."; no session started | PASS |
| 27 | `team: qa-whitebox` -> "write 'qa-white'"; `team: qa-b` -> unknown token with allowed list; overlay `qa-b = no` rc 2 naming rule and pointing at `squad-process upgrade`; `qa-black = no` composes | PASS |
| 28 | After `adopt --yes`, `compose manager` rc 0 for S, M, M+qa-b yes, L, L+design, M+architecture, L without qa-b; `duties:` line has a plausible owner for each of 13 duties (e.g. L: plan=team-lead, business-ac=ba, suite=tech-lead; M: suite/code-check=qa-white, behaviour=qa-black) | PASS |
| 29 | `squad-start` output and new `scope.md`: no whole-word "size". `who --help`, `who <ID>`, `team --help`, `lint --help`, `squad-spawn --help`, `squad-start --help`, `squad-team --help`, `squad-respawn --help`: 0 hits. Hits remain only in composed role rules (rule IDs `SIZE-n` and ids, CORE-3 text), not in the AC list; overlay/legacy errors name the old key as allowed. Manager proposal text: live Manager run (step L) | PASS |
| 30 | `team: ba,ba` -> "listed twice"; `team: ba,wizard` -> unknown token 'wizard'; compose rc 2 | PASS |
| lint | `squad-process lint` empty on branch (and on merged tree) | PASS |

Notes (not findings): `adopt` on a blank `size:` leaves the comment `<!-- converted from size:  -->` in `scope.md`. `squad-spawn` for a runtime whose plugin is still 0.5.2 only works with a 0.5.2 pin until ticket 13 bumps the version.

Findings: F1 AC 21: `upgrade --check` does not list `team-lead = yes` and `tech-lead = yes` as alternatives for an overlay rule about another L role.

## Round 2 (HANDIN c768b94, final 59e2741 per Tech Lead DECISION 12)

Re-check AC 21 only (LC-3b). Branch fast-forwarded in my scratch clone (INT4 + 12b = 59e2741); `squad-process upgrade --check --squad-dir <scratch> --old-root <0.5.2 archive> --new-pin "0.6.0 abc1234def56"`.

| AC | What I did / saw | Result |
|---|---|---|
| 21 | Overlay rule `when: size = L` with `roles:` `tech-lead`, `team-lead`, `tech-lead, team-lead`: each prints `size = L -> ba = yes`, `alternative: team-lead = yes`, `alternative: tech-lead = yes`. `roles: dev` and `roles: ba`: only `ba = yes`, no alternatives. Mixed overlay (`size = M`, `qa-b = no`, `roles: dev, tech-lead` `size = L`): `qa-white = yes`, `qa-black = no`, `ba = yes` + both alternatives. md5 of every file before/after `--check` and after `--apply --yes` identical ("NOT APPLIED ... nothing written"); `--check` rc 3 | PASS |

F1 closed. Verdict on 59e2741: PASS.
