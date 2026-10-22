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

## QA whitebox review

### QA whitebox: ticket 10 @ 6032595 (base 4901cab)

Verdict: **FAIL** (1 must-fix)

Ran: `test_squad_path_guard test_hooks_json test_squad_close test_windows_safe test_dev_rules_size` = 79 OK; `squad-process lint` exit 0. `bin/squad-path-guard` is mode 755, Python, no jq; FILE-11 / MRG-5 text and the `PreToolUse` entry in `hooks.json` match the ticket; `squad-close` warning is warn-only and excludes `.claude/squads/` and `.worktrees/`. FILE-11 names all non-dev roles (BA ruling §10 wins over the amendment; the later agreed AC only excludes dev): accepted.
I also fed the guard 10 payloads by hand (relative path, trailing-slash SQUAD_DIR, outside project, dev, symlink inside the squad folder → root, `.worktrees/`, `notebook_path`): all as specified.

#### Must fix
1. `bin/squad-path-guard:decide`: the project root comes from the unresolved `SQUAD_DIR` (comment: "given by the path, not resolved again") while the target is `realpath`ed. When the root path contains a symlink the two disagree.
   - Repro A (false block, traps the agent): `/tmp/gx/link -> real`, `SQUAD_DIR=/tmp/gx/link/.claude/squads/s`, role tech-lead, `file_path=/tmp/gx/link/.claude/squads/s/scopes/x/tasks/a.md`, `cwd=/tmp/gx/link` → exit 2 "draft it in …/tasks/" although that is exactly where the draft belongs.
   - Repro B (bypass): same `SQUAD_DIR`, role ba, `file_path=/tmp/gx/real/.scratch/a.md` (the real path of the root) → exit 0, write allowed.
   - Amendment said "root … resolved with one realpath". Pass: resolve the root (`realpath` of the squads parent, or of `SQUAD_DIR`) before comparing, both inside `decide`; update `test_one_realpath_and_no_git_call` to the real count (still no git or network call); add a test with a symlinked root for A and B (squad-spawn / Claude `cwd` may be either spelling).
#### Notes
2. Cosmetic: with a trailing slash in `SQUAD_DIR` and `SCOPE_DIR` the message shows `//` (only `SCOPE_DIR` is echoed raw; fine).
3. Known limit stated in evidence (Bash redirect not covered) matches the agreed AC.

#### Re-check @ 0f1a68c (diff 6032595..0f1a68c: guard, its test, evidence)
Verdict: **PASS**. Finding 1 fixed: the squad folder is now `realpath`ed like the target (2 realpath calls, test updated). Re-ran my repros: A (tech-lead, symlinked root, tasks/ draft) exit 0; B/B2 (ba, root file via either spelling) exit 2; symlink in the squad folder to the root exit 2; outside project exit 0. 74 tests OK (guard, hooks_json, windows_safe, squad_close).

## QA blackbox review

### QA-b 10 (sha 6032595, branch squad/plugin/process-fixes/plugin-dev-pf-1)
Ran `bin/squad-path-guard` (hook JSON on stdin) and `squad-close` in a temp project (git repo, `.claude/squads/t/scopes/s`, `.worktrees/w1`, symlinks); no code read.

| AC | What I did | Saw | Result |
|---|---|---|---|
| 1 | tech-lead writes `<root>/.scratch/x/issues/01-a.md` | exit 2, stderr `draft it in <SCOPE_DIR>/tasks/; a Developer task commits it [FILE-11]` | pass |
| 2 | tech-lead writes `$SCOPE_DIR/tasks/01-a.md`, `.claude/squads/t/x.md`; `/etc/passwd`, outside-root file | exit 0 each | pass |
| 3 | dev writes `.worktrees/w1/a.py`, `<root>/.scratch/x/a.md`; no `SQUAD_ROLE` | exit 0 each | pass |
| 4 | manager, ba, team-lead, qa-whitebox, qa-blackbox, designer, token-coach write `<root>/.scratch/x/issues/01-a.md` | exit 2 each, same message | pass |
| 4b | non-dev in `.worktrees/w1`, `src/a.py`, `README.md`; `..` path into root; symlink inside the squad folder pointing into root; symlink in root leading out; `notebook_path`; relative path; `{}` and garbage stdin | root/worktree/`..`/symlinks/relative/notebook: exit 2; `{}`/garbage: exit 0 (no crash) | pass |
| 5 | `squad-close t --scope s` with untracked `.scratch/x/issues/01.md`, `stray.txt` (+ an untracked file inside `.claude/squads/`) | `WARNING: untracked files in the project root outside .claude/squads/ (…FILE-11):` lists the two root paths only; close archived to `_done/s`, exit 0. `--dry-run` also warns. Clean root: no warning. Ignored file not listed; new `src/new.py` listed | pass |
| 6a | `squad-process rule FILE-11`, `who FILE-11`/`MRG-5`; compose of all 8 non-dev roles at M | FILE-11 in all 8 composed files; MRG-5 manager only | pass |
| 6b | compose `dev` at M: grep draft/tasks/root | **0 matches**: Developer rules carry no "first Developer task commits drafts" | accepted: BA FINAL amended AC6 to non-Developer roles |
| Tech | hooks.json valid JSON, `squad-process lint` rc 0; 5 guard calls = 0.08 s | | pass |

Gap 6b: business-ac §10 AC6 says the Developer's rules say the first Developer task commits drafts. Dev disclosed (evidence.md): Developer rules at their size cap (5106/5120 B), Tech Lead ruled the Developer need not carry it. Asked the BA to rule; verdict below.

#### Verdict
PASS on 6032595. 6b: BA FINAL amended AC6 (Developer gets the draft-commit instruction in its task file).
