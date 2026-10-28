# QA blackbox, task 08 (HANDIN c73908c, branch squad/plugin/drop-scope-size/plugin-dev-dsz-08)

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

## Re-check, HANDIN f041603 (delta from c73908c; final sha per Tech Lead DECISION 08)

Method: compose 6 roles for 4 teams (none, team-lead, tech-lead, full) on c73908c and f041603, rule-id lists compared per role; rule texts read; `lint` per team.

| Check | Saw | Result |
|---|---|---|
| SUITE-2f | Only QA blackbox, only when the Developer owns the suite (no QA whitebox, no tech-lead: none, qa-black, team-lead, ba). Text: run only touched test files, Developer owns the full suite on the final sha, no overlap. Matches CLAUDE.md (S Dev owns). Absent when qa-white (2e) or tech-lead (2b) | PASS |
| COST-4c | Only Tech Lead, only on teams with tech-lead: "Respawn once your design and AC are in files." Tech Lead on a no-team-lead team had only 4a before | PASS |
| Nothing else changed | Other roles' rule lists identical between c73908c and f041603; Tech Lead rest only renumbered | PASS |
| Compose / lint | exit 0, lint empty on all four teams | PASS |

Findings: none. Non-blocking note: Tech Lead with a Team Lead gets both COST-4b and COST-4c (same sense, two sentences).
