## Behaviour
- `status_of("State: ready (no Developer yet)")` -> `ready`; `State: handed in (5bc3126); QA next` -> `handed in`; both lines -> the `Status:` value.
- Run from `tests/`: `python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask test_windows_safe test_utf8_helpers test_instructions` -> Ran 98 tests, OK. [SQ-10] included.

## Review
AC trace (checks table: see `checks.md`)
- AC1 | tests/test_squadtickets.py::test_watchdog_blind_state_line_is_read_when_no_status | `cd tests; python3 -m unittest -q test_squadtickets`
- AC2 | same test, both-line cases | same
- AC3 | test_squadtickets, test_squadboard_tasks, test_squadtask | `python3 -m unittest -q <module>` from tests/
- AC4 | none needed, CONTEXT.md has no `Status:` definition | `grep -n 'Status:' CONTEXT.md`
