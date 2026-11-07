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
