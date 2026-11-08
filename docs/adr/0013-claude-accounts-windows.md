# The Windows launchers are one PowerShell 7 file with the Workspace default

Status: accepted (claude-accounts)

**Decision:** Windows gets `tools/claude-accounts/windows/claude-accounts.ps1`, the source of the installed copy `C:\Users\<user>\.claude-accounts\claude-accounts.ps1`, which both PowerShell profiles dot-source. It ports only the Workspace default (`c1`-`c3`, `c`, `cdefault --ws`, `Resolve-ClaudeWorkspace`, the Account token) and mirrors `lib.sh` on 3e0474f. Not ported: `cswitch`, `cautoswitch`, the popup. `windows/` is never linked by `install.sh`; the PO copies the file.

**Why:** herdr runs on Windows (`herdr.exe` 0.9.3); the Workspace default is the one launcher feature the PO wanted there.

**Consequences:**
- The file stays PowerShell 7 syntax and the older Windows shape: account 2 is `~/.claude-2` and account 3 is `~/.claude-3`, as on WSL, and `c2`/`c3` call the repo `lib.sh`'s `relink` (hardlinks and junctions) through Git bash. *Update:* `lib.sh` now has `relink` and `acct_dir`, so the repo `lib.sh` is the one installed on Windows. `install.sh` copies instead of linking there (`--copy`, automatic). `cswitch`, `cautoswitch` and `cwake` run on Git Bash through `bin/caproc.py`, which replaces `/proc` and `pgrep` with `herdr pane process-info` and a read of the process environment. `windows/` keeps the older `autoswitch.py` and `usage.py`. The first Windows install renames `~/.claude-b` to `~/.claude-2`. Windows PowerShell 5.1 cannot parse the file (`?:`); the 5.1 profile already errors on it (pre-existing).
- `CLAUDE_ACCOUNTS_HOME` overrides the state folder (tests and the PO's scratch run); every `herdr` call has a timeout and failure is silent; a workspace id is checked with `-cmatch '^w[0-9A-Za-z]+\z'` (`$` would accept a trailing newline).
- The squad can run PowerShell 7 over WSL (`pwsh.exe` from the WindowsApps alias, `-ExecutionPolicy Bypass`, test data on the WSL side, never under `/mnt/c`), so `tests/test_ca_win.py` runs the port for real and skips where there is no pwsh. What it cannot show (real NTFS rename while another process holds the file, a herdr pane's environment, the profile load, the spaces panel) is `tools/claude-accounts/windows/CHECKLIST.md`, the PO's.
- ADR 0011 says PowerShell is not a target of the plugin. That still holds: this file is the PO's own tooling under `tools/claude-accounts/`, which nothing in the plugin runs (ADR 0012). It does not make PowerShell a plugin prerequisite.
- Known limit: NTFS is case-insensitive, so two herdr ids differing only in case would share one file. Ids seen (`w26`, `w2H`, `w2J`, `w6`) never do.

**Alternative rejected:** port `lib.sh` to PowerShell as a module or run it in Git bash for every call (a Git-bash start on each `c1` and a second source of truth for the herdr JSON rules).

**Addendum 2026-11-08 (c3-default-fix):** a new pane's account comes only from the shell profile (workspace default first, else global); the profile now also clears an inherited `CLAUDE_CONFIG_DIR` for account 1. `squad-spawn` and `squad-respawn` do not pass `--env CLAUDE_CONFIG_DIR`: the profile would overwrite it, `herdr tab create --env` cannot unset a variable, and a copy of the default rule in spawn would be a second source that can drift. This does not change the Decision or Consequences above.
