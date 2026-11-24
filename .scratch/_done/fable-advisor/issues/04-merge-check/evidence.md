## Behaviour

`squad-merge-check <branch-or-sha> [--base REF] [--scope DIR]` (new `bin/squad-merge-check` + `bin/squadmergecheck.py`).

Reused (T3): `squadtask.fold/read_events/slug_of/squad_dir_of/checkers/slots/is_passed/_same_sha` for task states and PASS shas; the evidence-only rule of `squadevidence.is_evidence_path` (same logic, ticket `.md` looked up in the git ref, not on disk).

Read-only: `grep -n "write\|open(" bin/squadmergecheck.py` has no hit; git runs as a list with `--no-optional-locks`; no `shell=True`.

## AC trace

| AC | Test | How run |
|---|---|---|
| AC1 lines | `test_ok_main_moved_no_shared_file_and_read_only` (ancestor, log, passed, dirty, untracked, main-moved, siblings labels) | `cd tests && PYTHONPATH=. python3 -m unittest test_squad_merge_check` |
| AC2 VERDICT last line | every test asserts the last line | same |
| AC3 never writes, exit 0/1/2 | same ok test (HEAD, refs, status, branch equal before/after); `test_usage_errors_and_no_injection` | same |
| AC4 ok / dirty / not passed / main moved related | `test_ok_...`, `test_dirty_root_refuses`, `test_sha_not_passed_refuses`, `test_main_moved_with_related_files_refuses` | same |
| T5 evidence-only after pass | `test_evidence_only_commit_after_pass_is_ok` | same |
| T5 shared test hit | `test_main_moved_shared_test_hit_only_refuses` | same |
| T7 untracked = warning, injection | ok test (warning line); `x;touch pwned` exit 2, nothing created | same |
| T4 real sample | copy of `task-claim-gates.jsonl` (ticket 09 with a return, FAIL only): `fold` parsed both tickets, tool ran, `refuse: sha not passed` | manual, copy under mktemp |
| T8 | `test_squad_merge_record test_squad_evidence test_no_bare_bash test_hooks_json` | 59 tests OK |
