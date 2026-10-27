# Evidence: INT1 integration of 03 + 05 + 09
base 6ec3a75 (02 PASS); merged in order: 03 (0f4305d), 05 (8b350e8), 09 (e7a7910).

## Behaviour
- Three merges, no textual conflicts; changelog v9 (`skills/squad-process-update/changelog.md`) is one block with the 05 appends kept, no conflict markers.
- `tests/test_squad_migrate.py` + `tests/test_instructions.py` against the merged `templates/scope/scope.md`: 50 tests OK (the 2 ToPerScopeTest reds from 09 alone are green).
- One seam fixed: `tests/test_process_conversion.py` `test_every_target_is_a_rule_or_a_closed_drop_form` failed because the historic conversion mapping row `process.md:103 -> SIZE-3` names a rule 05 tombstoned. The test now accepts IDs tombstoned in `_removed.md` (`## ID (removed in vN)`). No other file touched.
- Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed 991cab6`: 1677 tests, OK, exit 0 (receipt `evidence/INT1/suite-default.txt`). First two runs failed only on test_process_conversion (the seam) and test_squadinbox `test_no_pyc` (stale `bin/__pycache__` from my own direct unittest runs, removed; not a code defect).
