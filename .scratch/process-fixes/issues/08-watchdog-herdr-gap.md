# Task 08: Watchdog: herdr outage must not carry `quiet_since` over

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`.

Status: handed in
Source: follow-up of scope watchdog (E6 (b)). After a long herdr outage the watchdog can suspend the PC at the first quiet check, because `quiet_since` is kept while herdr is down.
Files: bin/squad-watchdog (`decide`, the `not snap["ok"]` branch, about line 173), tests/test_squad_watchdog.py
Ticket: commit this file's content as `.scratch/process-fixes/issues/08-watchdog-herdr-gap.md` in your first commit.
Base: main. Own worktree. No merge, no version bump.

## AC
- AC1 When herdr does not answer, the watchdog sets `quiet_since` back to None (the quiet timer restarts after herdr is back).
- AC2 One test: quiet for most of `sleep_after`, herdr down, herdr back with a quiet machine, no `sleep` event at the first check; it fires only after a full `sleep_after` of quiet again.
- AC3 Existing watchdog tests pass; nothing else changes. Touched test file plus `grep -rl 'quiet_since\|squad-watchdog' tests/` hits pass.

## Design notes
One line in the down branch. Dev confirms and notes the touched files here.

Confirmed. Touched: `bin/squad-watchdog` (`decide`, down branch: `st["quiet_since"] = None`), `tests/test_squad_watchdog.py` (one new test). `grep -rl 'quiet_since\|squad-watchdog' tests/` hits only `tests/test_squad_watchdog.py`.

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 | `test_a_herdr_outage_restarts_the_quiet_clock_so_the_pc_does_not_sleep_at_the_first_check_after_it` (the first check after the outage, 1 min in, shows the clock was reset) | `cd tests && python3 -m unittest test_squad_watchdog` |
| AC2 | same test: quiet 0-4 min, herdr down at 10, back at 11: no suspend; 15: none; 16: one suspend | same |
| AC3 | the other 14 tests of `test_squad_watchdog`; the grep hits only that file | same; diff is 1 line in `bin/squad-watchdog` |

Mutation check: without the new line the new test fails (suspend at the first check after the outage); with it, 15 tests pass.
