| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | tests/test_squadtickets.py test_watchdog_blind_state_line_is_read_when_no_status (State: ready -> ready; State: handed in (..) -> handed in; State past line 12 -> ''); `cd tests; python3 -m unittest -q test_squadtickets` OK | | |
| AC2 | same test: "State: ready\nStatus: done" and "Status: done\nState: ready" -> done | | |
| AC3 | `cd tests; python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask` OK (grep -rl squadtickets tests/ hits) | | |
| AC4 | `grep -n 'Status:' CONTEXT.md` hits only line 54 and 220, no definition of the ticket line; no edit | | |
