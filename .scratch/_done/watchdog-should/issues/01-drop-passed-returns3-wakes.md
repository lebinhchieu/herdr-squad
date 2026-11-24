# 01: the watchdog no longer wakes the Manager when a ticket passes, nor on a 3rd return

Duties: design notes dev; technical AC qa-white (with dev); business AC ticket; code check qa-white; behaviour check qa-black; promote.md qa-white; full suite qa-white (targeted tests by default).
Files: bin/squad-watchdog, tests/test_squad_watchdog.py, README.md

Owner: Developer (design notes in this file). Depends on: nothing. Base: main 32c186c. Chieu's choice E1 (b).
Ticket file the Developer commits: `.scratch/watchdog-should/issues/01-drop-passed-returns3-wakes.md` (copy this into it).
Next on the same files: ticket 03 (idle wake only when unexpected) waits for Chieu's answer to E2; the same Developer takes it.

## Why
`wake_events` sends `WAKE passed <id>` and `WAKE returns3 <id>` to the Manager whatever the team shape. The process already tells the plan owner: [LC-20a/20b/20e] (Developer tells it on pass), [LC-7b/7c] (3rd return). With a Team Lead on the team the wakes bypass [MSG-6]. Chieu: the watchdog must not inform when a ticket passes.

## Technical AC
1. `wake_events` no longer emits a `passed:<id>` or `returns3:<id>` event. A ticket that passes, or has 3 returns, produces no `herdr agent prompt` and no `wake` log line.
2. The `blocked` wake is unchanged: a pane blocked 10 minutes wakes the Manager once, never relays, nothing is sent into a blocked Manager pane, a failed send is retried (existing behaviour and tests keep passing).
3. Dead code goes with them: `RETURNS_WAKE`, `ledger_rows`, `sha_text`, the `squadledger` and `DONE`-based `passed` bookkeeping that only fed those two wakes, if nothing else uses them (`grep` each name before removing; `passed_keys` stays: the snapshot uses it). State keys in `watchdog.state.json` that old files hold (`wake_status`) are ignored without error.
4. The module docstring and `README.md` line for `bin/squad-watchdog` describe only the blocked wake; no word about passed or returns3 remains (`grep -n -i "passed\|3rd return\|returns3" bin/squad-watchdog README.md` shows only the unrelated uses, listed in `## Behaviour`).
5. Tests: remove `test_passed_once_and_baseline_is_silent`, `test_passed_from_pass_messages_when_the_label_is_empty`, `test_third_return_counts_like_the_ledger_and_sends_once`; add ONE test that a ticket going to passed and a 3rd return send nothing. Extend the existing file; no new test file; no test newly skipped. Adjust `test_switch_off_and_old_state_file` and the blocked tests only if they relied on the removed events.
6. `## Behaviour` quotes one `squad-watchdog tick` on a scratch scope (stub herdr json, as in `tests/test_squad_watchdog.py`) where a ticket goes building -> passed: the log has no `wake` line and nothing was sent.

## Tests to run (targeted)
`cd tests && python3 -m unittest test_squad_watchdog`, plus every hit of `grep -rl 'squad-watchdog\|WAKE\|wake_events' tests/` (test_squad_start, test_squadtask, test_squad_log_message, test_ca_*: run those that reference the watchdog). SQ-10 applies: the diff edits `bin/` text; also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result.

## Manager notes (SQ-15 dry run on 32c186c)
- `cd tests && python3 -m unittest test_squad_watchdog`: 46 tests OK on base. No known failing.
- No file is deleted or moved (SQ-1): no reader-before-deleter order. Related tickets: 03 shares `bin/squad-watchdog` and its test, so 03 starts from 01's passed branch (same Developer, same worktree).

## Design notes (Developer)
- `wake_events(st, snap, now)` keeps only the `blocked` event; `rows`/`ledger_rows`, `sha_text`, `RETURNS_WAKE`, the baseline flag and the `wake_status` bookkeeping are gone. The blocked event needs no baseline: it fires only after 600 s of `since`, which a first pass cannot reach.
- `wake_status` from an old state file is popped on the next pass (no error). `DONE`, `passed_keys`, `squadledger` stay: `all_done`, the snapshot `passed` field and `passed_keys` still use them (`grep` checked).
- Tests: 3 removed, 1 added (`test_a_ticket_that_passes_or_returns_three_times_sends_and_logs_nothing`); `test_switch_off_and_old_state_file` and the held/retry test now use a blocked dev pane instead of a passed ticket.
