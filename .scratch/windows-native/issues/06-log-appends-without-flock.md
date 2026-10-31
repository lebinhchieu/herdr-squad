# 06: Log appends without `flock`

Status: ready-for-agent
Type: task
Blocked by: none
Source: findings.md W5

**What:** `bin/squad-log-message:72` and `bin/squad-usage-hook:41` run `{ flock 9 2>/dev/null; printf '%s\n' "$record" >&9; } 9>>"$log"`. Git for Windows has no `flock` (`command -v flock` fails), so concurrent hooks append to `*.jsonl` without a lock. Lines are short and appends use `>>`, so interleaving may never happen; that is unproven. The hook is silent either way.

## Do
- Either prove with a small stress test (N parallel writers, M lines each, every line intact) that unlocked `>>` appends are safe on Windows, and document it in ADR 0011; or move the append into a small Python helper that locks with `msvcrt` / `fcntl` as `squadinbox.py` does.

## AC
- [ ] On Windows, 8 parallel writers × 200 records give 1600 intact JSON lines in the log.
- [ ] The Linux path still uses `flock`.

## Comments
- 03d: Windows `test_squad_ledger` `test_simultaneous_fails_on_third_sha_give_one_notice` fails (0 notices, expected 1) because there is no `flock`; left failing, covered by this ticket.
