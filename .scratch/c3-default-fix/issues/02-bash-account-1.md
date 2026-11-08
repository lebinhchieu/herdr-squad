# 02 Bash/Git Bash startup path clears CLAUDE_CONFIG_DIR for account 1

Status: ready-for-agent
Slug: bash-account-1
Duties: design notes = Developer (in this file); technical AC = QA whitebox with the Developer; business AC = the ticket as written; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; full suite and promote.md = QA whitebox (full suite only after Chieu's yes via the Manager). A risk flag, user-visible change or business doubt found while building: BLOCKED to the Manager.

Brief: `scope.md` and `iterations/1.md` in this scope folder. Source of the bug: `C:/Users/84084/workspace/Guardian - Learn/.claude/squads/lastvil/goals/buildings-allies/claude-accounts-handoff.md` (read only).
Confirmed by the PO: in a herdr workspace whose default is c1, `echo $env:CLAUDE_CONFIG_DIR` in a new tab prints `...\.claude-3`; in c2 and c3 workspaces it is right. So a new shell inherits `CLAUDE_CONFIG_DIR` from the herdr server and nothing clears it for account 1.
Tests: test_ca_win, test_ca_install, test_ca_launchers, test_ca_autoswitch as touched (see CLAUDE.md > Running tests). Never run `install.sh` on the live `~/.claude-accounts`; use the temp HOME harness `tests/ca_stubs.py`.
Ticket path to commit this file to: `.scratch/c3-default-fix/issues/<NN>-<slug>.md` (first task also commits the other two; add `Status: ready-for-agent`).

Files: `tools/claude-accounts/lib.sh`, launchers in `tools/claude-accounts/bin/`, `install.sh` only if it writes a shell startup block. Design note first: find every place in this repo that exports `CLAUDE_CONFIG_DIR` for account 2/3 at shell startup without the unset for 1. The handoff says `~/.bashrc` has cases 2 and 3 but no 1; `install.sh` does not appear to write `~/.bashrc`, so if the repo does not own it, fix nothing there and report the exact snippet for the PO in `evidence.md`.

AC
1. For each repo-owned startup path found: default `1` with an inherited `CLAUDE_CONFIG_DIR` ends unset. List the paths checked in the design note (including "none found").
2. No change to behaviour for defaults 2 and 3.
3. A test for any code changed, in an existing test file.

## Technical AC (QA whitebox, proposed to the Developer; reply in this file or by ASK if you disagree)
T1. Design note lists every repo-owned startup path checked, with the `grep -rn CLAUDE_CONFIG_DIR tools/claude-accounts` command and its hits classified (sets for 2/3 / unsets / reads only). "None found" is allowed only with that grep shown.
T2. Where code changes: default 1 ends with the variable unset (`unset CLAUDE_CONFIG_DIR`), never `export CLAUDE_CONFIG_DIR=` (empty string) and never `~/.claude`. Defaults 2/3 export the same value as before.
T3. Nothing outside the repo is edited or run against: no write to `~/.bashrc`, no `install.sh` on the live `~/.claude-accounts`. Tests use the temp HOME harness `tests/ca_stubs.py`.
T4. Each changed path has a test in an existing file (test_ca_launchers / test_ca_install / test_ca_autoswitch as fits) that fails on base, passes on handin (SQ-1 receipts). If no code changes, `evidence.md` holds the exact `~/.bashrc` snippet for the PO and the reason.
T5. Run the touched test files and every hit of `grep -rl '<changed string>' tests/` (targeted only). `python3 bin/processlint.py` exits 0.

## Design note (Developer)
Command: `grep -rn CLAUDE_CONFIG_DIR tools/claude-accounts`. Hits, classified:
- Sets for 2/3 at startup: `windows/claude-accounts.ps1` (final switch; case 1 added in ticket 01). Nothing in bash.
- Sets for one launch only: `lib.sh:110` (`CLAUDE_CONFIG_DIR=... claude` for 2/3, as a command prefix) and the `.ps1` launcher function. Not startup.
- Unsets: `lib.sh:109` (`env -u` for account 1), `.ps1` lines 12, 176, 183.
- Reads only: `bin/cautoswitch:134`, `bin/caproc.py`, `record-usage.sh:7`.
- Docs only: README, HANDOFF, skill/SKILL.md.
`install.sh` writes no shell startup block (README: "The install never edits .bashrc"). Repo-owned bash startup path: none found. The recommended `.bashrc` line is already tested in `test_ca_launchers.BashrcLineTest` and has `*) unset CLAUDE_CONFIG_DIR`.
Result: no code change. The PO's own `~/.bashrc` is the gap (see evidence.md).
