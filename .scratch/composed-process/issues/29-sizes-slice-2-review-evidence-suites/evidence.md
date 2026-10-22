# Evidence 29 (slice 2): review, evidence, suites, promotion, lifecycle

## Behaviour

Files: `process/{review,evidence,suites,promotion,lifecycle}.md`, `CLAUDE.md` (Running tests), tests `test_sizes` (new slice-2 classes), `test_pod_contact_routes`, `test_suite_rules_process`, `test_qab_optional` (+ `fixtures/qab/golden.json` regenerated from the merged tree: base is 17 merged on 18), `test_process_conversion`, `test_instructions`, `test_dev_rules_size`. `test_retro_rules`, `test_team_lead_role` unchanged, still pass.

Run: `./bin/squad-process lint` (silent, exit 0). `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest` each of: test_sizes test_pod_contact_routes test_suite_rules_process test_qab_optional test_retro_rules test_process_conversion test_team_lead_role test_dev_rules_size test_instructions test_manager_m_l test_pod_rules_process test_squadcompose test_squadrules test_advisor_rules test_squad_ledger test_windows_safe test_squad_evidence test_process_history test_squadupgrade test_squadruntime → all OK.

### Technical AC
1. Hand-in S → Manager (REV-13a, 14a), M/L → QAs (REV-13b); Done tells Manager at S (LC-20a) and M (LC-20c), Team Lead at L (LC-20b); REV-19 (L) / REV-19b (M) for `qa-b: no`. Code check S = Developer + Opus review subagent (REV-22), Manager confirms both (REV-1, EVID-3a); M, L = QA whitebox (REV-2). Test: `test_hand_in_goes_to_the_manager_at_s_and_the_qas_at_m_and_l`, `test_s_paths_go_to_the_manager`, `test_m_paths_go_to_the_qas_and_done_to_the_manager`.
2. Suite owner S Developer (SUITE-2d), M QA whitebox (SUITE-1b, 3b, 4b, 5b), L Tech Lead (SUITE-1, 3, 4, 5); others unchanged-by-size (SUITE-2a/2b L, 2c/2e M, 6 L, 6b M). `CLAUDE.md` Running tests: "S the Developer, M QA whitebox, L the Tech Lead". Tests: `test_every_size_has_a_suite_owner`, `test_claude_md_names_the_size_owner`, `test_claude_md_running_tests_names_the_size_owner`.
3. `promote.md`: S Developer (PROMO-3b: Manager checks, Duties line carries it), M QA whitebox (SIZE-24b, PROMO-5b/8), L Tech Lead (PROMO-2, 5). PROMO-6 now says "the owner of `promote.md` ([SIZE-22])".
4. `qa-b: no` keeps its meaning: REV-19 (L), REV-19b (M), REV-20, EVID-6, EVID-7. `test_qab_optional` pairs now cover the new letters.
5. Rules acting on tech-lead/team-lead/ba at S or M: none, except exceptions listed in `test_sizes.EXCEPTIONS`: LC-25 (advisor when stuck, all roles, ticket 18, pinned `test_advisor_rules`), LC-26 (advisor before irreversible choice, manager + tech-lead, same), LC-23 (Designer exists at any size when design = yes). `test_no_rule_of_the_five_files_acts_on_an_absent_role` runs `who` for every ID of the five files at S/M x qa-b yes/no and lists failures.
6. Pinned tests edited in the same change; lint clean; `test_windows_safe` OK.
7. Follow-up IDs (29 list at base d8757ba), where each went:
   - evidence: EVID-1 (manager acts, others aware); 2b → L, new 2d (M, to the Manager); 2c → L, new 2e (M Manager checks); 3a (Manager, no reviewer file at S: `## Review` is the record); 3b, 7 (Team Lead aware only); 5 (Developer).
   - lifecycle: LC-1 (Manager, TL aware); LC-2 → L, 2b (S/M Manager); LC-5 → L, 5b (M Manager; S has 1-2 tasks, no QA queue); LC-6 → L, 6b; LC-7a (S, Manager), 7b → L, 7c (M Manager); LC-8 → L, 8b (M QA whitebox), 8c (S Manager Duties line); LC-9 → L, 9b; LC-10 → L (S/M: design notes live in the Duties line, SIZE-6c/6d); LC-11 → L, 11b; LC-12, 13 → L (a migration, contract or cross-repo order is a risk flag = L, SIZE-4); LC-14..17 → L, 17b (S/M Manager plans and tracks); LC-19 → L, 19b (S, M: ASK the Manager); LC-20a/20b/20c; LC-21, 22a get `size in M, L`; 22b → L, 22c (M Manager).
   - promotion: PROMO-1, 4, 6 (manager acts, tech-lead aware); 2 → L; 3a → L; 3b (S: Manager checks); 5 → L, 5b (S/M Manager cites it in the task file).
   - review: REV-1 (Manager); 2 loses the migration step → 2b (L); 3 → L, 3b (M); 4, 6 (QA whitebox, TL aware); 5a (Developer); 7, 8 → L; 14a (Manager), 14b → L, 14c (M); 15 (Manager, TL/Team Lead aware); 16 → L (S/M have no style contract: the design file and the screenshots in `evidence.md` are the bar); 21 → L, 21b (M QA whitebox); new 22.
   - suites: 1 → L, 1b (M), 2d (S); 2a → L, 2c (M), 2b → L, 2e (M); 3 → L, 3b (M); 4 → L, 4b (M); 5 → L, 5b (M); 6 → L, 6b (M).
   - True orphans fixed: REV-1, REV-5a, PROMO-3b, SUITE-3/4/5, LC-22b, EVID-3a, EVID-5 (`test_the_old_orphan_list_is_fixed`).
8. S Developer review duty: REV-22 (`dev`, `size = S`), in composed dev at S, not M or L (`test_review_rule_reaches_composed_dev_at_s_only`); dev S/design yes is 5106 B (cap 5120): `test_dev_rules_size`, `test_dev_rules_stay_within_5_kib`. To make room: PROMO-3b went to the Manager, EVID-2b (S) dropped (S has no reviewer files), shorter titles in LC-18/19b/SUITE-2d/REV-14a. **Not done: `squad-evidence check` enforcing `## Review` at S needs `bin/squadevidence.py`, outside this ticket's files; REV-22 and REV-1 say it must pass, the Manager confirms the section by eye. Needs a ticket in 30 (or a re-issue).**
9. REV-21 (L only) vs REV-21b (M, QA whitebox, no BA): `test_rev_21_has_no_ba_at_m`, `test_m_without_qa_blackbox_has_no_ba_in_rev_21`.

### Decisions I took
- L keeps the old rule ID (and text); the new letter goes to M (REV-14c, 19b, 21b; LC-5b..22c; EVID-2d/2e; SUITE-*b/c/d/e; PROMO-5b), so L-pinned tests keep their IDs.
- No `tl-review.md` at S: the Manager's `PASS` and the Developer's `## Review` section replace it (`process.md:221` and `files.md:104` still name `tl-review.md`; ticket 30 owns them).
- Developer ASK on a design difference goes to the Manager at S and M (LC-19b).
- Suite at M: QA whitebox runs it once every task passed (SUITE-3b); QA blackbox reads its receipt (SUITE-6b).
