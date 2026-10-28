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
- 5 KiB budget tests: none skipped (they were green on base and stay green). `test_dev_rules_size.compose` now composes in process with the D1 scaffold (`legacy_scaffold=True`, as `rulesview` does): the CLI never sets it, so a `size:` home had no duty facts and every `plan-owner`/`suite-owner` variant matched (5998 B). In-process bytes equal the CLI's on base 6389642 for all 24 combinations (checked on int1). Result: every combination <= 5120 B; S + architecture is 5 B below base, so `PINNED` is lowered by 5 (5438, 5437, 5147, 5146), never raised. Dev-facing titles of MSG-4a, MSG-11a, COST-5a, SUITE-2d kept the base length or shorter.
- SPAWN-2a/2b/2c (the one deliberate difference from base, not in the golden): the old per-size lists (2a S; 2b M and qa-b yes; 2c L and qa-b yes) became 2a Manager plans, 2b Team Lead plans (the Manager spawns the Team Lead and the team), 2c "the Team Lead spawns Developers". R9: the `qa-b = yes` clause is dropped, not translated to `qa-black = yes`: a spawn list does not depend on QA blackbox (M and L without qa-b had no list in base, a gap), and a `when:` names the duty value only (architecture §3). The Token Coach follows ITER-6a and ITER-6b (base 2b/2c listed it unconditionally). Spawning without QA blackbox: SIZE-21a (the confirmed team).
- Ran green: every `tests/*.py` hit of `grep -rl` on the changed IDs and file names (advisor_rules, architect_handoff, dev_rules_size, instructions, manager_m_l, pod_contact_routes, pod_rules_process, process_citations, process_conversion, retro_rules, sizes, squadcompose, squad_manager_guard, squadrules, squad_usage_hook, suite_rules_process, task_id_rule, team_lead_role) plus team_lead_perms, team_duties, windows_safe, crlf_squad_files, squad_spawn, qab_optional.

## Gaps closed (Tech ANSWER 08)
- SUITE-2f (QA blackbox, `suite-owner = dev`): run touched test files; the Developer owns the full suite on the final sha. Test over the 128 teams: every team with `qa-black` gets exactly one of SUITE-2f/2e/2b by its suite owner (64 teams).
- COST-4c (`tech-lead = yes`, Tech Lead): "Respawn once your design and AC are in files." One `when:` primary key only (`squadrules.py` PRIMARY_KEYS, no engine change in 08), so a Tech Lead with a Team Lead gets both COST-4b and COST-4c: accepted, recorded in changelog v9. Test over the 64 teams with `tech-lead`: 4c always, 4b only with `team-lead`.
- Same-roles golden: COST-4c, like SPAWN-2a/2b/2c, is new and a deliberate difference. Changelog v9 `added:` lists SUITE-2f and COST-4c with reasons.
- Re-ran green: suite_rules_process, team_lead_role, pod_contact_routes, team_lead_perms, sizes, dev_rules_size (5 KiB budgets), manager_m_l, qab_optional, instructions, pod_rules_process, process_conversion/history/writing/citations, processlint, squadprocess, squadcompose. `squad-process lint`: empty, rc 0.

## QA whitebox

### QA whitebox 08 on f041603 (final sha per Tech DECISION 08)
PASS. Checked from `git archive` copies of c73908c and f041603 (the Dev worktree was being edited live; I did not test it).
- Lint exit 0 empty. 296 targeted tests OK, 3 skipped (pre-existing): test_team_lead_role, test_suite_rules_process, test_pod_contact_routes, test_sizes, test_dev_rules_size (5 KiB tests run, not skipped), test_manager_m_l, test_qab_optional, test_instructions, test_pod_rules_process, test_architect_handoff, test_team_lead_perms, test_team_duties, test_crlf_squad_files, test_squadrules, test_processlint. (test_windows_safe git-attribute tests fail only inside a git-archive copy: no .git.)
- Own base-vs-branch compose (base 6389642 `size:` vs branch `team:` = legacy_team), S/M/L x design x architecture x goal x every present role, MSG/COST/SUITE/SPAWN/SAFE: rule-ID sets equal except SPAWN-2a/2b/2c (intended: per plan owner, M gets 2a, L gets 2b+2c, same roles listed) and new COST-4c at L (see below). Body changes beyond titles: MSG-11b/12/13/16b/20b (named roles replaced by "the owner roster.md names" / "plan owner"), MSG-6, MSG-11a/16a/20a ("changes the team"), SPAWN-2a/2b/2c/3/4/4a. All as the ticket and tech design describe.
- qa-b no (M, L with `qa-white`, no `qa-black`) vs base `qa-b: no`: no rule gone; SPAWN-2 differences only.
- All 128 team sets: Manager always has a spawn list, MSG-4/7, COST-10, SPAWN-10 rule; Dev has SUITE-2, COST-5, MSG-4, MSG-11; every present role has MSG-4; QA whitebox/blackbox always have a SUITE rule (SUITE-2f closes the qa-black-only gap I found on c73908c); Tech Lead always has a COST-4 rule (COST-4c closes the Tech-Lead-without-Team-Lead gap).
- Note (non-blocking, Tech Lead accepted in the test comment): at L the Tech Lead now composes COST-4b and COST-4c (two respawn lines, "plan and AC" and "design and AC"); the engine allows one duty key per `when`, so `tech-lead = yes and plan-owner = manager` is not expressible. Golden in test_team_lead_role excludes COST-4c.

## QA blackbox

### QA blackbox, task 08 (HANDIN c73908c, branch squad/plugin/drop-scope-size/plugin-dev-dsz-08)

Method: scratch homes (scope.md `plugin: 0.6.0 abc1234` + `team:`), 13 shapes (none; qa-white; qa-black; qa-white,qa-black; team-lead; team-lead,qa-white; tech-lead; ba; full L; L without qa-black; designer+QAs; architect+QAs; blank), `squad-process compose` for 6-9 roles, `lint`. Old-size baseline: same compose on INT1 6389642 with `size: S|M|L` homes, composed bodies of the messages/cost/suites/spawning/safety rules compared by text. CLI only. Judged only 08's five files; ITER-6a/6b live in iterations.md (ticket 06, merged on INT2).

| Check | Saw | Result |
|---|---|---|
| Compose 13 teams x 6 roles | exit 0 everywhere | PASS |
| `lint` per team | no output | PASS |
| `size` word / `[if size` / `qa-b` in the rules of the five files (all shapes, all roles) | none | PASS |
| Plan-owner pairs (MSG-4a/b, 7a/b, 8a/b, 11a/b, 18/19; COST-5/5a, 6a/b, 10a/b, 13a/b, 14a/b; SPAWN-2a/b, 5a/b, 8a/b, 10a/b) | exactly one variant per role per decided team: Manager variants (`a`) with no Team Lead (none, qa-white, qa-black, QAs, tech-lead, ba, designer, architect), Team Lead variants (`b`) with a Team Lead; blank team keeps both | PASS |
| Suite owner (SUITE-1..6) | no QA, no tech-lead: Dev `SUITE-2d`; qa-white (with or without qa-black): Dev `SUITE-2c`, QA whitebox `SUITE-1b/3b/4b/5b`, QA blackbox `SUITE-2e/6b`; tech-lead on team: Tech Lead `SUITE-1/3/4/5`, Dev `SUITE-2a`, QAs `SUITE-2b/6` (matches CLAUDE.md: S Dev, M QA whitebox, L Tech Lead) | PASS |
| Equivalence S -> `none`, M -> `qa-white,qa-black` | Manager and Developer rule bodies of the five files identical to the old S/M text; QA whitebox/blackbox identical for M | PASS |
| Equivalence L -> full L | Developer identical; Manager and Team Lead differ only by intended rewording: "signal to add a role to the team", "Tell every agent its scope's team", spawn line "every other role on `team:` ... `squad-spawn` refuses a role that is not on the team", "Raise gaps to the owner `roster.md` names" | PASS |
| MSG-12/14/15/16/17/20 (role-gated) | appear only with ba / tech-lead / designer / architect on team | PASS |
| Token Coach | Manager rule points at ITER-6a/6b; on INT2 (with 06) they read "no QA and no Team Lead: only when the PO asks" / "with a QA or a Team Lead: every scope" | PASS |

Not mine: Dev rules 5 KiB (ticket 11), tests.

Findings: none. Verdict waits for the Tech Lead's final sha (REV-3).

#### Re-check, HANDIN f041603 (delta from c73908c; final sha per Tech Lead DECISION 08)

Method: compose 6 roles for 4 teams (none, team-lead, tech-lead, full) on c73908c and f041603, rule-id lists compared per role; rule texts read; `lint` per team.

| Check | Saw | Result |
|---|---|---|
| SUITE-2f | Only QA blackbox, only when the Developer owns the suite (no QA whitebox, no tech-lead: none, qa-black, team-lead, ba). Text: run only touched test files, Developer owns the full suite on the final sha, no overlap. Matches CLAUDE.md (S Dev owns). Absent when qa-white (2e) or tech-lead (2b) | PASS |
| COST-4c | Only Tech Lead, only on teams with tech-lead: "Respawn once your design and AC are in files." Tech Lead on a no-team-lead team had only 4a before | PASS |
| Nothing else changed | Other roles' rule lists identical between c73908c and f041603; Tech Lead rest only renumbered | PASS |
| Compose / lint | exit 0, lint empty on all four teams | PASS |

Findings: none. Non-blocking note: Tech Lead with a Team Lead gets both COST-4b and COST-4c (same sense, two sentences).

## Team Lead review

- final: code f041603 (SUITE-2f, COST-4c added); lint 0; targeted tests OK (TL 2026-10-27)
