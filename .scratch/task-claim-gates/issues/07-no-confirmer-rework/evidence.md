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

## QA whitebox review

### QA whitebox, ticket 07 (task 01 rework: no confirmer, no-QA evidence path)

#### Technical AC (agreed text: tasks/design.md s8 after E3/E4, Tech Lead DECISION 01, 07)
Bar = design.md s8: T1, T2, T3, T4, T5, T6, T8, T11, T12 as written; T13 (parse_handin additive); T14 (only task-events/<slug>.jsonl written, now also by `passed` override); T15, T16, T17; T18 (CLI exit 2, must cover `passed NN` and `pass NN --slot`); T19 (no-QA evidence hook, real temp git repo); T20 (no squad-evidence call with a QA; PASS from manager/team-lead/tech-lead = W4, no event; FAIL from any sender recorded); T21 (Blocked-by leading numbers only); T22 (squad_dir_of for scopes/_done); T23 (tests and hand checks use a temp squad, never the real task-events); T24 (no-QA word `in progress` or `passed`, never `checking`; retired QAs still count; `override` PASS).
Rules: old os.path code in squadledger.py is not a return reason. No pre-written test points (LC-4). Ticket's own Technical AC line lists only T8, T19, T20, T1, T6; T21-T24 and T14/T18 changes came by DECISION: a gap there is a follow-up, not a FAIL, unless the Developer was handed them (Team Lead's ticket text decides).
REV-5b live run: once in a temp squad with a temp git repo, no-QA HANDIN calls `squad-evidence check`.
Per-ticket check: re-check only changed files and AC (LC-3b); base for the diff = 64b0785.

#### Verdict e3459f2 (base 64b0785): PASS
Run by me: `cd tests; python3 -m unittest test_squadtask test_squad_ledger` = 32 OK (no skips). Diff = bin/squadtask.py, bin/squad-task (docstring), tests/test_squadtask.py, ticket/evidence files; matches the ticket's Files line.
Code read: confirmer code gone (CONFIRM_ROLES, _team_tokens, squadrules import); checkers/slots/is_passed per D7 (retired-all QAs still count; override PASS); word() never `checking` with no QA; W4 for non-QA PASS, FAIL from any sender recorded; W6 only on override; W7 text; W9 on handin event and in output; evidence_check has no --base, needs HEAD == handed-in sha, never raises; squad-evidence is not started when a QA is on the roster (test stubs it); parse_blocked_by leading numbers; squad_dir_of `_done`.
REV-5b live (temp SQUAD_DIR, temp git repo as worktree, real `squad-evidence check`): no-QA HANDIN with valid evidence -> `pass` slot evidence, word `passed`, W3 only. `passed abc` and `pass 01 --slot` (no value) exit 2. Only task-events/s1.jsonl (+ .lock) written. Temp dir removed.
Technical AC: T1, T6, T8, T19, T20 (ticket's own list) ok; T21, T22, T24 ok in code and tests; T23 ok (all tests temp squad).

#### Follow-ups (not blocking, SQ-4)
1. T18: `test_cli_claim_exit_codes` does not cover `passed NN` / `pass NN --slot` exit 2 (code does it, I ran it by hand). Add one row.
2. T14: no snapshot test that the `passed` override writes only task-events/<slug>.jsonl (code reads that way).
3. Still open from 01: T15/T16/T17 tests; 6+ digit number false W5; Tech Lead's call on the dropped tech-lead FAIL is now moot (FAIL from any sender is recorded).
4. `evidence_check` falls back to the hook's cwd when the worktree dir is not found; HEAD check guards it, fine.
