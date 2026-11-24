## Review
AC trace
AC1 | README.md rows `bin/squad-watchdog`, `bin/squad-away-hook` | `grep -n 'squad-away-hook\|sleep-when-idle\|Sleep-when-idle' README.md`
AC2 | CONTEXT.md Away mode, Sleep-when-idle, Watchdog, one Relationships line | `grep -n 'Away mode\|Sleep-when-idle\|Watchdog' CONTEXT.md`
AC3 | docs/adr/0022-sleep-when-idle-and-away-mode.md | `cat` it
AC4 | no "Sleep-when-done" in README or CONTEXT | `grep -c Sleep-when-done README.md CONTEXT.md` (0, 0); QA greps code
AC5 | tests/test_squad_start.py | `python3 tests/test_squad_start.py` and `python3 -m unittest test_squad_start` in tests/: 49 tests each
AC6 | bin/squad-watchdog docstring | `sed -n 12,20p bin/squad-watchdog`
AC7 | no version bump | `git diff --stat`
T1: test_squad_watchdog 19 OK; README/CONTEXT.md hits (test_squad_close 24, test_squad_path_guard 21, test_promotion_0_6_0 3) OK.
T3: both README rows split into 4 fields by `|` (no stray pipe).
Note: the ADR Context names the old "Sleep-when-done" as history (promote.md text, kept as written).
