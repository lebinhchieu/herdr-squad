# 04 Process text B: evidence
sha: 9710ecf
## Review

AC trace (`cd tests; python3 -m unittest <file>` for tests, repo root for greps):

- AC1 | `squad-process lint` exit 0; tombstones in `_removed.md` (15 IDs, `replaced_by` each); grep `plan-owner\|team-lead = ` over the seven files: empty | run from repo root
- AC2 | grep of the 15 removed IDs over bin hooks agents skills tests templates: hits only `_removed.md`, `changelog.md`, fixtures, and two `assertNotIn("## SPAWN-5a")` lines plus a historical byte comment in tests | grep in `## Behaviour`
- AC3 | `tests/test_rules_contract.py` (row `acts("SPAWN-12","S") == ("manager",)`, `test_manager_subagent_default_rule`: three phrases, absent from dev and team-lead) | `python3 -m unittest test_rules_contract`
- AC4 | `test_rules_contract.py::test_spawning_cost_and_safety_follow_the_team`, `test_team_lead_spawns_and_retires_dev_only` (asserts SIZE-6b has no "owns the plan"/"task order") | same
- AC4b | grep `take over the plan|owns the plan|task order|plan owner|Reorder` over the seven files: one hit, sizes.md SIZE-6b ("never reorders the plan") | repo root
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

- Return after FAIL 37c625b (AC4): SIZE-6b says the Team Lead assigns per the Manager's plan and never reorders, heading "Assignment, Team Lead"; SIZE-17b reads the Manager's plan and `## Handover`; COST-4b heading "Plan and AC written, respawn"; one composed-text assertion. Fixed in bc3e3d9; 132 tests OK, lint exit 0.

## QA whitebox

### QA whitebox 04, sha 37c625b

Ran `cd tests && python3 -m unittest test_sizes test_architect_handoff test_rules_contract test_rules_wording test_dev_rules_size test_squad_usage_hook test_small_files_equivalence test_windows_safe test_utf8_helpers test_instructions` -> 132 OK. `squad-process lint` exit 0. AC1 grep empty. AC2 only 2 `assertNotIn("## SPAWN-5a")` lines + one historical comment in test_dev_rules_size.py:120 (pre-existing) remain. AC3, AC5, AC6, AC7 verified (SPAWN-12 manager only; hook text identical across scope.md shapes).

#### FAIL: AC4 (Team Lead text has no rule that lets it reorder the plan)
1. `templates/squad/process/sizes.md:55` SIZE-6b "Plan owner, Team Lead": "The Team Lead owns the plan, task order and assignment, in the same plan file and format the Manager uses." It composes for team-lead at S, M, L (checked with `test_rules_contract.composed("team-lead", size)`). It gives the Team Lead the plan and task order, against scope.md (Manager owns the plan, Team Lead "never reorders it") and AC4. The ticket also says every "plan owner" becomes Team Lead or Manager by what the sentence does. Pass: say the Team Lead assigns per the Manager's plan, spawns/retires Developers, tracks status, and never reorders; Manager owns the plan and order; drop "Plan owner" from the heading.
2. `sizes.md:166` SIZE-17b: "take over the existing plan file from the Manager": same conflict (the Team Lead takes over the plan). Pass: read the plan and its `## Handover` section; the Manager still owns the plan.
3. `cost.md:22` COST-4b heading "Plan owners respawn": heading still names the removed concept (text "Respawn once your plan and AC are in files" is fine for the Team Lead). Rename in the same fix (style, same return).
The tests that cover AC4 (`test_team_lead_spawns_and_retires_dev_only`) do not assert the absence of an ownership/reorder rule, so they pass despite this. Add one assertion on the composed Team Lead text.

#### Follow-ups
- `lifecycle.md:218` "Reorder when gaps appear" is task 03's file; confirm 03 handles it.
- `.claude/squads/plugin/process.local.md` line 25 cites COST-5a (Manager overlay), as the ticket says.

#### Re-check bc3e3d9 (diff 37c625b..bc3e3d9)
AC4 findings fixed: SIZE-6b and SIZE-17b reworded, COST-4b heading renamed, AC4 assertion added. 132 tests OK, lint 0. PASS.
Follow-up: who.md still names the old headings "Plan owner, Team Lead" / "Plan owners respawn" and WHO-1e gives the Team Lead plan/order (task 03's file; Dev noted it).

## QA blackbox

### QA blackbox 04 Process text B (sha bc3e3d9)

Live: `squad-process lint/rule/compose` from the 04 worktree against a scratch scope (team: team-lead, tech-lead, qa-white, qa-black; qa full). Compose rc=0 for manager, dev, team-lead.

| AC | how | what I saw | result |
|---|---|---|---|
| AC1 | live | `squad-process lint` exit 0; grep `plan-owner\|team-lead = ` over the 7 files empty; all 15 removed IDs answer "no such rule" and have a tombstone in `_removed.md` (31 `replaced_by` lines) | pass |
| AC2 | live | grep of the 15 IDs hits only `_removed.md`, changelog, fixtures, two `assertNotIn("## SPAWN-5a")` lines and one historical byte comment in tests (disclosed by the Developer) | pass |
| AC3 | live | `compose manager` has `## SPAWN-12 Subagent model and effort` (sonnet, effort high default; pick per spawn; gather/explore stay sonnet high; judgment may use opus; fork allowed, runs on Manager's model); `compose dev` and `compose team-lead` have none; `who SPAWN-12` not needed | pass |
| AC4 | live | Team Lead text keeps SPAWN-5b, SPAWN-8b, SPAWN-9, COST-13b, COST-14b; SIZE-6b "assigns tickets per the Manager's plan ... never reorders the plan"; SIZE-17b "the Manager keeps the plan" | pass |
| AC5 | not driven live | I fed `bin/squad-usage-hook` a synthetic Stop input for three scope.md shapes; it stayed silent (my synthetic transcript did not reach its trigger). Covered by `test_squad_usage_hook` (OK) in the targeted run | covered by test |
| AC6-AC8 | test run | `test_rules_contract test_rules_wording test_dev_rules_size test_squad_usage_hook test_small_files_equivalence test_sizes test_architect_handoff test_windows_safe test_utf8_helpers test_instructions`: Ran 132, OK | pass |

Follow-ups (not 04's, SQ-4):
- `lifecycle.md` LC-17 (task 03's file) still tells the Team Lead "Reorder when gaps appear", and LC-20b, REV-14a, LC-6c still say "plan owner". Contradicts "Team Lead never reorders the plan"; for 03 or the Manager.
- `process.local.md` line 25 cites COST-5a (Manager overlay; the Developer already listed it).
