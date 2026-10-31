# Windows-native fixes for plugin 0.6.1

Status: ready-for-agent

**Goal:** `squad-start` opens a Manager tab on native Windows, and the plugin's own suite can tell you whether the shell scripts work there.

**Evidence:** `findings.md` in this folder (W1 to W11, found 2026-10-28 on Windows 11, Git for Windows bash, herdr 0.9.3, python3 3.14.6). Read it first; each ticket cites its W number.

**Tickets** (`issues/`), in the order to take them:

| # | Ticket | From |
|---|---|---|
| 01 | `PATH=` env sent to `herdr tab create` is mangled | W1 (blocker) |
| 02 | `scaffold` / `upgrade` need the installed-cache fallback | W3 |
| 03 | Windows launch helper for the tests | W2 |
| 04 | Untrack dev state from the plugin repo | W7 |
| 05 | `squad-notify` on Windows | W4 |
| 06 | Log appends without `flock` | W5 |
| 07 | One `pick_bash` for every bash launch | W6 |
| 08 | Check the unverified items | W8 to W11 |

## Test machine and how to reproduce W1

- Native Windows, Git for Windows (`C:\Program Files\Git\usr\bin\bash.exe`), `python3` 3.14, `jq` 1.8, herdr 0.9.3 (default tab shell `pwsh`). `C:\Windows\System32\bash.exe` (WSL) is also on PATH and wins a bare `bash` launch from Python.
- Run inside a herdr pane (`HERDR_ENV=1`) in a project with a composed squad: `squad-start --squad <name> "x" --touches docs --name probe`. Expected failure: `tab_create_failed … The system cannot find the file specified`.
- Without a Manager: `herdr tab create --cwd "$PWD" --label p --no-focus --env "PATH=C:/some/dir/bin:$PATH"` fails; with `--env "PATH=/c/some/dir/bin:$PATH"` it works. Close the probe tab with `herdr tab close <id>`.
- A `herdr` shim that logs argv is the safe way to test without starting a Claude session: a bash script named `herdr` first on PATH, printing `{"result":{"root_pane":{"pane_id":"p1"},"tab":{"tab_id":"t1"}}}` for `tab create`, exit 1 for `agent get`, and `{"result":{"type":"ok"}}` otherwise. Note the shim is a bash script, so Git Bash does not convert its argv; the real herdr is a native exe and does.

## Constraints

- Linux behaviour must not change; Linux tests that pass today keep passing (ADR 0011 rule: nothing skipped on Linux).
- Follow ADR 0011 (`docs/adr/0011-plugin-runs-on-native-windows.md`): Git Bash plus `python3`, UTF-8 and `newline="\n"` rules for `bin/`.
- Do not edit the installed cache under `~/.claude/plugins/cache`; work in this checkout and cut 0.6.2.
- Nothing has been changed in this repo for this handoff except the files in `.scratch/windows-native/`. Not committed.
