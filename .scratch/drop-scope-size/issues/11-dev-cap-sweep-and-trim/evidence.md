# Evidence: 11 Developer 5 KiB sweep and trim
sha: d2e8d06

## Behaviour
- Sweep: 128 team sets x goal x qa (full, light), `dev` composed from a `team:` home (live-length names, no scaffold). Base 90be196: worst 5674 B, 140 of 256 (set x goal) over 5120. Now: worst 5110 B; 0 of 512 combos over 5120. No exceptions, no CAP (`EXCEPTIONS`/`CAP` deleted); `test_every_team_set_fits_5_kib` asserts every combo <= 5120. Per-rule breakdown of the old worst set: `$SCOPE_DIR/tasks/11-worst-set-breakdown.md`.
- On demand (ADR 0016:37): REV-5a and EVID-5 have an empty `roles:` (line kept, `when:` kept), cited from REV-22 / LC-19. `squad-process who REV-5a|EVID-5`: acts `-`, aware `-` at every key; no role composes them. Lint relaxed (`squadrules._structure`): a present empty `roles:` is allowed, a missing line stays `missing roles:` (Tech ANSWER 11). Tests: `test_on_demand_rules_attach_to_no_role`, `test_manager_composed_bytes_did_not_grow_vs_90be196` (Manager bytes at 90be196 hard-coded for 6 team/goal combos; now smaller or equal), `test_empty_roles_is_on_demand_and_lints_clean`; test_sizes orphan/pointer checks skip on-demand rules.
- Wording trims (changelog v9 `changed:`, duties kept): CORE-4/5/6, START-6/10 (title Dev start), MSG-3, MSG-11b (asks as MSG-4b says), LC-3a, LC-18 (title Dev work), LC-19, LC-19c, LC-25 (title Advisor), REV-14a, REV-22a, EVID-2a/2b/4, COST-5/5a. Pinned texts updated in tests: LC-25 (test_advisor_rules), LC-19c (test_architect_handoff). safety.md and the compose header untouched.
- Lint baseline (G2b): `squad-process lint` on 90be196 empty, exit 0; branch empty, exit 0.
- Tests green (touched/grep hits): dev_rules_size, sizes, architect_handoff, instructions, manager_m_l, pod_contact_routes, pod_rules_process, squadruntime, team_lead_role, advisor_rules, windows_safe, crlf_squad_files.

- QAB finding fixed: LC-19b (design notes by the Manager, no Tech Lead) now carries `Shots: [EVID-5]`; changelog row added; `test_developer_file_cites_evid5_wherever_it_applies` checks every team set where EVID-5 applies (fails 129 subtests without the pointer). 512 combos still <= 5120 (worst 5110).
