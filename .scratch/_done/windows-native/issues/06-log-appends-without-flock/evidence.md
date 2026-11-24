# Evidence: 06 Log appends without `flock`

## Behaviour

Where `flock` is missing (Git Bash on Windows), `bin/squad-log-message` and `bin/squad-usage-hook` append under a `mkdir "$log.lock"` spin (about 5 s). A stale lock is removed. If the lock is not won, the append goes ahead unlocked and the exit code stays the same. Where `flock` exists, the old branch runs unchanged.

Reason: O_APPEND does not promise one intact write for records over about 4 KiB, so without `flock` the lock serialises the appends (decided by reasoning, no stress claim; ADR 0011 D3b).

- The stress test file `test_log_append_stress` was removed by PO order (ticket 10).
- StaleLock tests (2): passed.
- test_hooks_json: passed. test_squad_manager_guard: 1 error, `test_stop_hook_still_exempts_the_manager`, WinError 193 (ticket 03 scope, Team Lead said ignore).
