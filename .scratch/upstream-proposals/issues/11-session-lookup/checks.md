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
