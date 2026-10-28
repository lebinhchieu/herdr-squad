# Windows check: per-workspace default (about 15 minutes, pwsh 7 + herdr.exe)

The squad ran `tests/test_ca_win.py` with pwsh 7.6.7 over WSL (ids, resolve, files, c1-c3, cdefault, a hung or missing herdr). You check only what that cannot show: a real NTFS disk, a real herdr pane, the spaces panel. `<repo>` = your checkout.

1. **Scratch first** (nothing live changes). In a pwsh 7 tab: `$env:CLAUDE_ACCOUNTS_HOME='C:\temp\ca-scratch'; . <repo>\tools\claude-accounts\windows\claude-accounts.ps1`. Then `cdefault 2` -> `default account: 2`, `cdefault` -> `2`, file `C:\temp\ca-scratch\default` holds `2`. Fails: the file does not parse; report the error text.
2. **Install, keeping a copy.** `Copy-Item $HOME\.claude-accounts\claude-accounts.ps1 $HOME\.claude-accounts\claude-accounts.ps1.before`, then copy `<repo>\tools\claude-accounts\windows\claude-accounts.ps1` over it. Leave `lib.sh` alone. Open a NEW pwsh 7 tab: no red error at start.
3. **Inside herdr.** In a herdr pane (Windows herdr.exe): `$env:HERDR_ENV; $env:HERDR_WORKSPACE_ID` -> `1` and an id like `w6`. Empty means herdr does not export them here: stop, tell the Tech Lead.
4. **c1 writes the default.** `c1`, quit claude. `Get-Content $HOME\.claude-accounts\workspace-default\<id>` -> `1`; the spaces panel shows `c1` on this workspace. No token: the file is the proof, the token is display only.
5. **cdefault --ws.** `cdefault --ws 2` -> `default account of <id>: 2`. By id: `cdefault --ws <id> 3`; by panel number: `cdefault --ws 1 2`; by label: `cdefault --ws <label> 1`. Each prints `default account of <that id>: N`.
6. **Ambiguous label.** Give two workspaces the same label, `cdefault --ws <label> 2` -> `ambiguous: <label> matches` + one line per workspace, nothing written. Fails: it wrote one anyway.
7. **Second workspace unaffected.** In another workspace `cdefault` -> its own value (global default when it has no file). Open a new pane in workspace 1: `cdefault` prints the value step 5 set last for it.
8. **Hung or missing herdr.** `$script:HerdrExe='C:\nope\herdr.exe'; c1` (herdr is now not found, claude.exe stays on Path; it resets with the tab): claude still starts within a few seconds, and `cdefault` prints a number.
9. **Two c1 at once (NTFS).** Two panes in two workspaces, run `c1` in both within a second. Both `workspace-default\<id>` files exist, each `1`, no `.tmp.*` left. A `.tmp.*` left is harmless; tell the Tech Lead.
10. **Rollback.** `Copy-Item $HOME\.claude-accounts\claude-accounts.ps1.before $HOME\.claude-accounts\claude-accounts.ps1 -Force`, new tab. `workspace-default\` may stay or be deleted; only the new file reads it.

Known, not fixed here: Windows PowerShell 5.1 cannot parse this file (it uses `?:`), so a 5.1 profile that dot-sources it errors at every start (already true before this change). NTFS ignores case: two herdr ids that differ only in case would share one file (ids seen: `w26`, `w2H`, `w2J`, `w6`).
