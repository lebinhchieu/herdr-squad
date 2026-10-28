# 03 Fix the baseline suite failures
Status: ready-for-agent
Type: task
Blocked by: 01, 02

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; QA whitebox runs the full suite once on the final sha (`python3 tests/run_suite.py --receipt <dir> --if-changed <base>`). Ticket + evidence path: `.scratch/squad-close-keeps-manager/issues/03-fix-baseline-suite-failures.md` and `.../03-fix-baseline-suite-failures/evidence.md` (commit this task file there as the ticket). Base: branch `squad/plugin/squad-close/plugin-dev-squad-close-1` at edf5d87. Context: `$SCOPE_DIR/evidence/suite/base-vs-final.md`, `$SCOPE_DIR/tasks/03-suite-baseline-failures.md`.

## Business AC
1. `python3 tests/run_suite.py --tz` passes with 0 failures on the final sha (the PO asked for these 55 failures to be fixed in this scope).
2. No behaviour of 01/02 changes; no test is deleted or weakened to pass: each fix is either a code/fixture correction or a golden update with the reason stated in evidence.

## Known failures (base 5adfc45 and 6ebcfbd, same)
- `tests/test_qab_optional.py` `NoLineUnchanged.test_every_role_matches_the_4901cab_golden`: 54 subtests (role/size/design). Golden: `tests/fixtures/qab/golden.json`.
- `tests/test_squadinbox.py` `NoBytecodeTest.test_no_pyc`: stray `bin/__pycache__/*.pyc` in the worktree.

## Touched files (LC-9b)
Likely `tests/fixtures/qab/golden.json`, `tests/test_qab_optional.py`, `tests/test_squadinbox.py` and whichever bin/test file leaves `bin/__pycache__`. Dev finds the cause of each first and sends `ASK 03:` to the Manager with the touched-file list before editing anything else. Note `.pyc` may come from a test run without `-B`/`PYTHONDONTWRITEBYTECODE`: if so, fix the source of the bytecode, not only the cleanup.

## Technical AC (QA whitebox; agree or counter in this file)
T1. Root cause of each failure stated in evidence with proof (command + output), not a guess.
T2. Golden updated only if the rules/templates text legitimately changed since 4901cab (merged composed-process work); evidence shows the diff class and that every changed role line is intended. Otherwise the code is fixed.
T3. `.pyc` fix keeps `test_no_pyc` meaningful (no weakening of the assertion).
T4. Full suite with `--tz` green; receipt in `$SCOPE_DIR/evidence/suite/`.
