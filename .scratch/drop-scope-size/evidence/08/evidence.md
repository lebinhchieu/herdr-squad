# 08 Rules: messages, cost, suites, spawning, safety

## Behaviour
- `messages.md`, `cost.md`, `suites.md`, `spawning.md`, `safety.md`: every `when:` is in team language (no `size`, no `qa-b`, no S/M/L); the five files hold no `size` word (test `test_spawning_cost_and_safety_follow_the_team`).
- Keys: `plan-owner` (Manager or Team Lead variants), `suite-owner` (tech-lead / qa-white / dev), `doubt-owner` (designer and architect doubts, BA gaps), `design-notes`, `tech-lead = yes`, `ba = yes`. SAFE-9 and SAFE-10 lost their `when:` (the role composes them only when on the team).
- R9: no `qa-b` left in a `when:` of these files (SPAWN-2b/2c carried it).
- Same roles as base: golden table from base 6389642 for 7 shapes (S, M, M qa-b no, L, L qa-b no, M design, L architecture) x 9 roles, 89 rules, `SameRolesAsBase` in `test_team_lead_role.py`. Only SPAWN-2a/2b/2c differ, by design: the old per-size lists (S, M with qa-b, L with qa-b; M and L without qa-b had none) became one list per plan owner (2a Manager plans, 2b Team Lead plans, 2c "the Team Lead spawns Developers"). IDs kept because the frozen v8 snapshot cites SPAWN-2a/2b/2c and lint reads snapshots (tombstoning 2b broke it).
- Text without absent roles: MSG-11b, MSG-13, MSG-16b, MSG-20b name "the owner `roster.md` names" instead of Tech Lead/BA; MSG-11a/16a/20a say a business doubt "changes the team" ([SIZE-14]), not "the BA" (a Developer at S must not name the BA, `test_sizes`).
- Changelog v9: 15 `changed:` (body changed, with reason) and 61 `retargeted:` lines appended; no ID removed or added.
- G2b: `squad-process lint` on base 6389642 and on the branch: both empty, rc 0.
- Tests fixed to the new keys/titles, no weakening (outside the ticket's list, as in 07): `test_sizes` (orphan tests now sweep the 128 teams for team-language rules: a rule no team composes), `test_dev_rules_size`, `test_manager_m_l`, `test_pod_rules_process`, `test_instructions`, `test_qab_optional`. Added behaviour tests in `test_pod_contact_routes`, `test_team_lead_role`, `test_suite_rules_process`.
- Deferred, same as ticket 07 (Tech Lead DECISION 07): the 5 KiB dev-rules budget tests, skipped "5 KiB trim is ticket 11" (`test_sizes` 1, `test_dev_rules_size` 3). They were green on base, but with a team home the Developer text is 6.7 KB at S because 17 Developer rules in lifecycle/review/evidence (ticket 07) still key on `size`/`qa-b` and match every shape. My five files add at most 34 B per shape (S 773 -> 805, M 620 -> 654, L 632 -> 660 B of title + body; titles of dev-facing rules kept short). Re-enable at integration/11.
- Ran green: every `tests/*.py` hit of `grep -rl` on the changed IDs and file names (advisor_rules, architect_handoff, dev_rules_size, instructions, manager_m_l, pod_contact_routes, pod_rules_process, process_citations, process_conversion, retro_rules, sizes, squadcompose, squad_manager_guard, squadrules, squad_usage_hook, suite_rules_process, task_id_rule, team_lead_role) plus team_lead_perms, team_duties, windows_safe, crlf_squad_files, squad_spawn, qab_optional.

## Gaps for the Tech Lead (not fixed here, no rule exists for them)
- `suite-owner = dev` with a QA blackbox on the team: no QA suite rule (SUITE-2b/2e/6/6b cover tech-lead and qa-white owners).
- Tech Lead without Team Lead: COST-4b ("Respawn once your plan and AC are in files") composes only with `plan-owner = team-lead`.
