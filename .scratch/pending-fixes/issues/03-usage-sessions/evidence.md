# Evidence 03: squad-usage sessions

## Review
AC trace (QA whitebox T-list; ticket AC1/AC2):
- AC1 / T1 | tests/test_squad_usage.py::test_sessions_column_and_flag_list_each_session_and_agree_with_the_row, test_table_totals | `python3 tests/test_squad_usage.py`
- AC2 / T2, T5 | same test (2 sessions + one empty transcript, no crash; oldest first) | same
- T3 | same test: turns sum = row turns; newest session's peak = row peak ctx | same
- T4 | `python3 bin/squad-usage --sessions plugin-mgr-pending-fixes` (below)
- T6 | `python3 tests/test_squad_usage.py` 27 tests OK; hits: test_squad_usage_hook, test_squad_respawn OK
- SQ-10 | test_windows_safe, test_utf8_helpers, test_instructions OK (14, 14, 16 tests)

## Behaviour
`sessions` is the last column of the table (existing columns and order unchanged). `squad-usage --sessions NAME` prints one line per session, oldest last turn first: peak ctx, turns, last turn. One session prints one line; no transcript prints `NAME: no transcript`.

Live, read-only, this squad:

    $ squad-usage --sessions plugin-mgr-pending-fixes
    session  peak ctx  turns  last turn
    1        85k       28     2026-11-21 14:08
    2        74k       15     2026-11-21 14:09
    3        80k       34     2026-11-21 14:14

Row of the same agent: turns 77 (= 28+15+34), peak ctx 80k (= newest session), sessions 3.

Deviation from T3: the row's `peak ctx` stays the newest session's peak (unchanged behaviour, tests and the 100k/150k checks read it). So the invariant is: turns sum = row turns, last session's peak = row peak ctx; the max over sessions is not forced into the row.
