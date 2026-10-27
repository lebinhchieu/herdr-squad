# Evidence: 06 Rules: small files
sha: pending

## Behaviour
- who, starting, files, goal, promotion, closing, notes, iterations: no `size` word left (grep clean); `when:` lines now key on duty/presence facts (`plan-owner`, `tech-lead`, `promote-owner`, `handin-target`, `goal`). Retargeted rules keep their ID; changelog v9 lists each changed ID with a reason. No rule removed, no tombstone needed (Tech Lead ANSWER); SIZE-1,2,13,14,22 still cited (live in 05).
- 7-shape equivalence: `tests/test_small_files_equivalence.py`, golden generated from BASE compose; for the 72 rules whose body is unchanged, every present role sees the same rule set at S, M, L, L without QA blackbox, M+design, M+architecture, L+goal. Absent roles skipped. Rewritten rules (WHO-1a/1b/2/2b/2c/2d/2e/3a/3b/8a/8b, START-1/2a/2c/3/3b/19, FILE-5a/5b/6/7/10, GOAL-3a/3c/6b/6d, PROMO-3a/3b/5b, CLOSE-1/3c, ITER-1/3b/6/6a/6b) are covered by their own tests (test_team_duties, test_pod_rules_process, test_process_conversion).
- Deviation, ITER-3b/FILE-8/ITER-6a/6b: use `handin-target` (qas / team-lead / manager) to mimic M,L vs S; ITER-3b body says "when you own the plan".
- Tests updated (cite my rules): test_pod_rules_process.test_summary_file_row (ITER-3 is the Team Lead's at every size; ITER-3b the Manager's), test_process_conversion START-2d `when: plan-owner = team-lead`.
- Lint baseline (G2b): base (merge-base with main) empty, exit 0; branch empty, exit 0.
- Tests green: architect_handoff, crlf_squad_files, dev_rules_size, instructions, manager_inbox_read, manager_m_l, pod_rules_process, process_citations, process_conversion, retro_rules, squadadopt, squad_close, squadcompose, squad_migrate, squad_path_guard, squad_respawn, squadruntime, squad_start, squad_usage_hook, suite_rules_process, team_lead_role, team_models, templates, utf8_helpers, small_files_equivalence.
- Not green, not mine: `test_squadinbox.test_no_pyc` fails on base too. `test_sizes` (45 failures: size-model duty/orphan/v7-changelog tests on S/M absent roles) passes on base and tests the model this scope drops; ticket 04a (`test_sizes.py` in its file list) rewrites it. Tech Lead to confirm.
