# Ticket 10b: prune the five R1 rules-wording test files

**Result:** 104 rows in `removed.tsv` (103 tests removed, 1 shape-matrix row). 217 tests became 115 (-47%). One test was added: the per-role net test. Code sha `fe7c3df`, base `e24f306`. Tests only.

| file | tests before | after | lines before | lines after | verdict |
|---|---|---|---|---|---|
| test_squadrules | 61 | 43 | 509 | 370 | pruned 30%: engine tests, one per lint class, kept on purpose |
| test_squadcompose | 81 | 42 | 744 | 502 | pruned 48% |
| test_sizes | 34 | 8 | 564 | 138 | pruned 76% (+1 new net test); fewer than 10 tests, see below |
| test_team_duties | 39 | 20 | 345 | 165 | pruned 49% |
| test_small_files_equivalence | 2 | 2 | 169 | 92 | 5 of 7 shapes cut (90 golden rows), tests stay |

`test_sizes` ends with 8 tests (below 10, as the Tech Lead allowed): 7 team-model tests and the new net test. The S/M/L-era classes were cut as the size model (PO "Added" 2026-10-31). `test_sizes` is also faster on Linux: 127s to 7.5s on WSL.

## Kept net
| role | kept test |
|---|---|
| manager, team-lead, tech-lead, qa-whitebox, qa-blackbox, ba, designer, dev, token-coach, architect | `test_sizes::ComposedPerRole::test_each_role_composes_its_header_duties_line_and_must_own_rule_ids` (new; one test, ten roles, IDs only; `duties:` line present exactly for manager, team-lead, tech-lead) |
| duty owners | `test_team_duties::Sweep::test_all_128_sets_have_one_present_owner_per_duty` (named by the Tech Lead) and `test_sizes::TeamRules::test_who_lists_exactly_the_acting_roles_per_duty_fact_and_value` |
| small files per role | `test_small_files_equivalence` (both tests, shapes M and Lgoal) |
| lint and citations | `test_squadrules` lint-class tests, `test_template_rule_files_lint_clean`, `test_pointer_*`, `test_bare_ids_are_not_pointers`; `test_sizes::test_every_pointer_to_a_size_rule_in_the_templates_resolves` |

No composed-per-role test with IDs existed before, so it was written new. Its IDs per role are role-defining rules (for example dev: START-10 REV-13b EVID-2a SUITE-2a), not sentences.

## Decisions to look at
- `test_commentary_that_contradicts_the_mapping_is_not_applied` names "ticket 02" in its docstring. It was cut with all `LegacyTeam` tests because the Tech Lead's Added list says so (`legacy_team` has no caller in `bin/`).
- Class `CutoverTest` (ticket 12) is kept; its two role loops now run `dev` and `manager` instead of all ten roles (cheaper, same path).
- `test_sizes::Changelog` had an existing skip (clone without base `2e81e5e`); it went with its test. Zero new skips.
- Fixture `tests/fixtures/rules/compose/golden/dev-M-design.rules.md` deleted (only the cut golden test read it).
- Known leftover (not done, as the Tech Lead said): `legacy_team` stays in `bin/squadrules.py`.

## Mutation proof (`mutation.txt`, scratch copy, never committed)
| mutation | test that failed |
|---|---|
| dev: delete REV-14a | `ComposedPerRole` fails |
| tech-lead: move SUITE-1 to `roles: manager` | `ComposedPerRole` fails: `['SUITE-1']` lost by tech-lead |
| designer: delete START-12 | `ComposedPerRole` fails: `['START-12']` lost by designer |
| duty: plan-owner chain loses the manager end | `Sweep::test_all_128_sets...` and `test_thirteen_duties...` fail |
Unmutated: both pass.

## Per-file results
Linux (WSL Debian): `after-linux.txt`, all OK. Windows (python 3.14): `after-windows.txt`, all OK; the same files were all OK at the base. Files: the five, plus `test_processlint`, `test_process_citations`, `test_instructions`, `test_pod_rules_process`. Hits of `grep -rl dev-M-design`: only the cut test. No full suite run.
