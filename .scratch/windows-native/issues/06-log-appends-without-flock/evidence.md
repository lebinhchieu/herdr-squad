# Evidence: 06 Log appends without `flock`

## Behaviour

Where `flock` is missing (Git Bash on Windows), `bin/squad-log-message` and `bin/squad-usage-hook` append under a `mkdir "$log.lock"` spin (about 5 s). A stale lock is removed. If the lock is not won, the append goes ahead unlocked and the exit code stays the same. Where `flock` exists, the old branch runs unchanged.

Proof: plain `>>` tore records over about 4 KiB on Windows. With the lock, 8 writers x 200 lines (one writer pads 9000 bytes) per hook keep every line intact.

- LogMessageStress: passed (1598 intact after the parallel pass, 2 launches lost to Git Bash fork failures, re-run serially).
- UsageHookStress: passed on the final run (1598 intact, 2 lost, within the 10% cap).
- StaleLock tests (2): passed.
- test_hooks_json: passed. test_squad_manager_guard: 1 error, `test_stop_hook_still_exempts_the_manager`, WinError 193 (ticket 03 scope, Team Lead said ignore).
