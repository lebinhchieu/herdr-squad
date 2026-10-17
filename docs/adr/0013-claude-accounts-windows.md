# The Windows launchers are one PowerShell 7 file with the Workspace default

Status: accepted (claude-accounts)

**Decision:** Windows gets `tools/claude-accounts/windows/claude-accounts.ps1`, the source of the installed copy `C:\Users\<user>\.claude-accounts\claude-accounts.ps1`, which both PowerShell profiles dot-source. It ports only the Workspace default (`c1`-`c3`, `c`, `cdefault --ws`, `Resolve-ClaudeWorkspace`, the Account token) and mirrors `lib.sh` on 3e0474f. Not ported: `cswitch`, `cautoswitch`, the popup. `windows/` is never linked by `install.sh`; the PO copies the file.

**Why:** herdr runs on Windows (`herdr.exe` 0.9.3); the Workspace default is the one launcher feature the PO wanted there.

**Consequences:**
- The file stays PowerShell 7 syntax and the older Windows shape: account 2 is `~/.claude-b` (WSL: `~/.claude-2`), account 3 is `~/.claude-3`, and `c2`/`c3` still call the Windows `lib.sh`'s `relink` (hardlinks) through Git bash. **The Windows `lib.sh` must not be replaced by the repo's**, which has no `relink`. Windows PowerShell 5.1 cannot parse the file (`?:`); the 5.1 profile already errors on it (pre-existing).
- `CLAUDE_ACCOUNTS_HOME` overrides the state folder (tests and the PO's scratch run); every `herdr` call has a timeout and failure is silent; a workspace id is checked with `-cmatch '^w[0-9A-Za-z]+\z'` (`$` would accept a trailing newline).
- The squad can run PowerShell 7 over WSL (`pwsh.exe` from the WindowsApps alias, `-ExecutionPolicy Bypass`, test data on the WSL side, never under `/mnt/c`), so `tests/test_ca_win.py` runs the port for real and skips where there is no pwsh. What it cannot show (real NTFS rename while another process holds the file, a herdr pane's environment, the profile load, the spaces panel) is `tools/claude-accounts/windows/CHECKLIST.md`, the PO's.
- Known limit: NTFS is case-insensitive, so two herdr ids differing only in case would share one file. Ids seen (`w26`, `w2H`, `w2J`, `w6`) never do.

**Alternative rejected:** port `lib.sh` to PowerShell as a module or run it in Git bash for every call (a Git-bash start on each `c1` and a second source of truth for the herdr JSON rules).
