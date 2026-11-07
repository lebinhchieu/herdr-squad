# Evidence 02

## Behaviour

`squad-spawn dev <name> --repo R --task 03` writes one `claim` event after the pane is up (temp squad, fake herdr). `squad-log-message` hands each message record to `squad-task from-message` and joins its warnings into `additionalContext`.

Real run in a temp squad (QA team, no claim; `squad-log-message` fed three payloads, then `squad-task show`):

```
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"task state warning: W3 handed in without a claim; owner taken from sender"}}
[dev-1] HANDIN 02: branch squad/sq/sc1/dev-1, commit abc1234 -> exit 0
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"task state warning: W4 not a checker; not counted"}}
[mgr] PASS 02: ok -> exit 0
[qa-w] PASS 02: ok abc1234 -> exit 0
02  passed  owner dev-1  sha abc1234  returns 0  W3 handed in without a claim; owner taken from sender
```

The claim, no-QA evidence pass, hand-off and failure cases are in the tests below (fake herdr, temp git repo).

Pinned hand-off: the args passed to an old runtime have no `--task`; env `SQUAD_SPAWN_TASK=03` carries it. `--worktree` (a respawn) writes no claim. A broken `squad-task` (exit 9) does not fail the spawn; a store that cannot be written does not fail the hook (exit 0, message still logged).

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC2 (spawn claims, owner, branch) | `SpawnTaskClaimTest.test_task_claims_the_ticket_for_the_agent_and_its_branch` | `cd tests && python3 -m unittest test_squad_spawn.SpawnTaskClaimTest` |
| AC3, AC5 (QA PASS recorded by slot; non-QA PASS is W4, no event) | `test_qa_team_records_handin_pass_fail_blocked_and_warns_by_context` | `cd tests && python3 -m unittest test_squad_log_message` |
| AC4, AC20, W9, T19 (no QA: pass by evidence check; failure W9; next HANDIN re-checks) | `test_no_qa_team_valid_evidence_passes_and_a_missing_image_is_w9` | same |
| AC8 (claim with open `Blocked by:` is recorded with W1, not refused) | `SpawnTaskClaimTest.test_claim_with_an_open_blocker_is_recorded_with_w1_and_never_refused` | spawn file |
| T1 (exit 0 on warning, store error, claim failure) | `test_a_store_that_cannot_be_written...`, `test_a_bad_task_value_is_refused_and_a_claim_failure_never_fails_the_spawn` | the two files above |
| T5 (real samples incl. a `..sha` HANDIN and a FAIL naming a sha; PASS with no sha; ASK and `evidence sha` write nothing) | `test_pass_with_no_sha_and_ask_and_evidence_sha_handin_write_what_they_should` | log-message file |
| T7 (dry-run writes nothing; owner and branch; `--worktree` no claim; no `--task` to runtime) | `test_dry_run_plans_the_claim...`, `test_env_task_claims_too_and_a_worktree_respawn_does_not_reclaim`, `test_the_hand_off_drops_task_from_the_args_and_passes_it_as_env` | spawn file |
| 3rd-return notice still works, shares the context | `test_the_third_return_notice_and_the_task_warning_share_one_context` + 2 existing notice tests (now with a QA row) | log-message file |
| T11 | targeted: the 2 touched files + 10 `grep -rl` hits (respawn, windows_safe, crlf, ledger, start, winlaunch, manager_guard, rules_contract, squadruntime, utf8_helpers): 231 tests OK; then 8 more hits by hand (old_language_inventory, rules_wording, instructions, templates, squadsettings, team_lead_perms, team_models, squadreport_digest): 105 tests OK. `run_suite.py --if-changed` hung 59 min on `test_squadboard_inbox` (not touched by this diff) and was stopped by PID; that file was not run | `python3 -m unittest ...` in `tests/` |

Changed existing test: `test_the_notice_is_stdout_json_on_the_third_failing_sha_only` now asserts `has 3 returns` in stdout instead of empty stdout, because task-state warnings (W3) share that output by design (D4); both 3rd-return tests also got a QA roster row.

Known, not mine: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` fails on 125e654 too (checked with my diff reverted).
