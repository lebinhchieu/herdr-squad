# Evidence 19 integration of 05 + 07

## Behaviour
Base `board-dev-inbox-10` already held 05; `board-dev-tasks-9` (07) merged as a merge commit. Code commit 336abb2 touches only `bin/squadboard_inbox.py`, `bin/squadboard_tasks.py` and their two test files (plus the ticket file).
- T05.AC8 / T19.TA2: `squadboard_inbox` imports `squadboard_tasks` plainly and calls `ready_by_scope(sel)`. The `getattr`/`try` fallback is gone; only a real failure gives `unknown:ready_for_review`. Test `test_T19_wiring_real_ready_by_scope` has no stub: choice `questions`, `others` has `checkout` n=2 (1 ready branch + 1 permission prompt), no `ready_for_review` in `unknown`. The `sel["ready_for_review"]` hook stays for the older 05 tests.
- T19.TA3: `squadboard_tasks._ticket_folder` = same rule as `squadboard_list._tickets` (`tickets:` line, else `.scratch/<scope>/issues`, else unknown). It is a copy of the rule, so test `test_T19_same_folder_rule_as_list` asserts both find the same ticket set over every fixture scope. `find_tickets` is no longer used in `squadboard_tasks` (grep: 0 hits).
- T19.TA4: `questions`, `parked`, `alpha-ui` return `rows == []`, `unknown` has `tickets`, quality `approx`.
- T19.TA5 changed expectations (two, both in `test_squadboard_tasks.py`): with no `tickets:` line, or a line naming a missing folder, scope `checkout` now lists no tasks (before: fell back to the guess and listed them). This is the removed fallback the ticket asks for. No test deleted or skipped.
- Ran, all pass: `test_squadboard_tasks` (13), `test_squadboard_inbox` (11), `test_squadtickets` (6), `test_windows_safe`, `test_no_bare_bash`, `test_old_language_inventory`. `grep -rl 'squadboard_tasks\|squadboard_inbox' tests/` hits only the two edited files.
- Note: `test_squadtickets` has 6 tests here, not 17; unchanged by this task.
- Scratch dirs: none left by me (logs in /tmp/integ12-*.log, for the PO to clean).
