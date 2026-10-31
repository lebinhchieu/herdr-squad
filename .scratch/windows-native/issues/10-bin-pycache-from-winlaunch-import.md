Status: needs-triage

# 10 tests/winlaunch.py import writes bin/__pycache__, so test_squadinbox.NoBytecodeTest.test_no_pyc fails after any winlaunch-importing test

Cause: `winlaunch` does `sys.path.insert(0, bin)` and `import squadio`; unless `sys.dont_write_bytecode` is set, Python writes `bin/__pycache__/squadio*.pyc`. `test_squadinbox.test_no_pyc` (AC15) asserts `bin` has no `*.pyc`/`__pycache__`. Seen on Windows after other test files ran (rm -rf bin/__pycache__ then the test passes alone); on Linux a whole-suite run in one process has the same ordering risk.
Fix direction (winlaunch.py is 03a's file, Tech Lead decides): set `sys.dont_write_bytecode = True` around the squadio import.

## Comments
