# Evidence: 15 Merge check passes a team with no QA; version bump

## Behaviour

Code sha 19b1f8a (base 2033fa8 = 53577d plus the merge of ticket 14's branch dfb2a3d, an ancestor of HEAD). Files: `bin/squadtask.py`, `bin/squadmergecheck.py`, `.claude-plugin/plugin.json`, `skills/squad-process-update/changelog.md`, `README.md` (row `squad-merge-check`), `tests/test_squadtask.py`, `tests/test_squad_merge_check.py`.

**AC1 checkers and slots.** `test_squadtask.py::CheckersAndWords::test_checkers_of_a_team_without_qa_ignore_retired_rows`: two retired QA rows; team `tech-lead, designer` and `none` give `{"qa": []}` and slots `["evidence"]`; `qa-white`, `ba, qa-black`, a blank or missing line and an invalid token keep the two retired agents; a live QA row still wins. FAILS on the base `bin/` (checked: base `squadtask.py` and `squadmergecheck.py` restored over HEAD, 3 new tests failed, then the patch re-applied).

**AC2 HANDIN hook.** `test_squadtask.py::NoQaEvidence::test_hook_records_evidence_pass_for_a_no_qa_team_with_retired_qa_rows`: in a temp git repo with `team: tech-lead, designer` and two retired QA rows, the hook writes events `handin` then `pass` with slot `evidence`, by `hook`, and the word is `passed`. FAILS on base (no pass recorded).

**AC3 merge-check.** `test_squad_merge_check.py::MergeCheck::test_no_qa_team_evidence_pass_is_ok_and_a_rule_id_row_is_no_ticket`: real CLI run, an `evidence=PASS` state plus a `SQ-10` row on the same sha: exit 0, output has `[evidence=PASS]`, no `SQ-10`, last line `VERDICT: ok`. FAILS on base (refuse: sha not passed by every checker).

**Real data** (this scope, `SCOPE_DIR` not set, scope passed by path; scope.md line 8 is `team: tech-lead, designer`):
```
$ python3 -c "import squadtask as t; c=t.checkers('<po-clarity scope>'); print(c, t.slots(c))"
{'qa': []} ['evidence']          (base: the two retired agents plugin-qaw-po-clarity, plugin-qab-po-clarity)
$ python3 bin/squad-merge-check HEAD --base main --scope <po-clarity scope>   -> prints its ancestor/log/dirty/siblings lines and the merge-rules pointer
```

**AC4** `test_squadboard_tasks` 26, `test_squad_watchdog` 114, `test_squadplan` 12: OK.

**AC5**
```
$ grep -c '"version": "0.11.1"' .claude-plugin/plugin.json      1
$ head -1 skills/squad-process-update/changelog.md              ## v32 -- 2026-11-25
$ python3 bin/squad-process lint                                exit 0
$ git merge-base --is-ancestor dfb2a3d HEAD                     exit 0 (ticket 14's tip is an ancestor)
```
The `## v32` bullets for 09-14 are the `## Changelog line` of each passed evidence.md (09-11 read with `git show squad/plugin/po-clarity/plugin-dev-po-clarity-14:<path>`); all six were present.

**Tests run** (foreground, `< /dev/null`, one file at a time):
```
test_squadtask 22 OK · test_squad_merge_check 12 OK · test_squadboard_tasks 26 OK · test_squad_watchdog 114 OK · test_squadplan 12 OK
grep -rl hits: test_squad_merge_record 3 · test_squad_log_message 24 · test_squad_review_pack 7 · test_old_language_inventory 2 · test_promotion_0_6_0 3 · test_rules_wording 31 · test_squadupgrade 45 · test_squad_evidence 51 · test_processlint 31 -- all OK
SQ-10 trio: test_windows_safe 14 OK · test_utf8_helpers 14 OK · test_instructions 16 OK
```

## Review

Fresh-context reviewer (sonnet, high) on `2033fa8..19b1f8a`, Standards and Spec axes, ran both new test files. Spec: AC1-AC3 and AC5 met by code and tests. Standards: none. Findings: none. Edge cases it checked: CRLF, a trailing `(note)`, a blank or missing `team:`, an invalid token (falls back to the old behaviour), a goal home (no scope.md, old fallback), an int task id. One nit left as is: `checkers` now reads `scope.md` on each call (one small file read).

## Checks

| AC | Dev: test or capture |
|---|---|
| AC1 | `test_checkers_of_a_team_without_qa_ignore_retired_rows` OK; real scope gives `{'qa': []}`, `['evidence']` |
| AC2 | `test_hook_records_evidence_pass_for_a_no_qa_team_with_retired_qa_rows` OK |
| AC3 | `test_no_qa_team_evidence_pass_is_ok_and_a_rule_id_row_is_no_ticket` OK |
| AC4 | `test_squadboard_tasks`, `test_squad_watchdog`, `test_squadplan` OK |
| AC5 | plugin.json count 1; `## v32` on top; `squad-process lint` exit 0 |

## Changelog line

`squad-task` checkers and `squad-merge-check` (15): when no QA row is live and `scope.md` has a decided `team:` with no `qa-white` or `qa-black`, the only checker slot is `evidence` (the HANDIN hook's evidence PASS counts), and `squad-merge-check` skips old rows keyed by a rule id such as `SQ-10`. why: it refused a passed branch because it wanted PASSes from the retired QAs and read a rule id as a ticket.
