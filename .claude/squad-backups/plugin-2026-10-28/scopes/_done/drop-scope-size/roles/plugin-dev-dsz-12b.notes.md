# plugin-dev-dsz-12b notes (ticket 12, continued from dsz-12)
Done: ticket 12 PASS from Tech, QAW, QAB on final sha 59e2741 (code c768b94). Nothing open.
Delivered: S4 inventory test (tests/test_old_language_inventory.py, per-file counts), AC29 test, AC21 `alternative:` lines in bin/squadupgrade.py (_other_l_role), raw qa-b\b needle, evidence at .scratch/drop-scope-size/issues/12-cutover-reject-old-language/evidence.md.
Gotchas: run tests from tests/ with PYTHONDONTWRITEBYTECODE=1 (test_squadinbox test_no_pyc fails if pycache exists or files share a process). No changelog v9 rows needed for 12.
