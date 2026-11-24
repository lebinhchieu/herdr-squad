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

## QA whitebox

### 10 QA whitebox, sha b35c5d0: PASS
Worktree w07 (detached). Tech AC T1-T9 from the ticket.
- T1: nine moved rules (MRG-2..5, CLOSE-2/4/5, ITER-6c) all `roles: manager`; tools that print them are in evidence.md. OK.
- T2: contract test (6 team shapes, every role, MUST_ATTACH) passes. Developer/QA/Tech Lead compose unchanged except the index (QA/Dev lines equal before/after).
- T3: Manager index 19 lines, Tech Lead 19 lines (limit 40). Live compose here: Manager 565 lines, Tech Lead 277, Dev 118; matches the evidence table. No MRG-2..5/CLOSE-2/4/5 in the Manager's attached text; they are in the index.
- T4: `squad-process phase close --home <scope>` prints CLOSE-2, CLOSE-5 (CLOSE-4 is goal-only); `phase nope` rc 2.
- T5: merge-check prints rules before VERDICT, pointer line on reader failure; close dry-run prints close block; token-coach spawn prints coach block on stderr (test exists).
- T6: lint rc 0; `upgrade --check` rc 0 ("nothing needs a decision"); bad phase value lint test exists.
- T8: 10 test modules, 346 run, 2 fail: test_a_failed_agent_start_leaves_the_old_overrides_file and test_lean_without_a_lean_json_defaults_to_no_mcp_servers. Both fail on base without 10 (see evidence/06/qa-w.md). Not caused by 10.
- Edits outside the Touched list (test_rules_wording:222, test_squad_close) are small and explained in evidence.md. Accepted.
Follow-ups: (1) For a home pinned to an older runtime than the running plugin, `squad-process phase` refuses and squad-close prints nothing (2>/dev/null); the live fable-advisor scope is pinned to 0.7.5, so a run from the main plugin shows nothing. A close run from the pinned runtime uses its own rules, so this is consistent. (2) The index has no titles by design; CORE-6 still finds every rule.

## QA blackbox

### 10 qa-b: smaller attached rules (sha b35c5d0)
Live. `squad-process phase/compose` from the dev-c worktree on the real scope home (read-only, `--out` to a scratch dir); tools run from a scratch squad (mktemp, removed) whose `_runtime/<ver>-<sha>` is a copy of b35c5d0 so pin == running plugin. Before = main 9b05952 compose of this scope's team.

| AC | What I did | What I saw | Result |
|---|---|---|---|
| 1 merge rules | `squad-merge-check <branch>` in scratch | `## MRG-2..MRG-5` printed, then `VERDICT: refuse...` as the last line, rc 1 | pass |
| 1 close rules | `squad-close p --scope s --dry-run` from the pinned runtime | `## CLOSE-2`, `## CLOSE-5` printed first, then the normal dry-run sections, rc 0 | pass |
| 1 coach rules | `squad-spawn token-coach c1 --scope s` (fake herdr, scratch) vs `qa-whitebox` | coach: `## ITER-6c` on stderr; qa-whitebox: nothing | pass |
| 1 phase cmd | `squad-process phase merge/close/coach`, `phase bogus` | exact rule sets; bogus rc 2 with message | pass |
| 2 index | compose manager / tech-lead | Manager index 212 -> 19 lines, TL 24 lines; `squad-process rule <ID>` for all 496 index IDs: no failure | pass |
| 3 no rule lost | `## ID` heading sets before/after, 5 roles | TL, QAW, QAB, Dev: identical. Manager: lost only MRG-2..5, CLOSE-2, CLOSE-5, ITER-6c (all printed by tools); gained COST-8b, ITER-18, LC-6c from other tickets in the branch base. MRG-1, CLOSE-1, ITER-6 stay | pass |
| 4 numbers | compose before/after | Manager 769 -> 565 lines (56078 -> 47034 B); TL 529 -> 277 (29633 -> 19211 B); QAW/QAB/Dev unchanged; matches the dev table within base differences | pass |

#### Follow-ups (not AC breaks)
- Run from a plugin version that differs from the scope's pin (e.g. a dev worktree), `squad-close` prints no close rules (`|| true` hides the version-mismatch message). Same-version runs are fine.
- On a scope with an empty retro, `squad-close --dry-run` refuses (ITER-16) before it prints the close rules.
- The coach spawn was run with a stub herdr; a dry-run of a coach spawn does not print the rules, only a real spawn does.
