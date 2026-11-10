## Behaviour

New `phase:` attribute (`merge | close | coach`; lint error otherwise) on nine Manager-only rules. They leave the Manager's attached rules and `rules:` line and print when their phase starts. The index is now a heading, one pointer line, then the unattached IDs as words wrapped at 100 columns.

**Before and after** (`squad-process compose`, base = 7b89c09, the branch after merging 04-06; scope team tech-lead, qa-white, qa-black; goal = a goal home). Token figures are estimates (bytes / 4), not `squad-usage` readings.

| Role | Lines before | Lines after | Bytes before | Bytes after | Est. tokens saved |
|---|---|---|---|---|---|
| Manager | 778 | 565 | 57068 | 46977 | about 2500 |
| Tech Lead | 532 | 277 | 29680 | 19156 | about 2600 |
| QA whitebox | 216 | 216 | 14016 | 14016 | 0 |
| QA blackbox | 177 | 177 | 11481 | 11481 | 0 |
| Developer | 118 | 118 | 8210 | 8210 | 0 |
| Goal Manager | 902 | 728 | 68610 | 60231 | about 2100 |

Index of the Manager and Tech Lead: 19 lines (was 213 and 280 lines in the design note's base measure).

**Moved rules (T1).** Each has `roles: manager` in its file (`squad-process who` prints nothing for these: none has a team or duty key in `when:`; CLOSE-4 has `goal = yes`). The tool that prints it is in the last column.

| Rule | Phase | Printed by |
|---|---|---|
| MRG-2, MRG-3, MRG-4, MRG-5 | merge | `squad-merge-check`, before `VERDICT:` |
| CLOSE-2, CLOSE-4, CLOSE-5 | close | `squad-close` (scope, goal, squad, `--dry-run`), at start |
| ITER-6c | coach | `squad-spawn token-coach`, on stderr after the JSON line |

Stay attached: MRG-1 (new sentence: run `squad-merge-check`), CLOSE-1 (new words: `--dry-run` first), CLOSE-3a/3b/3c, ITER-6/6a/6b, SQ-7/SQ-7b (untouched).

**Tool outputs.** `squad-process phase coach --home <scope>` prints `## ITER-6c Wait for the Token Coach` plus its body. `squad-process phase nope` exits 2 (`phase: unknown phase 'nope' (one of merge, close, coach)`). A broken rules reader in `squad-merge-check` prints `merge rules: squad-process phase merge --home <dir>` and the same verdict and exit code. When a home's pin differs from the running plugin version, `phase` refuses as `compose` does (`pass --plugin-root`); the tools then print nothing or the pointer line and carry on.

**Test changes outside the list.** `tests/test_rules_wording.py:222` read MRG-4 from the Manager's composed text; it now reads it with `squad-process rule MRG-4` (one line). `tests/test_squad_close.py` dry-run test also asserts `## CLOSE-2`. `squad-close` runs the phase print only when `bin/squad-process` exists, so a test stub bin dir is unaffected.

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 phase rules print at phase start | `PhaseTest.test_phase_prints_exactly...`; merge-check, close dry-run, spawn coach tests | `cd tests && PYTHONPATH=. python3 -m unittest test_squadcompose test_squad_merge_check test_squad_close test_squad_spawn` |
| AC2 index shrinks, CORE-6 finds every rule | `PhaseTest.test_index_is_short...` (loops `find_rule` over all) | same |
| AC3 no role loses a needed rule | `PhaseContractTest` (6 shapes, every role, MUST_ATTACH) | `... unittest test_rules_contract` |
| AC4 before/after lines | table above | `squad-process compose` |
| T6 lint | `test_a_bad_phase_value_is_a_lint_error`; `squad-process lint` exit 0; `upgrade --check` exit 0 | `... unittest test_squadrules` |
| T9 golden | `manager-goal.rules.md` diff: index only | `test_squadcompose` |

Targeted runs, all OK: test_squadcompose, test_squadrules, test_rules_contract, test_squad_merge_check, test_squad_close, test_architect_handoff, test_small_files_equivalence, test_squadruntime, test_rules_wording, test_sizes, test_run_suite, test_dev_rules_size, test_squadupgrade. test_squad_spawn: 1 failure, `test_a_failed_agent_start_leaves_the_old_overrides_file`, which also fails on the base (Manager confirmed). No full suite.
