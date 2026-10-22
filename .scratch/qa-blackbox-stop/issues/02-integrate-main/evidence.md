# 02 evidence

## Behaviour
- AC1: `git merge main` (769e5af, contains b7c5838) into the 01 branch; only conflict `tests/fixtures/qab/golden.json`. Took main's file, regenerated every hash from the merged tree with `test_qab_optional.compose`+`normalise`: exactly the 18 dev/qa-whitebox/qa-blackbox rows differ from main's; ba/designer/manager/team-lead/tech-lead/token-coach unchanged. Merge commit a9b046c.
- AC2: `git diff main HEAD -- templates` shows SAFE-11 line = task 01's; `squad-process lint`: ok.
- AC3: greps of `tests/` for SAFE-11, "Scratch directories", safety.md, golden.json, test_dev_rules_size, test_process_conversion: hits are all inside the full suite (AC4).
- AC4: `run_suite.py --tz`: Ran 1486 tests, OK; receipt `evidence/suite-tz.txt` = `sha a9b046c... clean=yes`. First run failed `test_squadinbox.test_no_pyc` (my own regen script left `bin/__pycache__`); removed it, reran whole suite with `-B`, green.
- AC5: `git merge-tree --write-tree main HEAD` -> tree 1af8c2ec..., rc=0, no conflict.

## Review
Fresh sonnet review of `main..HEAD`: no problems. Confirmed 54 golden keys, 18 differ, nothing from main lost, SAFE-11/changelog/pin consistent; reran 4 test files green.
