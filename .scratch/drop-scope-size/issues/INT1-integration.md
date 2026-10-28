# INT1 Wave 2 integration

Status: ready-for-agent
Type: task

## What
Integration per GOAL-6b: merge tickets 03 (squad/plugin/drop-scope-size/plugin-dev-dsz-3), 05 (...-dsz-5), 09 (...-dsz-9) onto base 6ec3a75. Resolve changelog v9 append conflicts (keep all).

## AC
- tests/test_squad_migrate.py and tests/test_instructions.py green on the real merged templates/scope/scope.md (Tech DECISION 03, 09).
- Full suite `python3 tests/run_suite.py --receipt <dir> --if-changed 991cab6` green; Tech Lead runs it on the final sha.
- Only integration seams fixed; no new features.

## Comments
Written at Tech Lead's ASK INT1 so `squad-evidence check` finds the evidence folder.
