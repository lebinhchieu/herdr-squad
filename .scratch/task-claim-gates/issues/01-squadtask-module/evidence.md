# Evidence 01: squadtask module

## Behaviour

A scratch squad, team with no QA (M = 1), ticket 02 `Blocked by: 01`:

```
$ squad-task claim 02 --owner dev   (ticket 02 is blocked by 01)
recorded claim 02
warning: W1 started while ticket 01 is not yet passed
$ squad-task handin 02 --sha abc1234
recorded handin 02
$ squad-task pass 02 --sha abc1234   (confirmer; no QA on this team, so M=1)
recorded pass 02
$ squad-task show 02
02  passed  owner dev  sha abc1234  returns 0  
```

The claim on a blocked ticket gives W1 and is still recorded (AC8). Events go to `$SQUAD_DIR/task-events/<slug>.jsonl`; `squad-task show` derives the word.

## Review

| AC | Test or capture | How run |
| --- | --- | --- |
| states.md s2 words, s5 label table (needs-triage, needs-info, ready-for-agent, ready-for-human, claimed, done, wontfix) | `CheckersAndWords.test_words_and_label_table` | `cd tests; python3 -m unittest test_squadtask` |
| s4 M never 0, T8 (no QA; Team Lead as confirmer) | `CheckersAndWords.test_checkers_m_never_zero_and_confirmer` | same |
| s6 W1-W8 return text and still write, T6 | `Warnings.test_w1_to_w8_each_returns_text_and_still_writes`, `test_blocker_passed_or_merged_is_not_open` | same |
| AC8 claim while `Blocked by:` open: W1, claim recorded | W1 row of the test above; CLI capture above | same |
| T1 exit 0 on warning, hook never fails, write error never raises | `StoreAndHook.test_hook_entry_warns_and_never_fails`, `test_cli_claim_exit_codes` | same |
| T2 two writers, `mkdir` lock without `fcntl` | `StoreAndHook.test_concurrent_writers_and_mkdir_lock` | same |
| T3 parity with `squadledger.build`; T4 event shape; T5 real samples, ASK and evidence handin write nothing | `StoreAndHook.test_event_shape_and_fold_parity_with_ledger` | same |
| T11 targeted tests | `test_squadtask`, `test_squad_ledger` (unchanged), `test_windows_safe`, `test_no_bare_bash`: 45 OK | `cd tests; python3 -m unittest test_squadtask test_squad_ledger test_windows_safe test_no_bare_bash` |
| T12 stdlib, Windows-safe | `test_windows_safe` (every `bin/*.py`) | same |

Notes: a verdict that names an unknown sha counts for the current sha (same as `squadledger`); W5 still warns. W6 counts QA slots only ("1 of 2 checkers PASS").
