Status: ready-for-agent
Type: task
Task ID: 33
Touches: `tests/fixtures/qab/golden.json`, `.scratch/composed-process/issues/33-qab-golden-refresh.md` (this ticket), `.scratch/composed-process/issues/33-qab-golden-refresh/evidence.md`
Does not touch: any rule file, `bin/`, `templates/`, other tests, docs.
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_qab_optional test_sizes test_dev_rules_size`
Blocked by: 16 (passed). Base: `squad/plugin/integrate-promote/plugin-dev-ip-3` @ 88f5834.

# 33: Refresh the qab golden after ticket 32

**Done when `test_qab_optional` passes on the integration branch with a golden that matches the composed rules of ticket 32.**

## Why
The full suite `--tz` on 88f5834 failed 52 subtests of `test_qab_optional.NoLineUnchanged.test_every_role_matches_the_4901cab_golden`: ticket 32 changed REV-22, SIZE-2, SIZE-22 (so every role's composed output changed) and ran only its targeted tests, so the golden hashes were not regenerated. Tickets 20, 29, 30 each regenerated `golden.json` the same way. Receipt: `scopes/integrate-promote/evidence/suite-default.txt`. The other two failures of that run were not code: `test_no_pyc` (my own ad hoc `squad-process lint` wrote `bin/__pycache__`, removed) and `test_ca_autoswitch` age 899 (a load flake; passes alone, twice).

## What
1. Copy this file to `.scratch/composed-process/issues/33-qab-golden-refresh.md` (first commit).
2. Regenerate `golden.json`: for each of its 54 keys `role/size/design`, `sha256(normalise(compose(role, size, None, design).stdout))`, using the `compose` and `normalise` functions of `tests/test_qab_optional.py` (import them with `PYTHONDONTWRITEBYTECODE=1 python3 -I`, run from `tests/`). Keep the key set, order and JSON format of the file unchanged (diff shows only changed hash values).
3. Evidence (`evidence` skill): the test run, and `git diff --stat` showing only `golden.json`.

## Technical AC
1. `git diff 88f5834..HEAD --stat` lists only `golden.json`, this ticket and its evidence.
2. `git diff` of `golden.json` changes only hash values; the 54 keys are unchanged.
3. The Harness passes (counts in the evidence). `bin/squad-process lint` exit 0. Run Python with `PYTHONDONTWRITEBYTECODE=1` so no `bin/__pycache__` is left.
4. No full suite by the Developer; the Tech Lead runs it once more on the final sha.
5. The golden changes only because of REV-22/SIZE-2/SIZE-22: state in the evidence that you diffed one role's composed output between 3dcc7b2's parent 853b0a4 and HEAD and the difference is those rules only (`git diff 853b0a4 HEAD -- templates/squad/process/` shows only review.md and sizes.md).

## Comments
