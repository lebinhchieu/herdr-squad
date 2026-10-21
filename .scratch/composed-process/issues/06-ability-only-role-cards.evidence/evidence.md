# Evidence 06: role cards hold ability only

## Behaviour

Tests: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_instructions test_pod_rules_process test_suite_rules_process test_task_id_rule test_team_lead_role test_manager_m_l test_designer_handoff test_pod_contact_routes test_process_citations` plus the files that read cards or lint: `test_squadrules test_manager_inbox_read test_process_writing test_crlf_squad_files test_model_effort_settings test_squadcompose test_process_conversion` → 223 OK. `squad-process lint` (default now `--cards error`) exits 0, prints nothing.

### Technical AC
1. **Lint.** `bin/squad-process lint` → exit 0, no output (before: 40 card-duplicate warnings). Default flipped in `bin/squadrules_cli.py:102` (`default="error"`); `test_squadrules.test_cards_default_is_error`.
2. **≤ 30 lines.** Cards are 13-17 lines after frontmatter (manager 17); `test_instructions.CardShapeTest.test_each_card_is_at_most_30_lines_after_frontmatter`. Shape: `You are…`, `## Stance`, `## Tools` (names only), closing line `roles/<agent>.rules.md` + `[CORE-3]` (`test_each_card_ends_with_the_pointer_line`). The manager card also keeps a short `## Writing a rule` stance (mapping's "stays in card" lines 34-40).
3. **Assertion map** below.
4. `test_process_citations` now runs `squad-process lint` for `[ID]` pointers (`test_lint_resolves_every_pointer`, `test_an_unknown_pointer_is_reported` with a fake `[MSG-99]` → exit 1).
5. **Probe** (Haiku, composed rules at M, design yes): below.

### Open item: no `squad-process show` from a composed path
`grep -rn "squad-process show" agents skills bin templates` lists: `bin/squadprocess.py:156` (the command's own header), `bin/squad-process:7` (usage), `bin/squad-respawn:59` (legacy-mode prompt only; composed mode overrides it on the next line), and the `allow` entries of four settings templates (stay until 09). No card, skill or rule. `test_squadrules.test_no_card_calls_squad_process_show` covers agents and skills; `CardShapeTest.test_no_card_calls_show_or_names_process_md` also bars `process.md` in card bodies. Legacy squads (B06-6) are ticket 24, checked at integration.

### B06-7 Card + rules vs card + `show`, worst size (bytes)
| role | old card | `show` (v6) | old total | new card | composed worst of 12 | new total | ≤ old |
|---|---|---|---|---|---|---|---|
| manager | 16874 | 24424 | 41298 | 1929 | 39216 | 41145 | yes |
| ba | 2930 | 24424 | 27354 | 959 | 9666 | 10625 | yes |
| team-lead | 5760 | 24424 | 30184 | 1222 | 17418 | 18640 | yes |
| tech-lead | 6026 | 24424 | 30450 | 943 | 25926 | 26869 | yes |
| qa-whitebox | 3703 | 8598 | 12301 | 924 | 9995 | 10919 | yes |
| qa-blackbox | 3074 | 8598 | 11672 | 1046 | 9248 | 10294 | yes |
| designer | 2602 | 6405 | 9007 | 970 | 7201 | 8171 | yes |
| dev | 5172 | 8590 | 13762 | 884 | 10945 | 11829 | yes |
| token-coach | 2189 | 24424 | 26613 | 890 | 3216 | 4106 | yes |
(`show` for BA, Team Lead, Tech Lead, Manager and Token Coach has no section view; the whole v6 `process.md`, 24424 B, is what they read. Manager is under by 153 B only.)

### B06-8 Finding 4 text
`test_review_finding_4_text_is_gone`: no "label shape" or "(Retro)" in manager.md, no `escalations.md` in tech-lead.md. Ready-tasks duty: `squad-process who START-2d` → S: acts `tech-lead`.

### B06-4 Duties reachable
Targeting is asserted on rules (`rulesview.who` / `acts`), e.g. `who REV-3`: M and L act `tech-lead, qa-whitebox, qa-blackbox`, aware `dev, team-lead`; `who SAFE-9`: `qa-whitebox`. `test_process_conversion` still passes (mapping.md accounts for every source line, unchanged).

### Probe (AC 5, B06-5)
Roles composed with `squad-process compose <role> --home <M scope, design yes> --out <role>.rules.md`; each run:
`claude -p "<Search your system instructions for exact phrases A (own rule) and B (rule not targeted at it)…>" --model haiku --plugin-dir <this worktree> --agent squad:<role> --append-system-prompt-file <role>.rules.md --output-format json --tools ""`. B = MRG-1 phrase ("Do not offer to merge in place of asking the PO", Manager only); Full output: `probe-output.txt`.

| role | A (own) | marker A | B (foreign) | cost USD |
|---|---|---|---|---|
| manager | YES | MRG-1 "Do not offer to merge in place of asking the PO" | NO (SAFE-10, QA blackbox only) | 0.0044 |
| ba | YES | REV-8 "Agree the business AC before work starts" | NO | 0.0015 |
| team-lead | YES | LC-15 "Each task fits one Developer session" | NO | 0.0021 |
| tech-lead | YES | LC-14 "split work so parallel tasks do not touch the same files" | NO | 0.0028 |
| qa-whitebox | YES | REV-2 "check out the Developer's branch (read-only)" | NO | 0.0014 |
| qa-blackbox | YES | REV-9 "test the running app the way" | NO | 0.0014 |
| designer | YES | LC-23 "one self-contained file, no network, opens from disk" | NO | 0.0013 |
| dev | YES | REV-13b "to QA whitebox and QA blackbox, copy the Team Lead" | NO | 0.0016 |
| token-coach | YES | ITER-8 "Find waste in the table" | NO | 0.0009 |
Total ≈ $0.017 (cap $0.20).

### Assertion map (old test → new)
Tests outside the ticket's Touches that also read cards and had to move: `test_manager_inbox_read` (inbox lines now from `ITER-4/5/11`), `test_process_writing.test_manager_holds_the_rule_verbatim` → `test_manager_card_holds_the_writing_stance`, `test_crlf_squad_files.InstructionWordingTest` (roster/LF wording from `FILE-4`/`FILE-5*` via composed manager and team-lead rules).

**test_instructions**
- `test_manager_and_dev_know_the_label_rule` → same name, on composed rules (SPAWN-7, dev).
- `test_every_scope_role_starts_by_reading_its_scope_folder` → same name, on composed rules (START-6/7).
- `test_the_manager_covers_both_modes…`, `test_the_designer_is_wired…`, `ManagerInboxTest.*` → same names, composed manager rules; `test_the_add_bullet_says…` wording follows ITER-4 ("body goes in").
- `test_every_command_an_instruction_tells_agents_to_run_exists` → same name, adds composed rules; unchanged tests: project row, stale tokens, lifetimes, notes path, process variables (v6 template, until 09), init jsonl.
- `SectionViewTest.test_each_section_role_runs_its_own_show_command`, `test_other_roles_do_not_use_show` → `CardShapeTest.test_no_card_calls_show_or_names_process_md`.
- `test_the_fallback_sentence_names_exactly_the_role_view`, `test_every_citation_is_in_the_role_view_or_listed_as_outside_it` → deleted: the sentence and the card citations are gone; `[ID]` pointers are linted (`test_process_citations`).
- `test_show_is_allowed_for_exactly_the_four_roles…`, `test_dev_copies_reports…`, `test_dev_writes_evidence_md…`, `test_tech_lead_checks_evidence_md…`, `test_qas_write_findings…`, `test_manager_and_team_lead_link…` → `RuleDutiesTest.<same name>`; `test_no_role_file_still_says_dev_evidence` → `CardShapeTest.<same name>`.
- New: `CardShapeTest` (30 lines, closing line, finding 4, tool names exist).

**test_pod_rules_process** (all were on the v6 template)
- `test_m_roles_include_team_lead_and_l_is_as_m` → same name (`who MSG-5`); `test_plan_duty_row_is_tech_lead_in_s_only` → `test_plan_duty_is_tech_lead_in_s_only` (SIZE-6a, LC-15); `test_pod_contact_and_team_lead_to_manager_bullets` → `test_pod_contact_and_team_lead_to_manager`; `test_summary_file_row` → same (ITER-3); `test_cap_bullet_has_goal_share_clause` → `test_cap_clause_has_goal_share`; `test_final_rule_covers_the_team_lead` → same (MSG-7b); `test_no_relay_bullet` → `test_no_relay_rule` (MSG-10); `test_down_and_handover_clauses`, `test_s_keeps_the_confirm_gate_for_all_spawns` → same; `test_team_lead_to_manager_dispute_wording` → `test_team_lead_dispute_wording` (WHO-8c).
- `test_s_row_is_unchanged` → deleted: compared the v6 size table with V3; `test_process_history` owns history files and SIZE rules are linted.
- `test_no_leftover_old_model`, `test_no_byte_budget` → deleted: absences in the v6 template text; rule files are linted.

**test_suite_rules_process**: `test_suites_bullet_replaces_long_suites` → deleted (v6 heading); `test_tech_lead_runs_it…`, `test_no_overlap`, `test_timing`, `test_receipt_first_line`, `test_failure_returns_the_task`, `test_integration_and_light_lines…` → same names on SUITE-1..5, SUITE-2a/b, LC-21 (qa light); `test_claude_md_points_at_process` → same; `test_role_files_cite_the_rule` → `test_cards_no_longer_hold_suite_text`; `test_integration_task_in_role_files_runs_targeted_tests` → `test_integration_task_runs_targeted_tests` (GOAL-6a/6b).

**test_task_id_rule**: `test_template_has_bullet` → `test_rule_is_targeted_at_every_role_and_size` (MSG-3); `test_v5_has_it_v4_not` → deleted (history files, `test_process_history`); `test_rosters_say_ticket_nn` unchanged.

**test_team_lead_role**, **test_manager_m_l**, **test_designer_handoff**: every test keeps its name; assertions now on composed rules of the role (and the card for identity: "M and L", no `model:` key).

**test_pod_contact_routes**: `test_every_manager_line_is_allowed` → `test_every_manager_line_of_a_card_is_allowed` (all 9 cards, shorter allow list); other three keep names, assert on composed rules per size.

**test_process_citations**: `test_the_19_headings_are_pinned_in_order`, `test_named_places_exist` → deleted (v6 headings; `test_process_history` pins the template); `test_every_citation_resolves` → `test_lint_resolves_every_pointer` + `test_agents_skills_bin_cite_no_process_md_heading`; `test_there_are_citations_to_check` → `test_rules_do_cite_ids`; `test_a_renamed_heading_is_reported`, `test_a_missing_named_bullet_is_reported` → `test_an_unknown_pointer_is_reported`.

### Not checked here
B06-6 (legacy squad gets its duties) is ticket 24 / integration. The closing line "rules are attached" is true in composed mode only until then.
