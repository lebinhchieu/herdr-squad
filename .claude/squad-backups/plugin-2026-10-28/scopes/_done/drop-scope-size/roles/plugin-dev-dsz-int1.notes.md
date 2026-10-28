# INT1 notes (Dev int1)
- Done: merged 03, 05, 09 into squad/plugin/drop-scope-size/plugin-dev-dsz-int1; both QA PASS on 8fa0aa0; evidence at 6389642.
- Only seam: tests/test_process_conversion.py accepts tombstoned IDs (SIZE-3).
- Gotchas: run unittests from tests/ (rulesview import); direct unittest leaves bin/__pycache__ which fails test_no_pyc: rm it and use PYTHONDONTWRITEBYTECODE=1 before run_suite. rtk blocks `find -exec`.
- Nothing open.
