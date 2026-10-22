# Evidence: 12 a ledger instead of copies; the 3rd return raises itself

**`squad-ledger` prints every task's state from `messages.jsonl`; HANDIN/PASS/FAIL no longer copy the Team Lead; the hook tells the sender of the first FAIL on a task's 3rd failing sha to send `BLOCKED NN: 3 returns`. Harness green.**

Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_ledger test_squad_log_message test_task_id_rule test_windows_safe test_dev_rules_size test_pod_contact_routes test_instructions test_processlint test_process_conversion` → OK.

## Behaviour

- **AC1 ledger** `LedgerTest.test_json_matches_expected`: task 03 (HANDIN A, FAIL x2 on A, HANDIN B, PASS x2) → sha B, both PASS, 1 return, 2 FAIL messages; task 04 (3 shas, FAIL on each) → 3 returns, the open BLOCKED, 2 ASK rounds. `--task 4` matches `04`; table test pins the columns. A DECISION closes BLOCKED and resets rounds; an ANSWER does not close a BLOCKED.
- **Row shape** every row has `task, sha, branch, handin_from, verdicts, returns, fail_messages, blocked, ask_rounds`; `null` when empty. A FAIL before any HANDIN is one return on an anonymous sha; shas compare by prefix; `3` and `03` are one row. Run read-only on this scope's live log: `ledger-live.txt`.
- **AC2 task IDs** `test_bare_number_ids_after_the_type`: `HANDIN 03:`→03, `HANDIN SET-13:`→SET-13, `FAIL 3:`→3, `STATUS: building SET-01`→SET-01, text with no ID→null.
- **AC3 notice** `NoticeTest`: fires once, on the first FAIL of the 3rd failing sha; not on the 2nd checker's FAIL on that sha, not on the 1st/2nd sha, not on a 4th; PASS never resets; an earlier sha failed again is not new; S names the Manager ([LC-7a]), M/L the Team Lead ([LC-7b]); two FAILs sent together on the 3rd sha → one notice (computed under the log's flock, from the log including the new record).
- **AC4 exit 0** forced failures: no `jq` on PATH, bad payload, log path unreadable (a directory) → exit 0, empty stdout.
- **Delivery path, live.** Headless `claude -p` with a PostToolUse hook on matcher `SendMessage` printing `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"CANARY-9902 ..."}}`: the model quotes it back ("PostToolUse:SendMessage hook additional context: CANARY-9902..."). Same for `Bash`. So the notice reaches the sender through `additionalContext`; the hook still exits 0.
- **Rules.** `grep -rn "copy the Team Lead" templates agents` → none. Edited: REV-12, REV-13b, LC-7a, LC-7b, LC-17, MSG-19, NOTE-3, ITER-3 (returns, passed shas from `squad-ledger`). MSG-3 unchanged (MSG-2 already says the ID follows the type; dev cap).
- **Developer rules size**: max over size x design x goal = 5106 B before and after (cap 5120). REV-13b shrinks M/L by 24 B; MSG-3 untouched.
- Hash note: rules REV-12, REV-13b, LC-7a, LC-7b, LC-17, MSG-19, NOTE-3, ITER-3 have new hashes (unreleased, by design).
