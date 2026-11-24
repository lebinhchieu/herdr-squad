# Evidence: 11 11 squad-usage shows the start size and first-act turn
sha: 1c764f8

## Behaviour

Code sha 1c764f8 (base bf69a21, ticket 10 on top of 46d2f4b). Files: `bin/squad-usage`, `tests/test_squad_usage.py`; `bin/squadtranscript.py` needed no change (the old `first_action_ctx` in `bin/squad-usage` became `first_turns`, one pass giving start, 1st act and act turn; 1st act values are unchanged).

- AC1: `test_act_turn_counts_main_thread_turns_up_to_the_first_action_and_start_is_the_first_turn`: 3 main-thread turns (Read, Read, Edit) → `act turn` 3, `start` 30k (= ctx of turn 1), `1st act` 45k, in `--sessions` and in the table.
- AC2: `test_a_leading_sidechain_turn_does_not_shift_act_turn_or_start`: a leading sidechain Edit turn is not counted; `act turn` 2, `start` the first main-thread turn.
- AC3: `test_no_action_gives_a_dash_for_act_turn`: `1st act` and `act turn` are `-`.
- AC4: `test_a_message_over_several_lines_keeps_the_max_for_start_and_act_ctx`: lines of one message with usage 10k, 30k, 20k give `start` 30k; the action message 40k, 50k gives `1st act` 50k.
- Red on the ticket 10 base bf69a21 (new test file against that tree): 10 failures, 1 error, including these four; green at 1c764f8.
- AC5 (real data, this scope, a Developer with an edit): `SCOPE_DIR=<po-clarity scope> python3 bin/squad-usage --sessions plugin-dev-po-clarity-10`:
```
session  peak ctx  start  1st act  act turn  turns  last turn
1        117k      33k    33k      2         74     2026-11-24 16:30
```
  Table rows (cut to 120 columns; `act turn` follows `1st act`):
```
agent                     model/effort              turns  peak ctx  max peak  last ctx  1st act  act turn  line  out   
plugin-dev-po-clarity-10  claude-sonnet-5-5/high    74     117k      117k      117k      33k      2         83k   40k   
plugin-dev-po-clarity-14  claude-sonnet-5-5/high    41     100k      100k      100k      50k      6         100k  31k   
```
- `--help` documents `start`, `1st act`, `act turn`, `peak ctx`, `max peak`; sidechain turns are never counted. `--sessions` columns: session, peak ctx, start, 1st act, act turn, turns, last turn.
- Tests (foreground, one file at a time, all OK): test_squad_usage 39, test_squadtranscript 3, test_squad_usage_hook 13, test_squad_manager_guard 25, test_session_lookup 16, test_squadboard_active 9, test_squad_respawn 34, test_squadruntime 74, test_crlf_squad_files 6, test_templates 8; SQ-10 trio: test_windows_safe 14, test_utf8_helpers 14, test_instructions 16.
- Review finding fixed in the last commit: `first_turns` counted synthetic and usage-less lines as turns, which `read_session` (the `turns` column) skips; now it skips them too, test `test_a_synthetic_turn_is_not_a_turn_so_act_turn_agrees_with_the_turns_column`. The real-data output above is unchanged by it.

## Review

Fresh sonnet/high subagent on `bf69a21..1c571b3`; checks are in `## Checks`.
- Standards: no findings; tests extend the existing file and map to AC1 to AC4; no other reader of the table's column indexes (grep without worktrees).
- Spec: AC1 to AC4 covered, design met (`start`, `act turn`, sidechain skipped, `--sessions` columns, table column after `1st act`); `bin/squadtranscript.py` needs no change.
- Bug found and fixed in the next commit: a synthetic or usage-less leading line was counted as a turn (start 0k, act turn shifted by one against the `turns` column). `first_turns` now skips what `read_session` skips; new test.
- Checked and fine: a message id repeating after another keeps its first position; uuid fallback; 1st act equals the old `first_action_ctx`.

## Checks

| AC | Dev: test or capture | QA whitebox | QA blackbox |
|---|---|---|---|
| AC1 | `test_act_turn_counts_main_thread_turns_up_to_the_first_action_and_start_is_the_first_turn` OK: act turn 3, start 30k; red on bf69a21 | - | - |
| AC2 | `test_a_leading_sidechain_turn_does_not_shift_act_turn_or_start` OK: act turn 2 | - | - |
| AC3 | `test_no_action_gives_a_dash_for_act_turn` OK: `-` | - | - |
| AC4 | `test_a_message_over_several_lines_keeps_the_max_for_start_and_act_ctx` OK: 30k / 50k | - | - |
| AC5 | `SCOPE_DIR=<po-clarity> python3 bin/squad-usage --sessions plugin-dev-po-clarity-10` prints `1  117k  33k  33k  2  74  2026-11-24 16:30` | - | - |

## Changelog line

squad-usage: `--sessions NAME` shows `start`, `1st act` and `act turn` per session and the table gets `act turn` after `1st act`; why: nothing showed how many turns a Developer read before its first edit, and the context at its start.
