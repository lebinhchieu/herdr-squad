# 13 Ledger keeps every verdict with its cause

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/05-ledger-verdicts.md`, Token Coach proposal 5)
Blocked by: 12
Aim: Ledger lists each return with sender, cause and criteria
Estimate: 1.5h
Depends on: 12

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/13.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Also run `test_squadboard_tasks`, `test_squadplan`, `test_squad_watchdog`, `test_squad_merge_record`, `test_squadtask` (they read `squadledger.build`).
Files: `bin/squadledger.py`, `tests/test_squad_ledger.py`

## Problem
With no QA, `squad-ledger` shows no verdicts and the cause of each return is lost. The Manager's and Tech Lead's `FAIL` messages are already recorded and counted (returns 2 for task 04), but the cause text is not kept, and the verdicts of a failing sha vanish at the next `HANDIN`. The Tech Lead sends `STATUS ... no FAIL` by design, so no PASS exists.

## Change
`squadledger.build` keeps its row keys and values. A second function `history(records, task)` returns, per task, every `PASS` and `FAIL` in order from any sender: `{sha, from, verdict, cause, acs}`; `cause` = first line after `FAIL NN:` (up to 160 characters); `acs` = `AC\d+[a-z]?` tokens in the text. `squad-ledger --task NN` prints the table and under it one line per entry; without `--task` the output is unchanged; `--json` adds `history` only when `--task` is given.

## AC
- AC1: fixture HANDIN s1, FAIL from the Team Lead naming AC5, HANDIN s2, FAIL from the Manager naming AC3, HANDIN s3: `--task NN --json` history has 2 entries in order with the right sha, sender, cause and acs; `verdicts` of s3 stays null; `returns` 2.
- AC2: a PASS from the Manager appears in history.
- AC3: without `--task` the table output is byte-identical to base (existing ledger tests pass unchanged).
- AC4: `FAIL integration: ...` shows under task `integration` (needs 12).
- AC5 (real data): `SCOPE_DIR=<po-clarity scope> python3 bin/squad-ledger --task 04` prints two history lines with their cause.

## Comments
