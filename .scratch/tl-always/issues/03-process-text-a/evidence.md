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
