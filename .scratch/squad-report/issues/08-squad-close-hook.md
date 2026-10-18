Status: ready-for-agent
Type: task
Task ID: 08
Touches: `bin/squad-close`, `tests/test_squad_close.py`
Does not touch: any `squadreport*`, `bin/squad-report` (a stub of it is built inside the test)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_close test_windows_safe`. The test copies `bin/` into a stub plugin dir (like its existing tests) with a stub `squad-report` that records its argv and can be made to fail or hang.
Blocked by: 04 (goal form needs 06 only at integration)
Parallel with: 05, 06, 07, 09

# 08: Report step in `squad-close`

**Done when closing a scope or goal builds its report first and a report failure never changes the close.** Business S6 (AC6.1-6.4); spec → "squad-close hook".

## What
In `bin/squad-close`, for `--scope` and `--goal` and not `--dry-run`, before the agent retire step and before the folder move:
`python3 "$bin/squad-report" "$name" --final --quiet --deadline 60 || echo "warning: report not generated (squad-report exited $?)" >&2` and continue. Nothing else in the script changes (output order, exit code, effects). `python3` and no `timeout`/`fcntl` (ADR 0011; Git Bash). The report folder travels into `_done/` with the scope.

## Technical AC
1. Scope close: the stub is called once with `<scope> --final --quiet --deadline 60` **before** any retire/move (the stub records the existence of the scope folder and live roster at call time); afterwards the folder is in `_done/` (AC6.1). Goal close: called with the goal name (AC6.2).
2. Stub exits non-zero or prints junk: close prints exactly one `warning: report not generated (squad-report exited N)` on stderr and its exit code, stdout and effects equal a close with no hook (compare against the existing close tests' expected values) (AC6.3).
3. `--dry-run`: the stub is never called and nothing is written (AC6.4).
4. A hung stub (sleeps past the deadline) is not killed by `squad-close`; the closing script waits only as long as `--deadline` makes the real tool exit 5 (the stub test asserts the arguments, the real deadline is 04 AC5).
5. Existing `test_squad_close.py` cases still pass unchanged; the new cases are additions.
6. Primary behaviour only (qa: light).
