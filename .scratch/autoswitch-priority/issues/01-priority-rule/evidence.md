# Evidence 01: priority rule for the next account

## Behaviour
Each case is a real `cautoswitch --once --dry-run` run in the test harness (stub herdr, `usage-N` cache files), c1 = current at 95% 5h, threshold 90.

- Steps 1-3, weekly rank wins (c2 50% left, 25 h = 2.0/h; c3 100% left, 100 h = 1.0/h, lower 5h):
  `[dry-run] would set w1 default to c2 (weekly rank, score 2.00/h): c1 5h 95% 7d 80%; c2 5h 30% 7d 50%`
- Step 4, weekly top has 5h 70 (not under 60), so lowest 5h of all (c3 has no reset time):
  `[dry-run] would set w1 default to c2 (5h order): c1 5h 95% 7d 80%; c2 5h 70% 7d 10%`
- Step 4 when every 5h is above 60:
  `[dry-run] would set w1 default to c3 (5h order): c1 5h 95% 7d 80%; c3 5h 65% 7d 40%`
- Reset missing: c2 has no score, c3 is scored and wins:
  `[dry-run] would set w1 default to c3 (weekly rank, score 5.00/h): c1 5h 95% 7d 80%; c3 5h 40% 7d 50%`
- Reset in the past counts as 1 h (no divide by zero):
  `[dry-run] would set w1 default to c2 (weekly rank, score 60.00/h): c1 5h 95% 7d 80%; c2 5h 10% 7d 40%`
- Locked c2 (7d 100) skipped; c3 with 7d 97 comes in step 4 only:
  `[dry-run] would set w1 default to c3 (5h order): c1 5h 95% 7d 80%; c3 5h 50% 7d 97%`
- Guard, no other 5h is lower than the current 95:
  `w1 c1 over 90% but no other account has a lower 5h and a 7d under 100%; staying. c1 5h 95% 7d 10%`

## Real samples of the reset field (T18)
Real cache lines (`f5 r5 f7 r7 at`), `~/.claude-accounts/usage-N`:
- (a) non-zero r7: `usage-2`: `1 1794211200 84 1794348000 1794198049` (r7 = 1794348000, an epoch).
- (b) live `seven_day.resets_at` is an ISO string; `usage-popup.sh` parses it with `datetime.fromisoformat` and maps null to 0. `iso_epoch()` does the same and maps null/bad to None. Unknown case: `r7` = `0` gives None (test `test_usage_returns_week_reset_from_cache`). No real idle `0` line existed on this machine today.

## Review
Checks: `python3 -m py_compile` clean; `tests/test_ca_autoswitch.py` 58 tests OK. `tests/test_ca_install.py` and `tests/test_ca_launchers.py` (grep hits) fail the same way on the base commit 4e9b310 (environment, not this change). Two old tests encoding "lower on both" were rewritten, none skipped. `windows/autoswitch.py` untouched.
