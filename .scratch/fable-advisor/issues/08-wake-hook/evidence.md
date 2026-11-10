# 08 evidence

## Behaviour
`squad-watchdog` (extended, not a new hook) sends the scope's Manager one `WAKE ...` message per event: `passed <ticket>`, `returns3 <ticket>` (3rd return, `squad-ledger` count, with the current sha), `blocked <agent>` (pane `blocked` for 10 minutes: "Chieu's to answer; do not relay or approve the prompt"). Never twice (key in `watchdog.state.json` `wake_sent`, stored only after a successful send), nothing on a quiet pass, nothing into a Manager pane that is `blocked` (held, retried later), first pass or an old state file = baseline only. Switch: `squad-watchdog wake on|off`, file `watchdog.wake`, no file = on, shown by `status`. Target is the Manager the watchdog was started for (AC1 "plan owner" = that Manager). Message text: fixed template plus ticket id, hex sha, agent name, and the roster "owns" text cut to 80 characters, one line, no control characters. The send is the existing `herdr agent prompt` argv call.

Real samples (T1), read-only on this scope with `wake_events`:
- Ticket status words in the repo's tickets: `ready-for-agent`, `ready`, `handed in`, `needs-triage`, `done`, `resolved`, `blocked`, and empty (tickets without a Status line). DONE words kept: `passed done resolved merged`.
- herdr agent states seen live: `idle`, `working`, `done` (squadboard maps it to idle); `blocked` is the name in `squadboard_agents.STATUSES`; none was blocked at the time.
- `squad-ledger` on this scope's `messages.jsonl`: returns {01: 2, 04: 0, 07: 0, 05: 0, 02: 0, 03: 0}, current shas e.g. 07 ea90150, 01 06094ef. `wake_events` with a baseline of "building" for all tickets and this data gave no event: no ticket was passed in the ticket files and no ticket had 3 returns. The count comes from `squadledger.build`, the same function `squad-ledger` prints (two checkers on one sha = one return; test compares it).

Tests: `tests/test_squad_watchdog.py::WakeTest` (passed once + baseline, 3rd return once and 4th silent with the ledger count, blocked 9 min / 10 min / new spell, blocked Manager held then sent and failed send retried, off switch and old state file, hostile roster text, CLI switch and status).

## Review
AC trace
- AC1 | WakeTest.test_passed_once_and_baseline_is_silent, test_third_return_counts_like_the_ledger_and_sends_once, test_blocked_pane_wakes_once_after_10_minutes_and_never_relays | `cd tests; PYTHONPATH=. python3 -m unittest test_squad_watchdog`
- AC2 | test_blocked_pane_wakes_once_after_10_minutes_and_never_relays (text), test_no_wake_into_a_blocked_manager_pane_and_a_failed_send_is_retried | same
- AC3 | test_switch_off_and_old_state_file, test_cli_wake_switch_and_status | same
- AC4 | all WakeTest tests; no-repeat in each
Tech AC: W1-W5 and T1-T6 as above; T7 existing 19 watchdog tests unchanged and pass; T8 `git diff skills/` is the one word `phases`.
Run: `cd tests; PYTHONPATH=. python3 -m unittest test_squad_watchdog test_squad_start test_squad_log_message test_squadtask test_squad_report_query`

## Return fix (QA whitebox FAIL at 3675aa1)
`passed` now comes from `passed_keys` (event store via squadtask.is_passed, else ledger verdicts all PASS on the current sha), not the ticket label. Test: `test_passed_from_pass_messages_when_the_label_is_empty`.
