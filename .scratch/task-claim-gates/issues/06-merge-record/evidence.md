# Evidence 06

## Behaviour

Hook run in a temp git repo and a temp squad folder (never the real store). A claim exists for ticket 06 on `squad/plugin/s1/dev`; the Manager runs `git merge --no-ff squad/plugin/s1/dev`:

```
event: ev=merged task=06 by=mgr role=manager branch=squad/plugin/s1/dev sha=<HEAD of the merge> warn=["W7 merged before it passed"]
hook stdout: additionalContext "task state warning: W7 merged before it passed"   exit 0
```

A ticket that already passed merges with no warning and no stdout. A second run adds no second event. A non-Manager role, a command that is not a merge, a branch not in `HEAD` (merge did not land) and a branch no ticket owns write nothing. `squad-task merged NN` stays the manual fallback.

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC6 record side (branch merged, `merged` event with branch, sha, time) | `test_manager_merge_records_merged_with_w7_when_not_passed` | `cd tests && python3 -m unittest test_squad_merge_record` |
| W7 (merged before it passed; in event and in `additionalContext`) | same test; `test_passed_ticket_merges_without_warning_and_once` for the no-warning side | same |
| T1 (exit 0 always, hook never fails) | `run_hook` asserts exit 0 in all three tests | same |
| T11 (targeted tests) | `test_hooks_json`, `test_utf8_helpers`, `test_squadruntime`, `test_old_language_inventory` (grep hits for `hooks.json`) | `cd tests && python3 -m unittest <name>` |
| Hook entry (PostToolUse, matcher Bash) | `hooks/hooks.json`; `test_hooks_json` | same |

## QA whitebox

### QA whitebox, ticket 06 (merge record hook), sha f56f18a (base 125e654)

Technical AC: ticket's own T1, T11; design.md s5.3; T23 (temp store); T2/T12 style (stdlib, no top-level fcntl: it only imports squadtask).
Run by me: `cd tests; python3 -m unittest test_squad_merge_record test_hooks_json test_utf8_helpers test_old_language_inventory` = 23 OK. hooks.json parses; `bin/squad-merge-record` is mode 100755 in git. Diff = the ticket's Files line (+ evidence).
Code read: prefilter (role manager, `git merge` and `squad/`) before python; branch tokens; merged only when the branch is an ancestor of HEAD (or ref gone and no failure text); events found by `branch` in all task-events/*.jsonl; already-merged skipped (idempotent); written through squadtask.record (W7 in event and additionalContext); always exit 0.
REV-5b live (temp squad + temp git repo, real git): `git merge-base --is-ancestor ...` with the branch not in HEAD records nothing; after a real merge and the branch deleted (`git merge ... && git branch -d ...`) one `merged` event + W7, rc 0. Temp dir removed. No write to the real store.

#### Verdict: PASS

#### Follow-ups (not blocking, SQ-4)
1. `failed()` reads tool_response text/exit fields that no real PostToolUse sample backs (REV-4). It only matters when the branch ref is gone; the main path is git state, which I ran live. A failed Bash call fires no PostToolUse anyway.
2. The regex also matches `git merge-base ...`; harmless (needs the branch already in HEAD, then `merged` is true in git), but it can stamp `merged_ts` at the time of a later `git merge-base`/other command instead of the merge. Tighten with `merge(?![-\w])` if wanted.
3. Squash merge (branch not an ancestor) records nothing; design D6 says use `squad-task merged NN` (MRG-4 text in task 05).
4. `git -C <dir> merge` runs git in the payload cwd, not `<dir>`.

## QA blackbox

### QA blackbox verdict, task 06, sha f56f18a. VERDICT: PASS

Method: `live`. Scratch git repo + scratch squad folder `<temp>/sq2/scopes/s1` (same layout as a real squad; real store untouched). Claims made with `squad-task claim --branch`, merges done with real `git merge --no-ff`, the PostToolUse hook `bin/squad-merge-record` fed the hook JSON on stdin with `SQUAD_ROLE` set. Judged on states.md AC6 (record side), W7, AC14.

| AC | live: what I did | what I saw | result |
|---|---|---|---|
| AC6 | Manager merge of the branch of ticket 81 | `merged` event written, `squad-task show 81` = `merged`, rc 0 | pass |
| W7 | same, 81 had no PASS | hook stdout `additionalContext` "task state warning: W7 merged before it passed"; also on the row note | pass |
| AC6 no warning | ticket 82 passed (both QA PASS, manual run), Manager merge | `merged`, no hook output, no W7 | pass |
| once | same merge command run a second time | no second `merged` event (2 merged events for 2 tickets) | pass |
| role | merge of ticket 83 by role `dev` | nothing recorded, row stays `in progress` | pass |
| not a merge | `git log <branch>`; `git merge <branch>` where branch not in HEAD | nothing recorded, rc 0 | pass |
| unknown branch | Manager merge of a branch no ticket owns | nothing recorded, rc 0 | pass |
| AC14 / T1 | all runs above, plus garbage JSON on stdin | exit 0 every time | pass |

Follow-ups (none breaks an AC):
1. The hook finds the ticket only through a claim that recorded the branch (spawn claim or `squad-task claim --branch`). A claim with no `--branch` is not matched; `squad-task merged NN --branch/--sha` is the fallback.
2. In a flat scratch layout (scope dir not under `scopes/`) `squad-task` and the hook write different stores. In a real squad layout they agree. Not a real-team case.
3. Not tested: board display of `merged` from another scope (task 03).
Temp dir left for Chieu: /tmp/tmp.7havK7FUUb (rm refused).
