# Evidence: 10 drafts never in the project root

**`squad-path-guard` refuses Write/Edit/MultiEdit/NotebookEdit by every non-Developer role in the project root outside `.claude/squads/`; FILE-11 and MRG-5 say so; `squad-close --scope` warns on untracked root files and still closes. 164 tests green; dev rules byte delta 0.**

Harness: `cd tests; python3 -m unittest test_squad_path_guard test_hooks_json test_squad_close test_windows_safe` OK. Also: test_dev_rules_size, test_process_conversion, test_processlint, test_pod_rules_process, test_process_citations, test_task_id_rule, test_suite_rules_process, test_team_lead_perms, test_templates (164 OK together).
sha: see the HANDIN (code ed9d10a + fixes of the agreed Technical AC)

## Behaviour

**AC1/AC2/AC3/AC4** live CLI probe, `guard-probe.txt` (`bin/squad-path-guard` fed the hook JSON on stdin):
- tech-lead writes `<root>/.scratch/x/issues/01-a.md` → exit 2, stderr `draft it in <SCOPE_DIR>/tasks/; a Developer task commits it [FILE-11]`.
- tech-lead writes `$SCOPE_DIR/tasks/01-a.md` → exit 0. Under `.claude/squads/` → exit 0 (`test_squad_folder_is_allowed_for_every_role`).
- dev writes in the root/worktree → exit 0; no `SQUAD_ROLE` (PO) → exit 0.
- manager, ba, team-lead, qa-whitebox, qa-blackbox, designer, token-coach each write `<root>/x.md` → each exit 2.

**Tech AC1 decision table** `test_squad_path_guard.GuardTest`: role × squad folder / root / outside / developer worktree / no role; `..` and symlinked paths resolved; relative path against payload `cwd`; `notebook_path`; sibling dir with the same prefix (`proj-other`) allowed; missing `SQUAD_DIR`, target or payload → allow. `CliTest`: exit 2 + stderr; garbage stdin (`not json`, empty, `[1]`, `null`) and missing `SQUAD_DIR` → exit 0.
- Known limit: a Bash redirect bypasses the guard; FILE-11 says so and `squad-close` is the backstop.

**Agreed Technical AC (ticket-amendments, last section)**: tests use the real `SQUAD_ROLE` values (`test_tools_and_real_role_values`: Write, Edit, MultiEdit, NotebookEdit × tech-lead, qa-whitebox, qa-blackbox, team-lead, token-coach); a not-yet-existing target resolves through its symlinked parent (`..does_not_exist_yet..`); a symlink in the squad folder to the root is blocked; Windows case and separators normalised (`test_windows_case_and_separators_are_normalised`, `ntpath`: `c:/proj`, `C:\\PROJ`, `.CLAUDE\\Squads`, other drive, sibling prefix). The guard is Python: no `jq` dependency. **Accepted limit: a Bash redirect (`echo > file`) is not covered.** Forced failures with exit 0: garbage payload, missing `SQUAD_DIR` (`CliTest`).

**Tech AC2** `test_one_realpath_and_no_git_call` (QA whitebox FAIL fix: the root is resolved like the target, so a symlinked root compares equal; `test_a_symlinked_project_root_compares_equal_whichever_spelling_is_used` covers both repros): two `realpath(` calls (target and squad folder), no subprocess/socket/urllib/git in the code.

**Tech AC3** `hooks.json` valid; `test_hooks_json.test_path_guard_on_the_write_tools_only` covers the single `PreToolUse` entry (matcher `Write|Edit|MultiEdit|NotebookEdit`) and that the script exists.

**BA AC5 / Tech AC4** `test_squad_close.ScopedCloseTest.test_scope_close_lists_untracked_root_files_and_still_closes`: untracked `.scratch/x/issues/01.md` → printed under `WARNING: untracked files in the project root ...`, exit 0, the scope folder is archived. `.claude/squads/` and `.worktrees/` entries are not listed. `..._without_stray_files_prints_no_warning`: no warning when the root is clean.

**BA AC6** `squad-process who FILE-11` → acts: tech-lead, ba, team-lead, manager, qa-whitebox, qa-blackbox, designer, token-coach (all 8 composed outputs contain it, checked with `compose`); `who MRG-5` → manager. FILE-11 is 55 words (lint limit 60).
- **Developer rules: byte delta 0** (dev composed at S/design yes/goal yes = 5106 B before and after; cap 5120). Dev is not in FILE-11's roles: the cap leaves no room; Tech Lead ruled (a) in `ANSWER 10`: the Developer learns "commit the drafts" from the task text. `test_dev_rules_size` green.
- Deviation from `ticket-amendments.md` (roles = tech-lead, ba, team-lead): FILE-11 names all non-Developer roles, following `business-ac.md` §10 rulings 1 and 4, which win on behaviour.

**MRG-5** (manager): before a merge, run `git status --porcelain --untracked-files=all` in the root and tell the PO about every untracked file outside `.claude/squads/`.
