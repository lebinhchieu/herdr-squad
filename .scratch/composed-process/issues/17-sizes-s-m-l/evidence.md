# Evidence 17 (slice 1): sizes S / M / L

## Behaviour

Files: `process/{sizes,who,starting,spawning}.md`, new `tests/test_sizes.py`, pinning tests (`test_manager_m_l`, `test_pod_rules_process`, `test_team_lead_role`, `test_process_conversion`, `test_qab_optional` + `fixtures/qab/golden.json` regenerated). Slices 29-31 own review/suites/evidence/lifecycle/promotion/cost/messages/files/iterations/notes/goal/closing/safety, CLAUDE.md.

Run: `squad-process lint` (silent, exit 0). `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_sizes test_squadrules test_squadcompose test_pod_contact_routes test_pod_rules_process test_process_conversion test_qab_optional test_manager_m_l test_team_lead_role test_dev_rules_size test_process_citations test_squadadopt test_instructions test_suite_rules_process test_retro_rules test_squadprocess test_squadprocess_apply test_process_history test_squadupgrade test_windows_safe test_templates test_processlint` → 383 OK.

### Technical AC (tasks/tech-ac.md, 17)
1. Role sets: `test_named_owner_acts_at_its_size`, `test_rules_of_this_slice_never_act_on_an_absent_role` (48 rule IDs x S/M/L), `test_l_only_roles_act_nowhere_else_on_slice_rules` (Team Lead, BA, Tech Lead rules empty at S, M).
4. Owners per size: table in SIZE-22 (plan/spawning, design notes, technical AC, business AC, code check, behaviour check, hand-in/done, full suite, `promote.md`, migration/risk flag/business doubt, irreversible choice, 3 returns); `OWNERS` in test_sizes checks the rules of this slice by `who`. Suite, `promote.md`, hand-in rules are slice 29 (table row only here).
5. Risk flags force L: SIZE-4 (`test_every_risk_flag_forces_l`); business doubt S, M → L: SIZE-5a, SIZE-5c, SIZE-14 (`test_business_doubt_moves_s_and_m_to_l`).
7. Scope sizes (`size:` / `plugin:`): open: `scopes/sizes-and-models` size M, no `plugin:` pin; goal `composed-process` has neither line. Closed (`_done`): S ask-timeline, ca-win, evidence-inline, fix-autoswitch; M 11 scopes; L process-fixes, role-cards-upgrade, squad-report. No closed scope carries `plugin:`. Open scopes under the old meanings: only sizes-and-models (legacy squad, no `process.local.md`). Deploy order (decision 9): merge and install after every open scope has closed, or run `adopt` first so open scopes get pins; the PO deploys.
8. Retargeted IDs (for the changelog, slice 31): SIZE-2, 4, 5a, 5b, 5c(new), 6a, 6b, 6c(new, was 6c none), 7a, 8a, 10a, 11a, 11b, 13, 14, 15, 16, 17a-e (17e new), 21 → 21a/21b, 22 (new), 23b (new); WHO-1a, 1b, 2, 2d(new), 2b, 2c, 3a, 3b, 8a, 8b, 8c; START-2a, 2b, 2c, 2d; SPAWN-2a, 2b, 2c(new), 5a, 5b, 8a, 8b, 9, 10a, 10b.

### Decisions I took
- Developer 5 KiB cap (test_dev_rules_size): S design notes/technical AC/`promote.md`/BLOCKED duties reach the Developer in the Manager's first prompt (SIZE-6c, Manager rule) instead of a new Developer rule; no Developer rule grew (S 4912 → 4912 + header only).
- WHO-2 (Technical owners) now L only; WHO-2d gives S and M the Manager (irreversible choice after an advisor call) and the Developer (design notes).
- Pinning tests moved from M to L where they read Team Lead / Tech Lead rules (`composed("team-lead", "L")`).

### Follow-up rule IDs not retargeted (feed 29/30)
Rules that still act on a role absent at S or M (from `who`, my files excluded):
- closing: CLOSE-3a. cost: COST-1,2,3,4a,4b,6b,7,9,10b,11,13a,13b,14a,14b. evidence: EVID-1,2c,3a,3b,5,7. files: FILE-1,2,3,4,5c,7,8,9,10,11. goal: GOAL-2,3a,3b,4,5,6a,6b,6c. iterations: ITER-3. lifecycle: LC-1,2,5,6,7b,8-17,21,22a,22b. messages: MSG-1,2,3,4a,4b,5,6,7a,7b,8b,9,10,12,13,14,15,19. notes: NOTE-1,3. promotion: PROMO-1,2,3a,3b,4,5,6. review: REV-1,3,4,5a,6,7,8,15,16,21. safety: SAFE-2,5,9,10,11. suites: SUITE-1,3,4,5.
- Of these, true orphans at S or M (no present role acts): REV-1, REV-5a, MSG-4a (S), PROMO-3b, SUITE-3/4/5, COST-4a, LC-22b, EVID-3a, EVID-5, GOAL-2/3a (S, M), CLOSE-3a.
- In my files, accepted (join-on-move-up, composed only when that role exists): SIZE-17a-e.
- Stale pins to fix in 29/30: `test_pod_contact_routes.test_s_paths_stay` (REV-13a/REV-1 still name the Tech Lead until 29).
- Developer S rules still say "to the Tech Lead" (REV-13a, 14a, LC-20a, MSG-4a/11a, EVID-4): slice 29/30.
