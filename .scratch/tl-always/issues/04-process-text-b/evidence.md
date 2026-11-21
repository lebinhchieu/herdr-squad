# 04 Process text B: evidence

## Review

AC trace (`cd tests; python3 -m unittest <file>` for tests, repo root for greps):

- AC1 | `squad-process lint` exit 0; tombstones in `_removed.md` (15 IDs, `replaced_by` each); grep `plan-owner\|team-lead = ` over the seven files: empty | run from repo root
- AC2 | grep of the 15 removed IDs over bin hooks agents skills tests templates: hits only `_removed.md`, `changelog.md`, fixtures, and two `assertNotIn("## SPAWN-5a")` lines plus a historical byte comment in tests | grep in `## Behaviour`
- AC3 | `tests/test_rules_contract.py` (row `acts("SPAWN-12","S") == ("manager",)`, `test_manager_subagent_default_rule`: three phrases, absent from dev and team-lead) | `python3 -m unittest test_rules_contract`
- AC4 | `test_rules_contract.py::test_spawning_cost_and_safety_follow_the_team`, `test_team_lead_spawns_and_retires_dev_only` | same
- AC5 | `tests/test_squad_usage_hook.py::test_developer_text_is_the_same_for_every_scope_md_shape` | `python3 -m unittest test_squad_usage_hook`
- AC6 | `test_windows_safe`, `test_utf8_helpers`, `test_instructions` | each OK, see `## Behaviour`
- AC7 | `tests/test_dev_rules_size.py` | OK
- AC8 | touched files plus grep hits (`test_sizes`, `test_architect_handoff`, `test_small_files_equivalence`, `test_rules_wording`) | OK, 88 tests

## Behaviour

- Rules: the 14 `plan-owner = manager` rules and ITER-3b removed; `when: plan-owner = team-lead` dropped; SIZE-17b lost `team-lead = yes`; FILE-7 row says "Team Lead (from the Manager's plan)". "plan owner" wording became Team Lead or Manager (sizes.md BA rule, files.md summary). SPAWN-4a cites SPAWN-2b only; starting.md cites COST-6b.
- New SPAWN-12 (manager only): subagents default `model: sonnet`, `effort: high`, per-task choice, fork allowed.
- `bin/squad-usage-hook`: the `team` parse and COST-5a branch deleted; Developer text always "the Team Lead" and `[COST-5]`.
- COST-13b reworded to name no role ("the iteration file, the final sha named, or its verdict posted"): without the condition it composes for teams with no Tech Lead, and `test_architect_handoff` forbids that name.
- Tests edited: test_rules_contract (SIZE-6a row -> SPAWN-12 row, COST-5a/6a rows, COST-4b/4c now both for every Tech Lead, new SPAWN-12 test), test_rules_wording, test_dev_rules_size, test_small_files_equivalence (IDs), test_squad_usage_hook (rewritten test).
- Three edits outside the Files line, approved by the Tech Lead (ANSWER 04): `test_sizes.py` drops "plan-owner" from the duty tuple; `test_sizes.py::present_roles` counts team-lead always present; `test_architect_handoff.py::test_size_text_stays_clean_for_an_absent_role` drops "Team Lead" from the absent names.
- `process.local.md` line 25 (Manager overlay) cites COST-5a: not touched, listed for the Manager.
- Results: test_windows_safe OK (14), test_utf8_helpers OK (14), test_instructions OK (16); test_rules_contract, test_rules_wording, test_dev_rules_size, test_squad_usage_hook, test_small_files_equivalence, test_sizes, test_architect_handoff: 88 tests OK. Full suite not run (Tech Lead's).
