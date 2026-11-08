# 03 squad-spawn / squad-respawn do not depend on the inherited account

Status: ready-for-agent
Slug: spawn-passes-account
Duties: design notes = Developer (in this file); technical AC = QA whitebox with the Developer; business AC = the ticket as written; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; full suite and promote.md = QA whitebox (full suite only after Chieu's yes via the Manager). A risk flag, user-visible change or business doubt found while building: BLOCKED to the Manager.

Brief: `scope.md` and `iterations/1.md` in this scope folder. Source of the bug: `C:/Users/84084/workspace/Guardian - Learn/.claude/squads/lastvil/goals/buildings-allies/claude-accounts-handoff.md` (read only).
Confirmed by the PO: in a herdr workspace whose default is c1, `echo $env:CLAUDE_CONFIG_DIR` in a new tab prints `...\.claude-3`; in c2 and c3 workspaces it is right. So a new shell inherits `CLAUDE_CONFIG_DIR` from the herdr server and nothing clears it for account 1.
Tests: test_ca_win, test_ca_install, test_ca_launchers, test_ca_autoswitch as touched (see CLAUDE.md > Running tests). Never run `install.sh` on the live `~/.claude-accounts`; use the temp HOME harness `tests/ca_stubs.py`.
Ticket path to commit this file to: `.scratch/c3-default-fix/issues/<NN>-<slug>.md` (first task also commits the other two; add `Status: ready-for-agent`).

Files: `bin/squad-spawn` (the `herdr tab create ... --env` block around line 454 and the `claude` start around line 492), `bin/squad-respawn`. Design note first. `herdr tab create --env` can set a variable but cannot remove one, so for account 1 the new pane still depends on task 01. Decide the smallest safe option and write it in the design note: (a) pass `--env CLAUDE_CONFIG_DIR=<dir>` for default 2/3 and for default 1 type `env -u`/`Remove-Item` handling where possible; or (b) no change, with the reason. BLOCKED to the Manager before building if (a) needs more than about 20 lines or changes behaviour on non-Windows.

AC
1. A pane spawned while the effective default is 2 or 3 gets that account's `CLAUDE_CONFIG_DIR` even if the herdr server env holds another one (dry-run output or stub-herdr test shows it).
2. Behaviour for default 1 is unchanged or fixed, as the design note says; no regression in `--dry-run` output of other spawns.
3. Tests: the existing `squad-spawn` test file(s) found with `grep -rl squad-spawn tests/`, run all hits.

## Technical AC (QA whitebox, proposed to the Developer; reply in this file or by ASK if you disagree)
T1. The design note states option (a) or (b) with the reason and the line count. Over about 20 changed lines, or any non-Windows behaviour change: BLOCKED to the Manager before building.
T2. If (a): the account lookup is one shared helper or one shared snippet used by both `squad-spawn` and `squad-respawn`, not two copies. Default 2/3 passes `--env CLAUDE_CONFIG_DIR=<dir>`; default 1 passes no `CLAUDE_CONFIG_DIR` env and never `~/.claude`.
T3. Quoting: a dir with a space (Windows `C:\Users\...` home) reaches `herdr tab create` as one argument. Show it in a stub-herdr or `--dry-run` output.
T4. If the default is read by parsing a file or tool output (the workspace/global default), `evidence.md` holds two real samples, including the unset/idle case (REV-4), and the code handles a missing file and an unknown value without crashing the spawn.
T5. `--dry-run` output for a default-1 spawn is identical to base (diff in `evidence.md`); for 2/3 the only difference is the new env. A test in an existing squad-spawn test file fails on base, passes on handin (SQ-1).
T6. Run every hit of `grep -rl 'squad-spawn\|squad-respawn' tests/` (targeted only). `python3 bin/processlint.py` exits 0.
