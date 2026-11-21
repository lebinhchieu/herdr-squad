# 03 Process text A: evidence

## Review
AC trace:
- AC1 | `squad-process lint`; grep in checks | run in worktree
- AC2 | grep of removed IDs | `grep -rn` over bin hooks agents skills tests templates
- AC2b | test_rules_contract `test_team_lead_text_gives_no_plan_or_order` | `python3 -m unittest test_rules_contract`
- AC3 | test_rules_contract `test_manager_owns_plan_and_disputes_team_lead_never_reorders` | same
- AC4 | who.md WHO-1e; `squad-process who WHO-1e` | run
- AC5 | test_squad_log_message `test_third_return_always_goes_to_team_lead` | `python3 -m unittest test_squad_log_message`
- AC6 | windows_safe, utf8_helpers, instructions | `python3 -m unittest ...`
- AC7 | test_dev_rules_size | same
- AC8 | the ten files below | same

Checks: see `## Checks`.

## Behaviour
Run from `tests/`: `python3 -m unittest test_rules_contract test_rules_wording test_architect_handoff test_small_files_equivalence test_dev_rules_size test_squad_log_message test_windows_safe test_utf8_helpers test_instructions test_sizes` -> Ran 144, OK. `squad-process lint` exit 0.

- 16 `plan-owner = manager` rules removed with tombstones (v20); `plan-owner = team-lead` conditions stripped.
- Manager owns plan, order and disputes; Team Lead never reorders (LC-17, WHO-8c, MSG-6 `ASK` for a plan change).
- LC-14: Tech Lead writes deps, files, parallel groups under `tasks/`, one line to the Manager, Team Lead on copy.
- `bin/squad-log-message`: 3rd return notice always to Team Lead `[LC-7b]`.

Note: with LC-11c removed, no Manager rule says "split tasks only after architecture final" (LC-11d is Team Lead assignment). Per ticket; Tech Lead may want a follow-up.

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `squad-process lint` exit 0; grep for plan-owner and team-lead = over the three files: empty | - | - |
| AC2 | grep of the 16 removed IDs: only `_removed.md`, changelog, 3 `assertNotIn` lines | - | - |
| AC2b | `grep -in 'plan owner'` over lifecycle, messages, who, review: empty; `test_team_lead_text_gives_no_plan_or_order` OK | - | - |
| AC3 | `test_manager_owns_plan_and_disputes_team_lead_never_reorders`, `test_routes_follow_...` OK | - | - |
| AC4 | WHO-1e rows in who.md; `squad-process who WHO-1e` lists manager, team-lead, tech-lead | - | - |
| AC5 | `test_third_return_always_goes_to_team_lead` OK | - | - |
| AC6 | test_windows_safe, test_utf8_helpers, test_instructions OK (144 tests) | - | - |
| AC7 | `test_dev_rules_size` OK | - | - |
| AC8 | 10 test files run, 144 OK | - | - |

## QA whitebox
Ran `cd tests && python3 -m unittest test_rules_contract test_rules_wording test_architect_handoff test_small_files_equivalence test_dev_rules_size test_squad_log_message test_windows_safe test_utf8_helpers test_instructions test_sizes` -> 144 OK; `squad-process lint` 0. AC1 grep empty; AC2 hits only 3 negative assertions in tests; AC2c grep "plan owner" empty; AC2b greps: every hit Manager-only or "never reorders" (LC-17, MSG-6, WHO-1e, WHO team-lead row); AC4 WHO-1e split as designed; AC5 bin/squad-log-message always Team Lead [LC-7b] with test; test_team_lead_text_gives_no_plan_or_order present. No test newly skipped. LC-14, LC-15..17 read: consistent with Manager owns the plan.
PASS.
## Follow-ups
- Integration (SQ-6): 03 and 04 both edit iterations.md, _removed.md, spawning.md, starting.md and five test files (test_rules_contract, test_rules_wording, test_architect_handoff, test_dev_rules_size, test_small_files_equivalence). They are related siblings: merge both and run the shared tests on the result (SQ-6b).

## QA blackbox
Worktree .worktrees/plugin/tl-always/plugin-dev-tl-always-03, live runs.

| AC | how | saw | result |
|---|---|---|---|
| AC1 | live: `squad-process lint` (rc 0); grep `plan-owner\|team-lead = ` in lifecycle/messages/who | lint clean, grep empty | pass |
| AC2 | live: grep of removed IDs over bin hooks agents skills tests templates minus _removed/changelog/fixtures | only 3 `assertNotIn` lines in tests | pass |
| AC2c | live: `grep -in 'plan owner'` lifecycle/messages/review | empty | pass |
| AC2b | live: grep take over the plan / owns the plan / task order / plan owner / Reorder over 03's files | only who.md:36 (Manager row). LC-17 now (lifecycle:171): "You never reorder the plan ... send the Manager an ASK" | pass |
| AC3 | live: compose team-lead, manager, dev on a no-pin scratch squad (team: qa-white, qa-black) | Team Lead text: never reorder (MSG-6, who.md:153, LC-17); Manager text has SIZE-6a plan/order/spawning + MSG-6; dev composes (85 lines) with no plan-owner text | pass |
| AC4 | live: `squad-process rule WHO-1e` | heading "Plan, order and assignment", no `when:`, rows `Plan, task order` Manager and `Assignment` Team Lead. `squad-process who WHO-1e` prints nothing (same as any unconditional rule, e.g. MSG-6) | pass |
| AC5, AC6, AC7 | live: `cd tests && python3 -m unittest` on test_rules_contract, _rules_wording, _architect_handoff, _small_files_equivalence, _squad_log_message, _dev_rules_size, _windows_safe, _utf8_helpers, _instructions | 136 tests OK | pass |

Follow-ups (not AC of 03, files of 04): composed Team Lead and Manager text still has "Plan owner (`plan-owner` of `duties:`)" and "the plan owner ([ITER-3])" from files.md:90,97, and the `duties:` header still carries plan-owner (02's engine). Settle in 04/02/07.
