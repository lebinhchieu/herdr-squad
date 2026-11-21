# 04 Process text B: cost, spawning, starting, sizes, files, promotion
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: templates/squad/process/cost.md, spawning.md, starting.md, sizes.md, files.md, promotion.md, iterations.md (ITER-3b), _removed.md (tombstones, own hunks); bin/squad-usage-hook; tests/test_rules_contract.py (COST/SIZE/SPAWN rows), test_dev_rules_size.py, test_squad_usage_hook.py, test_small_files_equivalence.py (IDs in these files), test_rules_wording.py (its IDs); tests/test_sizes.py and tests/test_architect_handoff.py: only the three tests a 04 change turns red (test_every_duty_has_a_rule_per_acting_role_in_sizes_md, test_no_rule_of_the_two_files_acts_on_an_absent_role_..., test_size_text_stays_clean_for_an_absent_role), minimal edits (ruling 2026-11-21)
Depends: - (group A, parallel with 01, 03, 05, 06; the plan had `02`, which now comes after: SQ-1, see `tech-lead-plan.md`). Goal: `../iterations/1.md`; brief `../scope.md`.
Evidence: .scratch/tl-always/issues/04-process-text-b/evidence.md

## What and why
One variant each. Manager subagents default sonnet high, model/effort picked per task (gather/explore stay sonnet high, judgment may use opus or higher effort), forks allowed. Parallel with 03: disjoint files.

## Design notes (Tech Lead)
Same method as 03 on the other six files; the old engine still accepts `plan-owner`, so this runs green before 02. Read `../scope.md` and ADR 0006 first. Rules removed (tombstone in `_removed.md` in its existing order, `replaced_by` the Team-Lead twin): COST-5a, COST-6a, COST-10a, COST-13a, COST-14a, FILE-5a, ITER-3b, PROMO-5b, SIZE-6a, SIZE-6c, SPAWN-2a, SPAWN-5a, SPAWN-8a, SPAWN-10a, START-2a. Rules with `plan-owner = team-lead` lose the condition and keep their ID; SIZE-17b loses `team-lead = yes`. The FILE-7 table row `tasks/<id>.md` says "Team Lead (from the Manager's plan)", no `plan-owner` of `duties:`. Every "plan owner" in these files becomes Team Lead or Manager by what the sentence does (as in 03).

New rule (the only new text): in spawning.md, a Manager rule `SPAWN-12` (SPAWN-11 exists; confirm 12 is free with `squad-process rule SPAWN-12`): subagents the Manager spawns default to `model: sonnet`, `effort: high` (Agent tool parameters, not the Manager's model); before each spawn the Manager picks model and effort for the task: gathering and exploring stay sonnet high, a judgment call may use opus or a higher effort; a fork is allowed when it helps and runs on the Manager's model, so the Manager chooses it on purpose. `roles: manager`. One rule, limits in must/never/at most (ADR 0006).

`bin/squad-usage-hook` (reads `team:` for `team-lead`, line 34-40): the Developer text always names "the Team Lead" and `COST-5`; delete the `team` parse and the COST-5a branch. `tests/test_squad_usage_hook.py::test_developer_text_names_the_plan_owner_from_scope_md` is rewritten: same text for a scope.md with and without `team-lead` and with no scope.md.

Technical AC:
- AC1 `squad-process lint` is clean; every removed ID has a tombstone with `replaced_by`; `grep -n "plan-owner\|team-lead = " templates/squad/process/{cost,spawning,starting,sizes,files,promotion,iterations}.md` is empty.
- AC2 No citation of a removed ID outside `_removed.md`, the changelog and `hooks/squads/fixtures/`: `grep -rn "COST-5a\|COST-6a\|COST-10a\|COST-13a\|COST-14a\|FILE-5a\|ITER-3b\|PROMO-5b\|SIZE-6a\|SIZE-6c\|SPAWN-2a\|SPAWN-5a\|SPAWN-8a\|SPAWN-10a\|START-2a" bin hooks agents skills tests templates` hits only those. (`.claude/squads/plugin/process.local.md` line 25 cites COST-5a: the Manager's overlay, not this task; the Developer lists it in `## Behaviour`.)
- AC3 The new rule composes for `manager` only (`squad-process compose manager` shows it; `compose dev` does not), says sonnet high as default, per-task choice, forks allowed; one test row in test_rules_contract.py (`acts("SPAWN-12", ...) == ("manager",)`) and one assertion on the three phrases in the composed Manager text.
- AC4 The Team Lead's composed text keeps spawn/retire Developers only, cap, health checks (SPAWN-5b etc.), and has no rule that lets it reorder the plan.
- AC5 `bin/squad-usage-hook`: for each of three scope.md shapes (team lists `team-lead`, does not, absent) the Developer's stderr text names "the Team Lead" and `[COST-5]` and is identical across the shapes; the existing "other roles unchanged" test passes untouched.
- AC6 SQ-10: the diff edits `bin/` and text a `bin/` tool prints: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`; quote the result.
- AC7 `tests/test_dev_rules_size.py` passes (Developer 5 KiB cap, all teams); its COST-5a/MSG-4a/MSG-11a/SPAWN-5a references updated.
- AC8 Targeted tests: touched files plus `grep -rl "<each retitled or removed ID>" tests/` hits (goldens included). No test newly skipped; the full suite is the Tech Lead's.
Compatibility (LC-12): as 03; the Developer-facing hook text changes wording only. Rollback = revert the merge.

## Evidence
`evidence.md` next to the ticket (path in Evidence: line, Tech Lead).
