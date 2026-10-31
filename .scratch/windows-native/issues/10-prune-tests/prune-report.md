# Ticket 10: prune tests, phase 1 report

**Result:** 101 tests removed from 22 files, each logged with rule, reason and the test that still covers it (`removed.tsv`). Behaviour tests were kept. Native Windows, python 3.14.

**Time:** `qab_optional` 85s to about 16s (memoised, 0 removed). `dev_rules_size` was 32s before.

**Failing before my edits, still failing, not mine:** `po_inbox_mod` (1 fail, needs the real claude CLI), `squad_report_cli` (1 fail).

## Size and time (lines are before/after; time is the baseline run before edits)
| file | lines before | lines after | time before | tests before |
|---|---|---|---|---|
| test_squadinbox | 679 | 679 | 20.2s | 55 |
| test_squadreport_collect | 410 | 410 | 1.4s | 45 |
| test_squad_report_cli | 321 | 303 | 6.4s | 21 |
| test_squadreport_rollup | 295 | 295 | 4.0s | 18 |
| test_squadreport_tasks | 261 | 261 | 0.5s | 14 |
| test_squadreport_rollup_ui | 254 | 254 | 0.3s | 11 |
| test_instructions | 240 | 141 | 1.3s | 30 |
| test_team_lead_role | 229 | 70 | 0.8s | 13 |
| test_squad_report_query | 188 | 178 | 6.4s | 16 |
| test_processlint | 183 | 183 | 0.8s | 31 |
| test_dev_rules_size | 165 | 146 | 32.3s | 11 |
| test_qab_optional | 153 | 155 | 85.4s | 11 |
| test_architect_handoff | 135 | 115 | 3.4s | 15 |
| test_team_cli | 130 | 108 | 5.4s | 12 |
| test_squadreport_digest | 120 | 120 | 0.1s | 10 |
| test_squadreport_html | 118 | 118 | 0.3s | 9 |
| test_po_inbox_contract | 112 | 106 | 1.0s | 5 |
| test_suite_rules_process | 112 | 62 | 1.8s | 13 |
| test_promotion_0_6_0 | 97 | 46 | 0.9s | 8 |
| test_pod_contact_routes | 91 | 59 | 1.1s | 7 |
| test_squadtranscript | 84 | 84 | 0.2s | 3 |
| test_manager_inbox_read | 77 | 49 | 0.4s | 13 |
| test_manager_m_l | 77 | 39 | 0.6s | 10 |
| test_retro_rules | 74 | 18 | 1.2s | 7 |
| test_advisor_rules | 71 | 51 | 2.2s | 6 |
| test_po_inbox_mod | 62 | 62 | 58.8s | 2 |
| test_pod_rules_process | 62 | 21 | 2.0s | 10 |
| test_model_effort_settings | 60 | 36 | 1.7s | 4 |
| test_process_writing | 55 | 33 | 0.2s | 5 |
| test_squadreport_embed | 54 | 54 | 0.1s | 4 |
| test_process_citations | 52 | 36 | 1.0s | 4 |
| test_inbox_body_guide | 45 | 45 | 0.2s | 3 |
| test_hooks_json | 33 | 38 | 0.3s | 7 |
| test_designer_handoff | 25 | 20 | 1.0s | 3 |
| test_task_id_rule | 25 | 16 | 0.4s | 2 |
| test_squad_team | 0 | 286 | 8.5s | 26 |

`test_squad_team` shows 0 before only because I did not touch it (no `10:` commit); it is 286 lines. The 3 browser files are not in `baseline-before.txt`; I did not measure or touch them in phase 1.

## Removed
Style of cut: wording-only rule tests (b-5) and absence tests (b-4), and loops that repeat one check (b-2). Full list below as `file::test, rule, reason, survivor`.

- test_dev_rules_size::test_msg3_says_never_paste_at_every_size | b-2 | 12-combo loop of one wording check on MSG-3 | test_must_keep_duties_by_rule_id (MSG-3 `NN` alone, 3 combos)
- test_dev_rules_size::test_developer_file_cites_evid5_wherever_it_applies | b-2 | up to 512 composes for one cite; same path at every team | test_moved_rules_are_cited_from_the_rule_that_keeps_them (LC-19 cites [EVID-5])
- test_architect_handoff::test_default_model_is_sonnet_high_with_the_advisor | b-3 | asserts three constants of a settings file | none needed (no behaviour)
- test_architect_handoff::test_the_architect_proposes_irreversible_choices_and_the_po_decides | b-5 | exact rule wording | test_the_architect_carries_its_deliverable_and_start_rules_at_every_size (rule ids reach the role)
- test_architect_handoff::test_nothing_in_the_architects_rules_lets_it_check_code | b-5 | one phrase of wording | test_card_is_an_architect_card_without_model_or_effort (card has "check no built code")
- test_architect_handoff::test_the_team_follows_or_asks_the_architect_and_the_manager_decides_after_two_rounds | b-5 | rule-id presence plus exact sentence | test_the_manager_carries_flag_spawn_name_lifetime_gate_and_owner_rules (MSG-20 for manager)
- test_designer_handoff::test_readme_counts_nine_roles_and_names_the_designer | b-3 | README sentence | none (doc text)
- test_advisor_rules::test_triggers_and_note | b-5 | exact wording of LC-25/LC-26 | test_who_shows_acting_roles (LC-25/26 reach their roles)
- test_advisor_rules::test_step_up_replaced | b-4 | asserts absence of an old COST-11 phrase | none (removed behaviour)
- test_advisor_rules::test_lint_passes | b-1 | same `squad-process lint` run as processlint | test_process_citations (lint on the repo)
- test_instructions::test_manager_and_dev_know_the_label_rule | b-5 | exact rule words (--title, squad-label) | test_every_command_an_instruction_tells_agents_to_run_exists
- test_instructions::test_project_instructions_row_names_the_team_file | b-3 | one doc row contains a file name | none (doc text)
- test_instructions::test_init_ignores_the_message_logs_when_everything_is_committed | b-3 | one skill-text token | none (doc text)
- test_instructions::test_the_architect_starts_by_reading_its_scope_folder | b-1 | same asserts as test_every_scope_role_starts_by_reading_its_scope_folder for one more role | test_every_scope_role_starts_by_reading_its_scope_folder; test_architect_handoff
- test_instructions::test_review_finding_4_text_is_gone | b-4 | asserts three old phrases are absent | test_no_file_refers_to_something_that_was_removed
- test_instructions::test_no_role_file_still_says_dev_evidence | b-4 | absence of one old word | test_no_file_refers_to_something_that_was_removed
- test_instructions::test_no_role_is_described_as_living_beyond_its_scope | b-4 | absence of old phrases | test_no_file_refers_to_something_that_was_removed
- test_instructions::test_no_role_still_writes_its_notes_to_a_squad_level_roles_folder | b-4 | absence of an old path | test_no_file_refers_to_something_that_was_removed ($SQUAD_DIR/roles is in STALE)
- test_instructions::test_the_manager_names_each_inbox_command_and_flag | b-5 | token list of manager inbox wording | test_manager_inbox_read tests; test_every_squad_inbox_word_is_a_cli_command
- test_instructions::test_the_add_bullet_says_the_body_comes_from_a_quoted_heredoc | b-5 | one exact sentence | test_manager_inbox_read::test_existing_rules_of_the_bullet_stay
- test_instructions::test_the_inbox_bullets_carry_the_three_live_wording_rules | b-1 | same sentences are asserted in test_manager_inbox_read | test_manager_inbox_read::test_existing_rules_of_the_bullet_stay
- test_instructions::test_an_inbox_answer_is_never_a_merge_push_or_deploy_request | b-1 | same sentences as test_manager_inbox_read | test_manager_inbox_read::test_carries_only_existing_sentences_stay
- test_instructions::test_qas_write_findings_to_scope_evidence_and_embed_screenshots | b-5 | two exact tokens | none (wording)
- test_instructions::test_manager_and_team_lead_link_each_tickets_evidence_md | b-3 | one token in a composed file | none (wording)
- test_instructions::test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass | b-5 | exact rule wording | test_dev_rules_size::test_must_keep_duties_by_rule_id (REV-14a)
- test_manager_inbox_read::test_a_note_is_never_a_hand_written_row | b-5 | exact sentence | test_a_note_with_nothing_to_decide_goes_through_kind_read
- test_manager_inbox_read::test_the_hand_written_row_licence_is_gone | b-4 | absence of an old phrase | none (removed behaviour)
- test_manager_inbox_read::test_checkin_lists_each_step_the_po_must_take | b-5 | exact sentence | test_checkin_is_one_inbox_item
- test_manager_inbox_read::test_checkin_is_not_a_chat_report | b-5 | counts the word report in a rule | test_checkin_is_one_inbox_item
- test_manager_inbox_read::test_carries_only_allows_the_merge_words_in_the_checkin | b-5 | one phrase | test_carries_only_existing_sentences_stay
- test_manager_inbox_read::test_a_chat_reply_never_lists_steps_for_the_po | b-5 | one phrase | test_checkin_is_one_inbox_item
- test_manager_inbox_read::test_inbox_and_answer_bullets_keep_their_wording_rules | b-1 | same asserts as test_existing_rules_of_the_bullet_stay | test_existing_rules_of_the_bullet_stay
- test_manager_m_l::test_s_keeps_the_pod_health_checks | b-5 | token list of rule wording | test_s_keeps_developer_spawning_and_routing (rule ids)
- test_manager_m_l::test_m_l_manager_does_not_spawn_or_poll_developers | b-5 | exact sentences | test_s_keeps_developer_spawning_and_routing (SPAWN-5a absent at L)
- test_manager_m_l::test_m_l_watch_the_team_lead_only | b-5 | exact sentences | test_s_keeps_developer_spawning_and_routing
- test_manager_m_l::test_team_lead_briefing_carries_size_and_cap_share | b-5 | exact sentences | none (wording; duty table in test_team_duties, held R1)
- test_manager_m_l::test_disputes_split_and_final_stay | b-5 | exact sentences | none (wording)
- test_manager_m_l::test_stacked_base_named_by_manager_used_by_team_lead | b-5 | one exact sentence | none (wording)
- test_manager_m_l::test_merging_reads_sha_from_files_and_checkin_gets_three_returns_line | b-5 | exact sentences plus an absence | none (wording)
- test_hooks_json::test_existing_hooks_kept | b-3 | asserts two command strings of hooks.json | none (config constants)
- test_hooks_json::test_usage_hook_still_exempts_the_manager | b-5 | greps one line of bin source | none (source text)
- test_hooks_json::test_notify_on_stop | b-1 | same wiring check as test_notify_on_notification | test_notify_on_notification
- test_model_effort_settings::test_every_role_has_the_opus_advisor | b-3 | asserts one constant per settings file | test_every_settings_file_has_both_keys_with_allowed_values
- test_model_effort_settings::test_nothing_from_the_base_permissions_was_removed_or_changed | b-4 | compares with commit c1be501 (old base); skips when the commit is absent | none (history check)
- test_po_inbox_contract::test_the_mod_parses_every_fixture_and_the_extra_key_case | b-5 | greps three strings in the mod's .ts tests | the mod tests themselves run in test_po_inbox_mod::test_plugin_test_passes
- test_pod_contact_routes::test_team_lead_routes_in_l | b-5 | exact rule wording at L | test_routes_follow_the_plan_owner_of_the_team (rule ids by team)
- test_pod_contact_routes::test_s_paths_go_to_the_manager | b-5 | exact wording at S | test_routes_follow_the_plan_owner_of_the_team
- test_pod_contact_routes::test_m_paths_go_to_the_qas_and_done_to_the_manager | b-5 | exact wording at M | test_routes_follow_the_plan_owner_of_the_team
- test_pod_contact_routes::test_qa_blackbox_not_copying_team_lead_and_dev_blocked_route | b-5 | exact wording and absences | test_routes_follow_the_plan_owner_of_the_team
- test_pod_rules_process::test_s_keeps_the_confirm_gate_for_all_spawns | b-5 | one phrase | none (wording)
- test_pod_rules_process::test_no_relay_rule | b-5 | one phrase | none (wording)
- test_pod_rules_process::test_final_rule_covers_the_team_lead | b-5 | one phrase | none (wording)
- test_pod_rules_process::test_cap_clause_has_goal_share | b-5 | one phrase | none (wording)
- test_pod_rules_process::test_down_and_handover_clauses | b-5 | two phrases | none (wording)
- test_pod_rules_process::test_team_lead_dispute_wording | b-5 | phrases and absences | none (wording)
- test_pod_rules_process::test_pod_contact_and_team_lead_to_manager | b-5 | phrases | none (wording)
- test_pod_rules_process::test_summary_file_row | b-5 | phrase plus acts() rows that test_m_roles... style tests also show | test_m_roles_include_team_lead_and_l_is_as_m
- test_process_citations::test_rules_do_cite_ids | b-3 | counts at least 10 citations | test_lint_resolves_every_pointer
- test_process_citations::test_agents_skills_bin_cite_no_process_md_heading | b-4 | absence of the old `process.md ->` arrow in cards | none (removed layout)
- test_process_writing::test_every_exception_has_a_reason | b-3 | loops over an empty list | none
- test_process_writing::test_level_bullet_is_first_in_manager_and_rule | b-5 | compares a constant in the test file with itself | none
- test_process_writing::test_no_byte_budget_anywhere | b-4 | absence of a removed parameter | none (removed behaviour)
- test_process_writing::test_manager_card_holds_the_writing_stance | b-5 | three phrases in a card | none (wording)
- test_promotion_0_6_0::test_qa_b_in_rules_is_only_the_reviewer_file_name | b-5 | exact per-file hit counts of a word in rules | test_rules_have_no_size_word_outside_the_tombstones
- test_promotion_0_6_0::test_docs_agents_and_skills_have_none | b-4 | absence of an old word in docs | test_rules_have_no_size_word_outside_the_tombstones
- test_promotion_0_6_0::test_bin_and_hooks_hits_are_allow_listed | b-5 | exact per-file counts of a word in bin and hooks; breaks on any edit | none (ratchet on a removed word)
- test_promotion_0_6_0::test_context_has_team_duty_owner_checker_and_no_size_entry | b-3 | glossary terms exist | none (doc text)
- test_promotion_0_6_0::test_adr_0018_states_where_it_overrides_0016_and_0017 | b-3 | ADR text | none (doc text)
- test_retro_rules::test_coach_reads_backlogs_promotes_repeats_and_cites_both | b-5 | exact rule wording | test_who_shows_the_coach_on_the_backlog_rules_and_the_manager_on_the_follow_ups
- test_retro_rules::test_manager_spawns_the_coach_with_a_prompt_and_never_polls | b-5 | exact rule wording | test_who_shows_the_coach_on_the_backlog_rules_and_the_manager_on_the_follow_ups
- test_retro_rules::test_coach_writes_overlay_operations_and_plugin_proposals | b-5 | exact rule wording | same
- test_retro_rules::test_manager_turns_plugin_items_into_drafts_in_tasks_or_a_tracker | b-5 | exact rule wording | same
- test_retro_rules::test_developer_rules_are_untouched_and_the_card_has_one_stance_line | b-4 | absence plus a count of one phrase in a card | same
- test_retro_rules::test_lint_passes | b-1 | same lint run | test_process_citations::test_lint_resolves_every_pointer
- test_suite_rules_process::test_claude_md_names_the_size_owner | b-5 | exact CLAUDE.md sentence | none (doc text)
- test_suite_rules_process::test_claude_md_points_at_process | b-5 | CLAUDE.md tokens | none (doc text)
- test_suite_rules_process::test_cards_no_longer_hold_suite_text | b-4 | absence of an old phrase in cards | none (removed text)
- test_suite_rules_process::test_no_overlap | b-5 | one phrase in four composed files | test_the_size_owner_runs_it_and_others_never
- test_suite_rules_process::test_timing | b-5 | two phrases | test_the_size_owner_runs_it_and_others_never
- test_suite_rules_process::test_receipt_first_line | b-5 | one phrase twice | none (wording)
- test_suite_rules_process::test_failure_returns_the_task | b-5 | two phrases | none (wording)
- test_suite_rules_process::test_integration_and_light_lines_do_not_make_dev_or_qa_run_it | b-5 | phrases and absences | none (wording)
- test_suite_rules_process::test_integration_task_runs_targeted_tests | b-5 | phrases and absences | none (wording)
- test_task_id_rule::test_rosters_say_ticket_nn | b-3 | one phrase in a template | none (doc text)
- test_team_lead_role::test_old_spawn_route_is_gone | b-4 | asserts two old phrases are absent | none (removed behaviour)
- test_team_lead_role::test_cap_share_rule | b-5 | four exact phrases | none (wording)
- test_team_lead_role::test_no_relay_and_no_routine_manager_message | b-5 | exact phrases | none (wording)
- test_team_lead_role::test_final_rule_and_summary | b-5 | exact phrases | none (wording)
- test_team_lead_role::test_respawn_reads | b-5 | word list in NOTE-3 | none (wording)
- test_team_lead_role::test_keeps_model_and_notes_block | b-3 | asserts settings constants and two headings | test_model_effort_settings::test_every_settings_file_has_both_keys_with_allowed_values
- test_team_lead_role::test_party_to_dispute_does_not_settle_it | b-5 | one exact sentence | none (wording)
- test_team_lead_role::test_summary_names_passed_sha_and_checkers | b-5 | one exact sentence | none (wording)
- test_team_lead_role::test_every_rule_of_the_five_files_reaches_the_same_roles_in_the_7_shapes | b-2/b-4 | 110-rule golden x 7 shapes x 9 roles, a one-off proof against old base 6389642 (size keys); every edit to rule targeting breaks it | test_tech_lead_without_team_lead_respawns_per_cost_4c; duty table test_team_duties (held R1). Risk R1 noted
- test_team_cli::test_no_from_size | b-4 | asserts a removed flag and its absence in source | test_size_only_home_exits_2_with_the_team_line_pointer_and_read_home_raises
- test_team_cli::test_old_line_without_size_is_old_format_too | b-1 | same old-format path as test_old_format_error_is_one_shared_function | test_old_format_error_is_one_shared_function
- test_team_cli::test_undecided_team_has_only_the_manager | b-1 | same --has path as test_has_exit_codes_use_role_names and test_prints_comma_list_none_and_undecided | test_has_exit_codes_use_role_names
- test_team_cli::test_every_old_line_is_named | b-1 | same four old lines are asserted by the shared-function test | test_old_format_error_is_one_shared_function
- test_squad_report_cli::test_no_claude_process_is_spawned | b-4 | absence test, needs a stub shell script | test_output_summary_and_data_json (build runs with no claude)
- test_squad_report_cli::test_no_network | b-4 | absence test (socket patch) | none needed (no behaviour)
- test_squad_report_query::test_frontmatter_name_is_folder | b-5 | wording/format of a skill file | test_referenced_commands_exist
- test_squad_report_query::test_analyze_has_no_write_step | b-4 | absence test on skill text | none needed (no behaviour)

## Kept on purpose
- `processlint`: boundary unit tests, fast.
- `inbox_body_guide`, `po_inbox_mod` (2 real-claude smokes), `squadtranscript` (3 tests, 0.2s).
- `squadinbox`, `squad_team`, `squadreport_*`: behaviour tests of real code, read and kept (only 4 absence/wording tests cut in `squad_report_cli` and `squad_report_query`).

## Not touched
Held (R1, Team Lead decision): `squadrules`, `squadcompose`, `sizes`, `team_duties`, `small_files_equivalence`.
