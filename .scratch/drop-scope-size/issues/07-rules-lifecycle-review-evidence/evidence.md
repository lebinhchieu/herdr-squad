# 07 Rules: lifecycle, review, evidence
sha: 0f1dc44
## Behaviour
- `lifecycle.md`, `review.md`, `evidence.md`: every `when:` is in team language (no `size`, no `qa-b`); changelog v9 lists every changed ID.
- Return 1 fixes (QA whitebox F1-F5):
  - F2 LC-20a: `handin-target = manager`, "Done when the Manager sent PASS" (the S text). LC-20b: `handin-target = qas`, every checker, tell the plan owner. New LC-20e: `handin-target = team-lead`.
  - F3 LC-7a: `handin-target = manager`, S text, no checker sentence.
  - F4 REV-14a: restores "tell the plan owner after every checker passes it" (with QAs on the team).
  - F5 REV-3b: `aware: manager` restored, as in the M text.
  - A `when:` holds one duty/role key (lint), so L and M share LC-20b with "the plan owner" instead of naming Manager or Team Lead.
- Stale tests fixed to new IDs/keys, no weakening. Outside the ticket's list (Tech ANSWER 07 (b), DECISION 07): `tests/test_dev_rules_size.py`, `tests/test_sizes.py`, `tests/test_process_conversion.py`, `tests/test_instructions.py`, `tests/test_architect_handoff.py`, `tests/test_pod_contact_routes.py`, `tests/test_manager_m_l.py`.
- Deferred by Tech Lead DECISION 07: the 5 KiB dev-rules budget tests, skipped with reason "5 KiB trim is ticket 11" (`test_sizes` 1, `test_dev_rules_size` 3 tests). Nothing else skipped.
- Ran green (386 tests, 4 skipped): the 7 files above plus test_qab_optional, test_team_duties, test_squadrules, test_retro_rules, test_advisor_rules, test_pod_rules_process, test_processlint, test_templates, test_windows_safe, test_crlf_squad_files, test_squad_close.
- G2b: `squad-process lint` on base 6389642 and on the branch: both empty, rc 0.
- `test_qab_optional`: 11 tests, none skipped.

## Return 2: Manager rule sets vs base 6389642 (LC-, REV-, EVID- IDs only)
Composed per shape (S = no team, M = `qa-white, qa-black`, L = `ba, team-lead, tech-lead, qa-white, qa-black`); script compared base `size:` homes with branch `team:` homes.
- S Manager: no difference (LC-7a kept). S Dev: none.
- M Manager: base LC-7c -> LC-7a. LC-7a is now `plan-owner = manager` with "with QAs on the team the 3rd failing QA sends you `BLOCKED NN: 3 returns`", so the Manager keeps the base LC-7c duty (a `when:` allows one duty/role key, so a separate "no Team Lead" rule is not expressible). Test `test_manager_three_returns_rule_per_team_shape` pins S, M and L.
- L Manager: no difference (LC-7b aware, no LC-7a).
- Dev: LC-20c -> LC-20b (M), REV-14c/14b -> REV-14a (M, L); text carries the Manager/Team Lead report-back as "plan owner".
- QAs: new LC-7c at M and L (3rd failing QA sends the plan owner BLOCKED); base had it only as the Manager's M rule.
- REV-3b is now `handin-target = qas`, no `aware: manager` (a QA-less S Manager would otherwise carry a QA rule). Difference vs base: the M Manager no longer sees the single-verdict line; it receives the verdicts, so nothing is lost.
- Not a difference of mine: base-only SIZE-/TEAM- and new-only COST-/SUITE-/MSG- IDs are other tickets' files.

## QA whitebox

### QA whitebox 07 — on 426706d (HANDIN). Verdict held until the Tech Lead names the final sha (REV-3).
Checked read-only in worktree plugin-dev-dsz-07; base = 6389642 (INT1), tests also run from a git-archive of it.
Passed: `squad-process lint` exit 0 empty (= base). OK: test_qab_optional (11, no skips left), test_team_duties, test_squadrules, test_retro_rules, test_advisor_rules, test_pod_rules_process, test_team_lead_role, test_templates, test_windows_safe, test_crlf_squad_files, test_squad_close, test_processlint.

#### F1 (G1: tests touched by the change are red; all green on base 6389642)
Base 6389642 is green on every file below; at 426706d they fail. The ticket says every `grep -rl` hit runs green (CLAUDE.md, G1); Tech ANSWER 07 (b) allowed fixing stale tests outside the list, evidence.md only names two files.
- tests/test_process_conversion.py:101 `test_fix_a_handin_target_by_size`: expects REV-13a `size = S`; now `handin-target = manager`.
- tests/test_instructions.py:197 `test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass`: IndexError, `## REV-14b` no longer exists (merged into REV-14a).
- tests/test_architect_handoff.py: `test_conformance_joins_the_technical_ac_of_the_existing_checker`, `test_the_plan_waits_for_the_architecture`.
- tests/test_pod_contact_routes.py: `test_m_paths_go_to_the_qas_and_done_to_the_manager`, `test_team_lead_routes_in_l`.
- tests/test_manager_m_l.py: `test_s_keeps_the_pod_health_checks`.
- tests/test_sizes.py: `test_dev_rules_stay_within_5_kib` (S, yes, yes) 6121 B; tests/test_dev_rules_size.py: 24 failures (5.8 KB at every shape). The evidence says "same on base (7 KB then)": on base these 2 files are green (the test composed a `size:` home). The Dev changed the helper to a `team:` home, which turns them red. If the 5 KiB cap is ticket 11's, the ticket/Tech DECISION must say so and the test must be marked (skip with reason) rather than left red; otherwise bring Dev rules under 5120.
Pass: each test above fixed to the new IDs/keys (or an explicit Tech DECISION naming it deferred to 11/12 with a reason in evidence.md), rerun green.

#### F2 (correctness) templates/squad/process/lifecycle.md:250-255 LC-20a at a team with no checkers
Base LC-20a (S): "Done when the Manager sent `PASS`." New (`plan-owner = manager`): "Done when every checker sent `PASS`. Tell the Manager and wait". An S-shape Developer (handin-target = manager, no QA) now has no PASS source: "every checker" is empty. Pass: split on `handin-target` (manager: "Done when the Manager sent PASS"; qas/team-lead: every checker).

#### F3 (correctness) templates/squad/process/lifecycle.md:73-78 LC-7a at a team with no checkers
`when: plan-owner = manager` covers S (no QA): body says "the 3rd failing checker sends you `BLOCKED NN: 3 returns`, and your own 3rd FAIL counts". Base S text: "the Manager steps in; your own 3rd FAIL counts" (no checker sentence). Pass: keep the S-form for `handin-target = manager` or make the checker sentence conditional.

#### F4 (lost duty) templates/squad/process/review.md:149-153 REV-14a
Base L/M REV-14b/c: "...diff check...; tell the Team Lead / Manager after both pass it". New REV-14a (no `when`) drops that sentence at every shape. Pass: restore the report-back sentence for checkers on the team (own rule keyed `handin-target in qas`) or state in evidence why it is dropped.

#### F5 (style, REV-17) review.md:42-47 REV-3b
The `aware: manager` line of base REV-3b (M) is gone; the M Manager no longer sees the single-verdict rule. Non-blocking if intended; say so in evidence.md.

Method: base-vs-branch composed rule IDs over S/M/L/Mdesign/March/Lgoal x present roles, new side composed from `team:` = legacy_team(shape). Other differences are the intended moves (LC-7a/c, LC-20, REV-14). Lnoqb (qa-b no) not compared by me: Dev's 128-set test covers it.

### Return 1 re-check on c5dd6ce (diff 426706d..c5dd6ce, LC-3b)
Result: all F1-F5 fixed; PASS ready, sent once the Tech Lead names c5dd6ce final (REV-3).
- Lint exit 0 empty. Ran test_process_conversion, test_instructions, test_architect_handoff, test_pod_contact_routes, test_manager_m_l, test_sizes, test_dev_rules_size, test_qab_optional, test_team_duties: 166 tests OK, 4 skipped (all "5 KiB trim is ticket 11", per Tech DECISION 07).
- F1 fixed: tests moved to new IDs/keys, no assertion weakened; evidence.md names the 7 outside-list files.
- F2 fixed: LC-20a `handin-target = manager` (S text), LC-20b `qas`, LC-20e `team-lead`. Composed dev: S -> LC-20a, M/L -> LC-20b.
- F3 fixed: LC-7a `handin-target = manager`, no checker sentence; Manager S only gets it, M gets LC-7c.
- F4 fixed: REV-14a "with QAs on the team, tell the plan owner after every checker passes it" (wording-keyed, not a `when`; accepted per Tech ruling; S text only mentions QAs conditionally).
- F5 fixed: REV-3b `aware: manager`; Manager S and M carry the line, L does not (as base).
- Reminder for 11/12: un-skip test_sizes dev-5KiB and 3 tests in test_dev_rules_size.

### Return 2 re-check on 0f1dc44 (diff c5dd6ce..0f1dc44, LC-3b)
Result: clean; PASS ready once the Tech Lead names 0f1dc44 final (REV-3). My miss on c5dd6ce: I tested the Manager for the QA-side LC-7c sentence, which the Manager never receives; Tech Lead found the lost M Manager rule.
- Lint exit 0 empty. 256 targeted tests OK, 4 skipped (ticket-11 deferral): test_manager_m_l (new per-shape test), test_process_conversion, test_instructions, test_architect_handoff, test_pod_contact_routes, test_sizes, test_dev_rules_size, test_qab_optional, test_team_duties, test_processlint, test_squadrules.
- Invariant over all 128 team sets (own script): Manager composes a three-returns rule in every set (LC-7a with `plan-owner = manager`, conditional QA sentence; LC-7b aware when a Team Lead owns the plan); Dev composes exactly one LC-20 rule in every set. No failures.
- Base-vs-branch Manager (S/M/L shapes, LC/REV/EVID): S same; M base LC-7c -> LC-7a (same duty); L same. REV-3b without `aware: manager`: Manager still receives the verdicts; accepted as covered (evidence.md Return 2).
- Other diffs against base are tickets 08-14 files, not 07.

## QA blackbox

### QA blackbox, task 07 (HANDIN 426706d, branch squad/plugin/drop-scope-size/plugin-dev-dsz-07)

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

#### Findings
None. Verdict waits for the Tech Lead's final sha (REV-3).

#### Re-check on c5dd6ce (diff 426706d..c5dd6ce; lifecycle.md, review.md)

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

#### Correction (after Tech Lead DECISION 07)
My c5dd6ce re-check marked "Three returns" PASS too early. My own compose output showed it: for `qa-white, qa-black`, `qa-white` and `qa-black` (QAs, no Team Lead) `manager` listed only `REV-3b`; no three-returns rule, although `LC-7c` sends it `BLOCKED NN: 3 returns` (AC 12). Same for `tech-lead`-less QA teams. c5dd6ce is not final. Re-test on the new sha: compose manager for `qa-white, qa-black` and `qa-white`/`qa-black`, with and without `team-lead`.

#### Re-check on 0f1dc44 (diff c5dd6ce..0f1dc44)

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

## Tech Lead review

sha 0f1dc44 (final code, 07, return 2): TL read diff c5dd6ce..0f1dc44, composed Manager (qa-white,qa-black) has LC-7a, lint empty, 10 touched test files OK (5 KiB skips = ticket 11). REV-3b aware-manager drop accepted (M Manager receives verdicts).
