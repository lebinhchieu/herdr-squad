# Evidence: 13 13 Ledger keeps every verdict with its cause

## Behaviour

Base 2b535f5 (ticket 12 tip 24c1fc8), code sha e5bbc31. `SQUAD_*` unset, `PYTHONDONTWRITEBYTECODE=1`, tests foreground with `< /dev/null`.

**Tests.** `cd tests && python3 -m unittest test_squad_ledger test_squad_usage test_squadtask test_squad_merge_record test_squadboard_tasks test_squadplan test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions`: **Ran 269 tests, OK** (SQ-10 trio included). The `grep -rl` hits of `squadledger|squad-ledger` are test_squad_ledger, test_squad_usage, test_squadtask, test_squad_merge_record: all in that run. `squad-process lint`: exit 0.

**Changed test.** `test_task_filter_and_table` counted the output lines of `--task 4` (2); with history it prints the table plus one line per FAIL, so it now asserts 2 + 3. No other existing test changed (AC3 is the no-`--task` output).

**AC1.** `test_history_handin_without_checker_keeps_verdicts_null`: HANDIN a, FAIL from tl naming AC5, HANDIN b, FAIL from mgr naming AC3, HANDIN c: `--task 06 --json` history = `[(aaaaaaa, tl, "AC5 wrong", [AC5]), (bbbbbbb, mgr, "", [AC3])]`, `verdicts` null, `returns` 2. A FAIL text without a colon after `FAIL NN` gives cause "" (found in review: `http://` in the text was taken as the cause head).
**AC2.** `test_history_lists_every_verdict_with_cause_and_acs`: a PASS from the Manager is the third history entry; cause is cut at 160 characters; `AC3 AC3 AC12b` gives `[AC3, AC12b]`; without `--task` the rows have no `history` key; the text output is table plus one line per entry.
**AC3.** Real log, base `squadledger.py` (`git show main:bin/squadledger.py`) against the new module: `table(build(r))` and `build(r)` are equal, and `squad-ledger | md5sum` is `6fa69be07a7c0481faeec2ad7abdd98c` for both. `build()` rows keep their keys (`test_every_row_has_every_key_null_when_empty` unchanged).
**AC4.** `test_history_of_integration_task`: `FAIL integration: ... AC2` gives row `integration` with one FAIL entry, acs `[AC2]`.
**AC5 (real data).** `SCOPE_DIR=<po-clarity scope> python3 bin/squad-ledger --task 04` prints the table row (returns 2) and two history lines:
```
  c2c8c6a  plugin-tl-po-clarity  FAIL: c2c8c6a, `squad-evidence checks .scratch/po-clarity/issues/04-plan-panel/checks.md` exits 1: line 7 (AC5 row) has 6 cells, want 4, because the `\|` inside the g  [AC5]
  0945f9b  plugin-mgr-po-clarity  FAIL: sha 0945f9b, built-UI check ([SIZE-10a]). Scope, unfolded and goal shots are fin...
```
`--json` gives `history` with 2 entries (acs `[AC5]` and `[]`, causes 160 characters).

## Review

One fresh-context sonnet (high) subagent review of 24c1fc8..9820b6e, Standards and Spec lists (the code-review skill was not run as such).

**Standards.**
1. `_acs` can be `list(dict.fromkeys(...))`: done.
2. `test_task_filter_and_table` was sliced to two lines, which made its length assert vacuous: it now asserts the full count (2 + 3).
3. `history_lines` prints `None` for a record with no sender: cosmetic, left.
4. Test economy: three new tests for the five ACs, each a real risk.

**Spec.** AC1-AC4 hold. One bug: `_cause` took the text after any colon of the first line, so `FAIL 3 AC5 see http://x/y` gave `//x/y`. Fixed with an anchored `VERDICT_HEAD` regex and a test (commit e5bbc31). `AC_TOKEN` has `\b` after the optional letter, so `AC5ab` gives nothing: kept on purpose. AC5 needs real data: shown in Behaviour.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `test_history_handin_without_checker_keeps_verdicts_null`: OK | - | - |
| AC2 | `test_history_lists_every_verdict_with_cause_and_acs`: OK | - | - |
| AC3 | base vs new `table(build(r))` equal and the md5 of `squad-ledger` output equal on the real log: OK | - | - |
| AC4 | `test_history_of_integration_task`: OK | - | - |
| AC5 | `squad-ledger --task 04` prints 2 history lines with cause: OK | - | - |

## Changelog line

`squad-ledger --task NN` lists every PASS and FAIL of the task (sha, sender, cause, criteria named), `--json` adds `history` for it; why: with no QA the cause of each return was lost and the failing sha's verdicts vanished at the next HANDIN.
