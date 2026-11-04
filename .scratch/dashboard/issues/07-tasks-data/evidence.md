# Evidence 07 tasks data

## Behaviour
Reader `bin/squadboard_tasks.py` (route `/api/tasks`), run on the board fixture (squad `fix`, scope `checkout`, clock = fixture REF). Tests: `tests/test_squadboard_tasks.py` (11), `tests/test_squadtickets.py` (6), all pass.
- T07.AC1/AC2/AC3: stages read `todo, in progress, returned, blocked, ready for review, sha changed after PASS, merged, done`; task 01 owner `unassigned`; task 03 `returns` 3 and `last_fail_line` "reason 3 first line (newest)". The FAIL text is `FAIL 03: finding` then a reason line; a one-word header gives the next line.
- T07.AC4: task 05 reads `checking, 1 of 2 PASS, waiting on QA blackbox, 40 min`. Checkers come from the roster (QA roles, not retired).
- T07.AC5/AC6: only 06 is ready (`ready_for_review: [{task, branch, tip}]`); 07 (tip moved) and 08 (merged) are not. Tip is found by branch `squad/<squad>/<scope>/<handin agent>`, not parsed from the branch text.
- T07.AC7/AC8: `REV-8` gives no row; the `tickets:` line picks the folder (a missing folder falls back and reports `unknown:tickets`); with no line tasks still list.
- T07.AC9: goal choice adds `scope` to each row; scope choice has none.
- T07.AC10: `detail=<id>` returns agents and steps in time order with epoch and ISO time; only the FAIL reason line is free text (canary test).
- T07.AC11: after 01:00, task 03 has 4 new (HANDIN, FAIL, HANDIN, FAIL); no `since` gives 0. Copies within 120 s count once.
- DECISION 07 (+ FAIL F1): `ready_by_scope(sel) -> {scope: n}` is squad-wide whatever the choice (scope, goal): one key per open scope. Test `test_ready_by_scope` asks from scope checkout, scope questions and goal alpha and gets `checkout: 1` each time.
- Broken sources (no messages, roster, git, tickets folder): no exception, `unknown:<source>`.
- Reused: `squadledger.build/read_records/key`, `squadtickets`, `squadboard_git`, `squadboard_time`, `squadreport_tasks.REASON_CUT/DEDUPE_S/iso`. No private helper imported; `squadledger.py` not edited.
- Also ran: test_windows_safe, test_no_bare_bash, test_old_language_inventory, test_squadreport_tasks, test_squadboard_server: pass. `grep -rl 'squadtickets\|squadboard_tasks' tests/` hits only the two files above.
