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
