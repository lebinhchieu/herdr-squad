# Evidence: 14g rule-contract tests (C4)

## Behaviour

Tests only; no change in `bin/ templates/ agents/ skills/ docs/`. Code sha: `60de3c7` (base `4a8ed47`). Runs: `test_rules_contract` 13 OK, `test_rules_wording` 17 OK, `bin/squad-process lint` exit 0 and empty. `git diff 4a8ed47 | grep -i '^+.*skip'` is empty.

### Owned set (TL answer B)
`tests/rulesview.py` (added `rule_ids`) and 11 files, now merged: test_advisor_rules, test_pod_rules_process, test_retro_rules, test_suite_rules_process, test_task_id_rule, test_designer_handoff, test_manager_m_l, test_team_lead_role, test_pod_contact_routes, test_manager_inbox_read, test_process_citations. Files: 11 -> 2.

Left out (not mainly rule targeting/wording, or other owner): test_promotion_0_6_0 (git grep and version checks), test_dev_rules_size (byte budget, own compose), test_instructions (layout, cards, settings), test_old_language_inventory (git grep + script launch), test_crlf_squad_files (14b/14e), test_architect_handoff (card and settings), test_qab_optional, test_sizes, test_small_files_equivalence (golden tables, engine sweeps), test_squadcompose, test_squadrules.

### Net line loss (honest)
`git diff --shortstat 4a8ed47 60de3c7`: 329 insertions, 441 deletions = net loss **112** lines, not 400. Reason: the 11 files held 441 lines in all, so the floor of 400 cannot be met by this set; I did not pad or drop assertions to reach it.

### Old test -> where it lives now (`C` = test_rules_contract, `W` = test_rules_wording)
| Old | Now |
|---|---|
| advisor::test_who_shows_acting_roles | C WhoActsTest.test_who_shows_the_acting_roles (LC-25 set, LC-26 rows) |
| advisor::test_third_return_notice_cites_a_real_rule | W CitationsTest same name |
| advisor::test_overlay_can_turn_the_advisor_off | W CitationsTest same name |
| pod_rules_process (2 tests) | C test_who_shows_the_acting_roles (MSG-5, SIZE-6a, LC-15, LC-17b rows) |
| retro_rules (1 test) | C test_who_shows_the_acting_roles (ITER-13..16 rows) |
| suite::test_the_size_owner_runs_it_and_others_never | C ComposedRulesTest same name; its 3 `acts` lines are rows in the who test |
| suite::test_every_suite_owner_value_has_a_rule | C WhoActsTest same name |
| suite::test_the_suite_owner_follows_the_team_chain | C same name |
| suite::test_qa_blackbox_gets_a_suites_rule... | C same name |
| task_id::test_rule_is_targeted... | C test_task_id_rule_reaches_every_role_and_size (counts) + W test_task_id_rule_text_reaches_dev_qa_and_team_lead (wording) |
| designer::test_consuming_roles... | W same name |
| designer::test_tech_lead_keys_on_design_yes | W same name; its 2 `acts` lines are rows in C who test |
| manager_m_l (3 tests) | W ManagerWordingTest same names |
| team_lead_role::test_exists... | C test_team_lead_exists_when_the_team_lists_it_and_takes_the_handover (+ SIZE-17b row) |
| team_lead_role::test_spawns_and_retires_dev_only | C test_team_lead_spawns_and_retires_dev_only (+ SPAWN-9 row) |
| team_lead_role::test_spawning_cost_and_safety... | C same name; the file-text loop split into C test_spawning_cost_and_safety_files_have_no_size_word |
| team_lead_role::test_tech_lead_without_team_lead... | C same name |
| pod_contact_routes (3 tests) | C test_routes_follow_the_plan_owner..., test_doubts_go_to_the_doubt_owner; W CardRoutesTest.test_every_manager_line_of_a_card_is_allowed |
| manager_inbox_read (6 tests) | W ManagerInboxWordingTest, same names |
| process_citations (2 tests) | W CitationsTest, same names |

### Test counts
Before 31 `def test_` in the 11 files; after 30 (13 + 17). Falls by 3 (advisor-who, 2 pod, retro merged into one table-driven `test_who_shows_the_acting_roles`: 4 -> 1), rises by 2 (task_id split into counts and wording; team-lead file-text loop split off). Each assertion kept at the same strength.

### Shared cache
`rulesview.composed` and `who` stay `lru_cache`d; the new files add no compose of their own (only `test_dev_rules_size.compose`, as before).

## Review
Fresh sonnet/high subagent on `60de3c7`: dropped or weakened assertions none; bugs none. Notes, no change needed: the MSG-3 `S` count check is tautological, as in the base; the COST-4c check on `rule_ids` is as strict or stricter than the old substring check.
