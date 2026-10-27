# Evidence: 08 08 Rules: messages, cost, suites, spawning, safety

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
