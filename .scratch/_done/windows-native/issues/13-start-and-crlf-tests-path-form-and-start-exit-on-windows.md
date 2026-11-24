Status: ready-for-agent

# 13 Windows failures left after 03b1 in test_squad_start and test_crlf_squad_files (no launch errors)

Seen at integration sha 4b74d89, Windows 11, `cd tests && python -m unittest test_squad_start test_crlf_squad_files` (test_squad_start takes about 4 min on Windows). 0 `WinError 193`, 0 `TypeError`. 17 failures in A-D, plus E (not reproduced). The 18th failure (test_utf8_helpers label `Dev` vs `Dev 2`) is ticket 12.

## A. Path form: expected backslash path, tool prints forward slash (4 tests)
Expected text has `SCOPE_DIR=C:\Users\...\scopes\one` (native path), the herdr log has `C:/Users/.../scopes/one`.
- `StartTest.test_goal_prefix_creates_a_goal_folder_and_a_goal_manager`
- `StartTest.test_lone_task_creates_the_scope_folder_brief_and_a_fresh_manager`
- `StartTest.test_resume_a_goal_uses_goal_dir`
- `StartTest.test_resume_starts_a_new_manager_for_an_existing_scope_without_touching_its_files`

## B. Path form: crlf vs lf fixture name in dry-run output (3 tests)
Output holds `.../crlf/.claude/...`, expected `.../lf/...`: the test swaps the fixture folder name with a path form that does not match on nt.
- `CrlfReadersTest.test_close_scope_dry_run`
- `CrlfReadersTest.test_spawn_dry_run_reads_goal_and_design` (role `dev` and role `designer`, 2 subtests)

## C. `squad-start` exits 1: `/usr/bin/env: 'bash': No such file or directory` (5 tests)
`1 != 0 : could not start the Manager`. `squad-start` runs `squad-spawn` (shebang `#!/usr/bin/env bash`); the test PATH has no bash directory, so `env` cannot find bash. The resume subtest then says "no open scope or goal named one" (follows from the first start failing). Fix direction: the tests' PATH keeps the directory of `winlaunch.bash()`.
- `LauncherTest.test_a_c_locale_with_an_emoji_label_runs_clean_and_writes_utf8_lf`
- `LauncherTest.test_a_project_dir_with_a_space_and_an_emoji_works_for_new_and_resume`
- `LauncherTest.test_new_scope_and_resume_run_squad_spawn_through_bash` (2 subtests: new scope, `--resume`)
- `LauncherTest.test_no_bash_is_one_line_and_nothing_is_written_for_a_new_scope_and_for_resume`

## D. Fake herdr never called: ticket 12 class (5 tests)
`calls()` is empty (`[] != ['workspace rename wK one']`), or the refusing-herdr warning count is 0. Same cause as ticket 12 (extensionless bash stub). Named there too.
- `WorkspaceRenameTest.test_a_goal_names_the_workspace_after_the_goal`
- `WorkspaceRenameTest.test_a_lone_scope_names_the_workspace_after_the_scope`
- `WorkspaceRenameTest.test_a_refusing_herdr_gives_one_warning_and_the_start_goes_on`
- `WorkspaceRenameTest.test_resume_renames_to_the_resumed_name`
- `WorkspaceRenameTest.test_two_starts_in_a_row_each_rename`

## E. Seen once by QA-b, not reproduced (1 test)
`test_utf8_helpers.LabelAndSpawnTest.test_spawn_dry_run_and_stubbed_run_for_every_role` (role `token-coach`) failed in QA-b's run on 4b74d89. It passed in the Developer's 5-file run and in two more runs of `test_utf8_helpers` alone (only the ticket-12 label test failed). Likely load or timeout; if it shows again, start from its stderr.

## Done when
`python -m unittest test_squad_start test_crlf_squad_files` has no failure from A, B, C, D on Windows, and Linux counts are unchanged with no new skip.

## Comments
