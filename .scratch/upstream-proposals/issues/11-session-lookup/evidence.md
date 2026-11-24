# Evidence 11: hooks find a resumed session in roster.md

## Behaviour

Base 4e7d547. Fixtures: two real rosters copied from this squad, `tests/fixtures/session_lookup/scope-roster.md` (scope upstream-proposals, sha1 73ff4b154d3cee312c0c04aff436156c9b5d3f8d) and `goal-roster.md` (goal process-fixes, a goal Manager row, sha1 dd14d6179261d88255e7f66c7146f699804f5959).

**Tests** (`SQUAD_*` unset in the shell; `PYTHONDONTWRITEBYTECODE=1`): `python3 -m unittest` over the 19 files = the new `test_session_lookup`, `test_windows_safe`, `test_utf8_helpers`, `test_instructions`, `test_hooks_json`, the eight hook tests and every `grep -rl` hit of the hook and helper names over `tests/`: **Ran 362 tests, OK** (a `squad-notify: cannot write /dev/pts/999999` line is that test's own log). `python3 bin/squad-process lint`: exit 0. No `bin/*.pyc`.

**Resumed session keeps its id (AC11 limit).** Real payloads of one scratch session, `claude -p --session-id <id>` then `claude -p --resume <id>`, a `UserPromptSubmit` hook logging stdin, both calls carry the same `session_id` (copy: `resume-payloads.jsonl`):
```
{"session_id":"e019806c-8ccc-4a8d-aba6-a96a662c0cf1", ... "hook_event_name":"UserPromptSubmit","prompt":"reply ok"}
{"session_id":"e019806c-8ccc-4a8d-aba6-a96a662c0cf1", ... "hook_event_name":"UserPromptSubmit","prompt":"reply ok again"}
```
So the roster's Session cell still matches after `--resume`.

**Cost (AC8).** `squad-whoami` in the real project, 7 runs each: a session id with no row (the PO's own session) median 39 ms, max 42 ms; this Developer's id (row found) median 37 ms, max 44 ms. A session with the variables starts no `squad-whoami` (stub test).

## Checks

<!-- AC table: Dev column filled; QA columns are theirs -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `test_resumed_session_logs_as_its_roster_row` (real `bin/squad-log-message`): ok | | |
| AC2 | `test_unknown_empty_or_unreadable_session_stays_silent`: ok | | |
| AC3 | `test_environment_wins_over_the_roster`, `test_environment_wins`: ok | | |
| AC4 | `ResolveTest` (8 tests: worktree cwd, git worktree, goal Manager, goal of a scope, flat, `_done`, substring, bad name): ok | | |
| AC5 | `test_resumed_qa_is_stopped_by_the_path_guard_and_a_resumed_dev_is_not`, `test_resumed_manager_is_covered_by_the_manager_guard`: ok | | |
| AC6 | `test_every_squad_hook_of_hooks_json_calls_the_lookup`: ok | | |
| AC7 | fixtures `tests/fixtures/session_lookup/scope-roster.md` (sha1 73ff4b15), `goal-roster.md` (sha1 dd14d617): ok | | |
| AC8 | `test_a_session_with_the_variables_starts_no_squad_whoami`; timing in `## Behaviour` (about 40 ms): ok | | |
| AC9 | SQ-10 three files and every grep hit: see `## Behaviour` | | |
| AC10 | `squad-process lint` exit 0; `git diff --stat` lists only the allowed files | | - |
| AC11 | resumed-session payload quoted in `## Behaviour`; the scratch-squad run is QA blackbox's | - | |
