# Evidence 07

## Behaviour

Hand check in a temp squad folder (never the real store), roster with no QA:

```
recorded handin 07            warning: W3 handed in without a claim; owner taken from sender
recorded pass 07              warning: W6 passed by hand; evidence check not ok     (squad-task passed)
not recorded                  warning: W4 not a checker; not counted                (squad-task pass, no QA role)
07  passed  owner dev  sha abcdef1 ...
```

No-QA HANDIN runs `squad-evidence check` with no `--base` in the worktree of the branch; exit 0 records a `pass` (slot `evidence`, by `hook`). A failure is W9 on the handin event and in `additionalContext`; no pass.

## Review

| AC | Test or capture | How run |
|---|---|---|
| W4 (PASS from manager, team-lead, tech-lead) | `test_pass_from_non_qa_is_w4_and_fail_from_anyone_counts` | `cd tests && python3 -m unittest test_squadtask` |
| W6 (override, checks missing) | `test_w1_to_w8...` (QA team), `test_override_and_tip_moves_check_again` (no QA) | same |
| W7 text "merged before it passed" | `test_w1_to_w8...` | same |
| W9 | `test_missing_image_is_w9_on_event_and_output_no_pass`, `test_head_not_the_handed_in_sha_is_w9_not_checked` | same |
| AC3 (checking, 1 of 2 PASS) | `test_sender_role_comes_from_the_roster...` | same |
| AC4 (no QA: passed on exit 0, in progress + W9 on failure) | `test_valid_evidence_passes_with_no_message`, `test_missing_image...` | same |
| AC5 (every QA PASS: passed, no Manager PASS) | `test_sender_role_comes_from_the_roster...` | same |
| AC20 (tip moves, next HANDIN re-checks; word `sha changed` is the board's) | `test_override_and_tip_moves_check_again` | same |
| s4 (never `checking, 0 of 0`) | `test_words_and_label_table`, `test_missing_image...` | same |
| T8, T24 | `test_checkers_and_slots` | same |
| T19 (real temp git repo) | `NoQaEvidence` class | same |
| T20 (QA on roster: evidence never started; FAIL from anyone counts) | `test_pass_from_non_qa...` | same |
| T21, T22 | `test_blocked_by_leading_numbers_and_done_scope` | same |
| T23 | all tests use a temp squad folder; hand check used `--scope-home <temp>` | above |
| T1, T6 | `test_hook_entry_warns_and_never_fails`, `test_w1_to_w8...` | same |

Run: `python3 -m unittest test_squadtask test_squad_ledger` in `tests/`: 32 tests OK.
