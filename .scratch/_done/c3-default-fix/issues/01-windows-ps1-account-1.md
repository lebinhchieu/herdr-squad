# 01 Account 1 clears CLAUDE_CONFIG_DIR at PowerShell startup

Status: ready-for-agent
Slug: windows-ps1-account-1
Duties: design notes = Developer (in this file); technical AC = QA whitebox with the Developer; business AC = the ticket as written; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; full suite and promote.md = QA whitebox (full suite only after Chieu's yes via the Manager). A risk flag, user-visible change or business doubt found while building: BLOCKED to the Manager.

Brief: `scope.md` and `iterations/1.md` in this scope folder. Source of the bug: `C:/Users/84084/workspace/Guardian - Learn/.claude/squads/lastvil/goals/buildings-allies/claude-accounts-handoff.md` (read only).
Confirmed by the PO: in a herdr workspace whose default is c1, `echo $env:CLAUDE_CONFIG_DIR` in a new tab prints `...\.claude-3`; in c2 and c3 workspaces it is right. So a new shell inherits `CLAUDE_CONFIG_DIR` from the herdr server and nothing clears it for account 1.
Tests: test_ca_win, test_ca_install, test_ca_launchers, test_ca_autoswitch as touched (see CLAUDE.md > Running tests). Never run `install.sh` on the live `~/.claude-accounts`; use the temp HOME harness `tests/ca_stubs.py`.
Ticket path to commit this file to: `.scratch/c3-default-fix/issues/<NN>-<slug>.md` (first task also commits the other two; add `Status: ready-for-agent`).

Files: `tools/claude-accounts/windows/claude-accounts.ps1` (the last `switch (Get-ClaudeDefaultAccount)` block, about line 180), tests in `tests/test_ca_win.py` / `tests/ca_win_cases.ps1`. Check whether the installed copy rules in the repo (byte copy, see commit 2cf1604) need the same edit.

AC
1. When the effective default account is `1` and the shell starts with `CLAUDE_CONFIG_DIR` set to `~/.claude-3` (or `-2`), after loading the profile `CLAUDE_CONFIG_DIR` is unset.
2. Default `2` and `3` still set `~/.claude-2` / `~/.claude-3` (no change). The workspace default still wins over the global one.
3. Never sets `CLAUDE_CONFIG_DIR=~/.claude` for account 1 (see `skill/SKILL.md`).
4. One test for AC 1 that fails on the base sha and passes on the fix (SQ-1: run once on base, once on the handin sha).

## Technical AC (QA whitebox, proposed to the Developer; reply in this file or by ASK if you disagree)
T1. The final `switch (Get-ClaudeDefaultAccount)` gets a case `'1'` that removes `CLAUDE_CONFIG_DIR` from the process env. Cases `'2'`/`'3'` are byte-unchanged. No path sets `CLAUDE_CONFIG_DIR` to `~/.claude`.
T2. The case is silent when the variable is already unset (no error record, no stderr line, `$ErrorActionPreference` not changed).
T3. One test in `tests/ca_win_cases.ps1` + `tests/test_ca_win.py` (extend, no new file): start with `CLAUDE_CONFIG_DIR=~/.claude-3`, default 1, assert unset after the profile loads. Receipts in `evidence.md`: fails on the base sha, passes on the handin sha (SQ-1). Existing workspace-over-global default test still passes.
T4. Any other copy of the profile block in the repo (installed-copy rules, commit 2cf1604, `install.sh` text) gets the same edit; `grep -rn "Get-ClaudeDefaultAccount" tools tests` listed in the design note.
T5. Run `test_ca_win` and `test_ca_install` on the handin sha (targeted only, no full suite). `python3 bin/processlint.py` exits 0.
