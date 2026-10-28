Status: ready-for-agent
Type: task
Task ID: 27
Ticket file: lives in `$SCOPE_DIR/tasks/`; first commit copies it to `.scratch/composed-process/issues/27-integration.md`.
Blocked by: 10, 11, 12, 13, 14, 21, 25, 26 (all passed)

# 27: Integration of process-fixes (C1)

**Done when one branch holds all eight passed branches, every `*.evidence/` folder has moved to `NN-…/`, the targeted tests pass, and the Tech Lead's `--tz` suite passes on its sha.**

## Base and merge order (from the Tech Lead's trial merges, `git merge-tree`)
Branch from **858f670** (ticket 21, passed branch `squad/plugin/process-fixes/plugin-dev-pf-3`, itself on 4901cab). `--no-ff` merges, in this order:
1. `plugin-dev-pf-1` @ 2f2e5a7 (10)
2. `plugin-dev-pf-2` @ d2a2d99 (12)
3. `plugin-dev-pf-4` @ adc56af (14)
4. `plugin-dev-pf-8` @ ab02cf0 (26; brings 11 @ 0e0a362 and 10)
5. `plugin-dev-pf-7` @ 3dd0a79 (25; brings 13 @ afdc264 and 10)
Steps 1-4 merge clean in trial. Step 5 has one conflict, `templates/squad/process/iterations.md`, ITER-12 paragraph: 11 (in step 4) rewrote it with the Manager notice and dropped "The cost hook never nudges you…"; 13 (step 5) kept that sentence and added blocks ITER-13..ITER-16. Resolve: **keep 11's ITER-12 text, drop the "never nudges" sentence, keep any other change 13 made to that paragraph, keep ITER-13..16 as 13 wrote them.** Then re-run `squad-process lint`.
Verify with `git merge-base --is-ancestor <sha> HEAD` for each of the eight code shas (10 2f2e5a7→0f1a68c, 11 3be9c32, 12 054bf37, 13 a6e06f0, 14 99796ce, 21 27df79d, 25 9905c0c, 26 57335d5) and quote the output.

## Evidence folders
The branches that predate 21 carry old-form `NN-….evidence/` folders (10, 11, 12, 13, 14, 25, 26). `git mv` each to `NN-…/` (pure rename). Then `find .scratch -name '*.evidence'` is empty and `git ls-files | grep '\.evidence/'` is empty; `squad-evidence check` on every ticket is not required (the passes were checked on the pre-move shas). Keep 21's list of intentional `.evidence` leftovers valid: do not touch those files.

## Checks (Developer runs only the files touched, never the full suite)
- `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_dev_rules_size test_squadcompose test_squad_evidence test_squad_close test_squadruntime test_squadprocess test_squad_ledger test_squad_manager_guard test_squad_path_guard test_hooks_json test_squad_usage test_processlint test_process_conversion test_process_citations test_templates test_instructions test_windows_safe` (drop any name that does not exist).
- `python3 bin/squad-process lint`. Composed Developer rules for every size/design/goal combination within the 5120 B cap (`test_dev_rules_size`); report the merged byte delta against 4901cab (expect about +6 B).
- Rule IDs: no duplicate across merged files (ITER-12..16, FILE-11, MRG-5, COST-13/14…); lint covers it.
- The composed output for a fixture scope without `qa-b` stays byte-identical to the 4901cab runtime for every role except where tickets 10-13, 25, 26 add rules (list the differing rule IDs in evidence).

## Evidence
`.scratch/composed-process/issues/27-integration/evidence.md` (`## Behaviour`: merge list with ancestor checks, the conflict resolution diff for ITER-12, the folder move list, test outputs). Hand in to the Tech Lead (suite owner) with the branch sha; the Tech Lead runs `--tz` and saves the receipt; QAs read it.

## Promotion
Not part of this task: `promote.md` is a later, separate task.
