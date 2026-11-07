# Evidence 03

## Behaviour

The board reader (`bin/squadboard_tasks.py`) now folds the event store first, the ledger second, the ticket label third. Checked on a temp squad folder (never the real `task-events/`), 4 tickets, QA team and no-QA team:

| Case | Row shown |
|---|---|
| nobody claimed 01 | `todo`, owner `unassigned`, no last active |
| 03 has `Blocked by: 02`, 02 open | `blocked`, waits on `ticket 02`; claim on 03 gives `in progress` with the W1 note |
| 1 of 2 QAs PASS (plus a Manager PASS) | `checking, 1 of 2 PASS, waiting on QA blackbox, ...`; last active = newest event |
| both QAs PASS, tip matches or unknown | `passed`, waits on PO |
| same, branch tip moved | `sha changed after PASS` |
| no-QA team, evidence PASS by hook | `passed` (never `checking, 0 of 0`) |
| no-QA team, W9 on the handin | `in progress`, note `W9 evidence check failed: ...` |
| branch recorded in another scope, in `main` | `merged`, owner kept, tip found by the recorded branch |
| no events, a sibling scope with the same ticket folder has a HANDIN | owner and branch `squad/<squad>/<that scope>/<dev>`, M from that scope's roster |
| `Status: wontfix` | `wontfix` |
| bad lines or no store file | no crash, ledger or `todo` |

`ready for review` is gone, and the `ready_for_review` key is no longer in `/api/tasks` data. `squadboard_tasks.ready_by_scope` keeps its name for the Inbox and counts `passed` rows that have a branch tip. The picker (`squadboard_list`) counts a `merged` event as done and an open `blocked` event (or a return) as stuck. `squadboard_active` takes the newest event time as a ticket's last active.

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 todo, unassigned, no time | `StoreReader.test_AC1_AC7_AC8_AC9_...` | `cd tests && python3 -m unittest test_squadboard_tasks` |
| AC3 checking, 1 of 2, names the missing QA | `StoreReader.test_AC3_AC5_...` | same |
| AC4 no QA: passed by evidence, W9 stays in progress | `StoreReader.test_AC4_...` | same |
| AC5 every QA PASS: passed, waits PO, Manager PASS not counted | `StoreReader.test_AC3_AC5_...`, `Tasks.test_T07_AC5_AC6_ready_list` | same |
| AC6 merged, built in another scope | `StoreReader.test_AC6_T9_...` | same |
| AC7 blocked from live `Blocked by:` | `StoreReader.test_AC1_AC7_...` | same |
| AC8 claim on an open blocker: in progress + W1 note | `StoreReader.test_AC1_AC7_...` | same |
| AC9 wontfix (also when blocked: waits on nobody) | `StoreReader.test_AC1_AC7_...` | same |
| AC7 turns `todo` by itself when the blocker passed | `StoreReader.test_AC1_AC7_...` | same |
| s2 one word per row; AC12 / AC20 `sha changed after PASS` | `Tasks.test_T07_AC1_AC2_AC3_stage_per_task`, `StoreReader.test_AC3_AC5_...` | same |
| s5 label table on read (`done` gives `passed`) | `Tasks.test_T07_AC1_...`, `ScopeFilesShape.test_T28_TA3_...` | same |
| `ready for review` dropped, tip unknown gives `passed` | `Tasks.test_T07_AC5_AC6_ready_list`, `StoreReader.test_AC3_AC5_...` | same |
| T8 slots / no QA | `StoreReader.test_AC4_...` | same |
| T19 read side (hook `evidence` pass gives `passed`; W9 in the note) | `StoreReader.test_AC4_...` | same |
| T24 override PASS, all-retired QAs keep their slots | `StoreReader.test_T24_...` | same |
| T9 other-scope branch; D8 sibling ledger | `StoreReader.test_AC6_T9_...`, `test_D8_...` | same |
| T10 bad or missing store never raises | `StoreReader.test_T10_...` | same |
| T11 targeted tests | files below | see below |
| last active from events (board, task picker) | `Active.test_T03_task_event_...`, `StoreReader.test_AC3_AC5_...` | `python3 -m unittest tests.test_squadboard_active` |
| tasks_done / stuck from events | `PickerTests.test_T03_task_events_feed_...` | `cd tests && python3 -m unittest test_squadboard_list` |

Runs (targeted, T11): `test_squadboard_tasks` 24 OK; `test_squadboard_active` 9 OK; `test_squadboard_inbox` 12 OK (real `ready_by_scope` wiring); `test_squadboard_list` 13, 1 failure that is also on base 125e654 (`test_T04_AC1_rows_order_and_done_list`, reads file mtimes); `test_board_fixtures` 4 OK.

Note: `test_squadboard_inbox` hung twice under a pipe, then passed in 3 s on a plain run; not tied to this change.

Team Lead ruling (ANSWER 03): the two assertions that named `ready for review` are changed in 03, one line each: `tests/test_squadboard_panels.py` (`test_T12_AC7_...`: stage list uses `passed`; ready list and filter count are 0 until 04 renames the JS flag) and `tests/test_squadboard_demo.py` (`STAGES` uses `passed`). Re-run: panels `Panels12.test_T12_AC7_...` OK, `test_squadboard_demo.RunningDemo` 5 OK. The other failures in those two files are on base 125e654 too.
