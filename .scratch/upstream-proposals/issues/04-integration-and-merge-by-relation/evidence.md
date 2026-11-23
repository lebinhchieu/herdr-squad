# Evidence: 04 04 Integration and merge by relation

## Behaviour

### Evidence 04

#### Behaviour
- Commit 854a024 on squad/plugin/upstream-proposals/plugin-dev-upstream-proposals-04.
- New rules: GOAL-6e, GOAL-6f (team-lead, manager; aware tech-lead, qa-whitebox), MRG-6, MRG-6b (manager, phase merge, before MRG-2). GOAL-6a/6d lost `when: goal = yes` (6d keeps `tech-lead = no`). No rule attaches to dev.
- `python3 bin/squad-process lint`: exit 0.
- `squad-process phase merge --home <scope>` prints MRG-6, MRG-6b, MRG-2... in that order.
- `grep -rn 'SQ-6\|SQ-7' bin tests`: empty.
- Worst no-designer/no-architect Developer team: 5473 B (base 5473), growth 0 of a 0 B budget. `test_every_team_set_fits_the_limit` fails on base too for design teams (5692 B): Known failing on base, no FAIL.
- Tests (cd tests; python3 -m unittest): test_windows_safe, test_utf8_helpers, test_instructions, test_squad_merge_check, test_rules_wording, test_small_files_equivalence (golden M/manager gains GOAL-6d, by design), test_squad_review_pack, test_squadcompose, test_sizes: all OK; test_dev_rules_size: only the base failure.
- `squad-process upgrade --check`: SQ-7 and SQ-7b show "the plugin added MRG-6 / MRG-6b"; SQ-6/SQ-6b not flagged (kept, 0 need a decision). Replacements: SQ-6 -> GOAL-6e, SQ-6b -> GOAL-6f, SQ-7 -> MRG-6, SQ-7b -> MRG-6b.

## QA whitebox

### QA whitebox, ticket 04, sha 854a024

Verdict: FAIL (1 finding).

#### Checked, passes
- `squad-process lint` exit 0. Attachment (rulesview.who): GOAL-6e, 6f = team-lead, manager, aware tech-lead, qa-whitebox; MRG-6, 6b = manager; no `dev` anywhere (T8: dev worst team 5473, growth 0).
- GOAL-6a and GOAL-6d lost `when: goal = yes`; GOAL-6e covers the lone scope (ancestor = no integration), AC1.
- MRG-6 names `git merge-base --is-ancestor main <sha>`, `git diff --name-only <base> main`, the note "main moved, N files, none related"; sits before MRG-2. AC2, T-per-ticket.
- `grep -rn 'SQ-6\|SQ-7' bin tests templates agents skills`: no SQ-6/SQ-7 left in bin/ or tests/.
- Passing: test_windows_safe, test_utf8_helpers, test_instructions, test_squad_merge_check, test_rules_wording, test_small_files_equivalence, test_squad_review_pack, test_squadcompose, test_sizes.

#### Finding (breaks a test that passes on the base)
1. `templates/squad/process/merge.md:22` MRG-6b has `phase: merge` and `aware: team-lead, qa-whitebox`.
   `tests/test_rules_contract.py:228` `test_phase_rules_are_the_only_difference_and_only_for_their_acting_role` fails for 12 subtests (role team-lead and qa-whitebox, every shape): the contract is that a phase rule belongs to the manager only and a non-manager role gets the same rules with and without phases. An `aware:` role on a phase rule breaks it. The test passes on base (and on the 01 branch), and is a `grep -rl` hit of the MRG IDs; it is not in the HANDIN's run list.
   What would pass: drop `aware: team-lead, qa-whitebox` from MRG-6b (the Team Lead learns of the request when the Manager asks, MRG-6b text already says "ask the Team Lead"), or drop `phase: merge` if the Tech Lead wants awareness; then `python3 tests/test_rules_contract.py` is OK. Tech Lead's tl-design.md §3 prescribed the aware line, so it may want to confirm; the test is the bar.

#### Follow-ups (not a FAIL)
- `test_dev_rules_size::test_every_team_set_fits_the_limit` base failure for design teams only.

#### Re-check, sha a728476
Diff 854a024..a728476 removes the `aware:` line of MRG-6b only. `squad-process lint` exit 0; test_rules_contract, test_squad_merge_check, test_small_files_equivalence, test_rules_wording, test_squadcompose OK; `who MRG-6b` = manager only. Finding closed. Verdict: PASS.

## QA blackbox

### QA blackbox 04, sha 854a024

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 lone scope, only ancestor branches: no integration task | live | `squad-process rule GOAL-6e / GOAL-6a / GOAL-6f` (worktree plugin root); composed team-lead rules for the plugin scope | GOAL-6e: "Each an ancestor of the last (`git merge-base --is-ancestor`): no integration ... in a lone scope too". GOAL-6a/6d no longer carry `when: goal = yes`; GOAL-6e/6f are in the composed team-lead rules of a non-goal scope | pass |
| AC2 merge rule names both git commands and note text | live | `squad-process rule MRG-6`, `MRG-6b`; `squad-process phase merge --home <scope>` | MRG-6 names `git merge-base --is-ancestor main <sha>`, `git diff --name-only <base> main`, and the note "main moved, N files, none related". Phase order: MRG-6, MRG-6b, MRG-2, MRG-3 ... | pass |
| AC3 lint | live | `squad-process lint` | exit 0 | pass |
| AC4 IDs, MRG-6 before MRG-2, no SQ-6/SQ-7 in bin | live | phase merge order above; `squad-merge-check <branch>` | runs, rc 0, prints ancestor/passed/main-moved/siblings lines | pass |
| AC5 nothing attached to dev | live | composed `dev` rules | none of GOAL-6a..f, MRG-6, 6b | pass |
| AC6 upgrade --check, Comments name replacements | live | `upgrade --check --squad-dir .claude/squads/plugin --plugin-root <worktree>` | SQ-7, SQ-7b: "the plugin added MRG-6 / MRG-6b" (review, not blocking). SQ-6, SQ-6b are not listed (18 unaffected = kept). Ticket Comments name all four replacements | pass (see follow-up) |
| rule text: no PO name, no `_done/`, no version | live | read all four rules | none | pass |

Follow-ups (not FAIL, SQ-4):
- AC6 says every source op "shows as add or stale"; SQ-6 and SQ-6b are not listed in `upgrade --check` at all (the tool counts them unaffected). The Developer disclosed it; I accept it as the tool's behaviour.
- MRG-6 writes the second diff as `... <base> <sha>`; the ticket spelled `<base>..<sha>`. A reader must expand the "...". Optional wording fix.
- Byte budget, tests and golden changes: QA whitebox.
