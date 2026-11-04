# 03 evidence

## Behaviour
Design notes (state is in memory, not a file): `TICKNO`, `BACKOFF` and `INFLIGHT` are module variables of `bin/cautoswitch`. A restart of cautoswitch forgets them, so every off-default pane is tried once at once; that is safe because `pending()` (from cswitch.log) still guards a switch already running.
- AC1: `SHORT_WAIT = 60` (was 900). The loop looks at cswitch.log at once, then every `POLL = 5` s, up to `SHORT_WAIT`; no result: the pane stays pending and the loop goes on. `MAX_INFLIGHT = 2`: before a start, the panes with `pending()` are counted; at 2 the pane gets `deferred: cswitch <name>(<pane>); 2 switches already in flight`. Tests: `test_a_stuck_pane_costs_one_short_wait_...` (fake clock < 70 s for a hung pane + a normal pane that is switched), `test_at_most_two_switches_in_flight`.
- AC2/AC3: result lines are ` done`, `FAILED`, ` skipped:` (`result_since`). `skipped:`/`FAILED` -> `BACKOFF[pane] = [misses, TICKNO + min(2**misses, 10)]` and one line `backoff: <name>(<pane>) <why>; miss N, next try in D ticks (tick T)`. `done` removes the entry. A result that comes after the window (the watcher's timeout skip, up to 10 min later) is collected at the start of the next tick from `INFLIGHT` (log offset kept), so it also feeds the backoff and no immediate retry happens. Test `test_skip_backoff_doubles_to_the_cap_and_done_resets_it`: tries on ticks 1, 3, 7, 15, 25, 35 (2, 4, 8, 10, 10), then done resets.
- AC4: `--dry-run` output and `wake_step` are unchanged. cswitch is stubbed by the contract (`mode.<pane>` = `skip`: skip line to the log, exit 75, no `-> account` line).
- Side effect (existing design, kept): `wake_step` skips a workspace while any of its panes is still `pending()`, so a hung pane holds the wake of its workspace until it ends or 15 min pass; the loop itself is no longer held. The old test `test_a_move_still_running_at_the_deadline...` expected a wake after a 900 s wait that no longer exists; rewritten to `..._holds_the_workspace_wake_but_not_the_loop`.
- Known limit (by design, AC1): two panes that stay `working` hold both slots until the watcher's 600 s timeout writes `skipped:`; the other panes show `deferred:` meanwhile. A `blocked` pane is skipped synchronously by cswitch (task 02), so it never takes a slot. The count covers panes with a claude process plus every pane this process started (`INFLIGHT`), so a pane between `/exit` and relaunch still counts.
- Checks: `python3 -m py_compile tools/claude-accounts/bin/cautoswitch tests/test_ca_autoswitch.py` ok; `tests/test_ca_autoswitch.py` 53 tests OK; grep hits `test_ca_install.py` 22 OK, `test_ca_launchers.py` 81 OK (3 skipped, as before). Running the three modules in one process fails in `test_ca_install` only when a `bin/__pycache__` exists in `tools/claude-accounts` (an install test copies every file of `bin/`); run with `PYTHONDONTWRITEBYTECODE=1`.

## Review
Fresh review (advisor) of 3c6a23f..226ac18 against AC1-6 and the contract; findings and what was done:
- In-flight count only saw panes with a live claude process; a pane between `/exit` and relaunch could let a third switch start: fixed (count over `panes | INFLIGHT`).
- `promote.md` missing: added.
- `## Review` missing: this section.
- Two hung `working` panes hold both slots up to 10 min: kept, it is the cap of AC1; written under Behaviour.
- Design notes: `tasks/03.md` has no design-notes section; the state decision (in memory) is the first line of Behaviour.
