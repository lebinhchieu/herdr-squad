---
name: claude-accounts
description: The user's two Claude accounts and their launchers c1 / c2 / c / cdefault / cswitch. Use when the user mentions c1, c2, "account 1/2", the default account, switching accounts, or hitting / nearing a usage limit.
---

# Three Claude accounts

**c1 = account 1, c2 = account 2, c3 = account 3.** Same settings, CLAUDE.md, skills, plugins, hooks and memory; only the login differs.

| Command | Does |
|---|---|
| `c1` / `c2` / `c3` | Start Claude on account 1 / 2 / 3; args pass through (`c2 --resume <id>`) |
| `c` | Start Claude on the default of this herdr workspace, else the global default |
| `cdefault` / `cdefault 1\|2\|3` / `cdefault --ws [<workspace id\|panel number\|label>] <1\|2\|3>` | Show the effective default here / set the global default / set one herdr workspace's default (ref = id, panel number or label, first match in that order; two equal labels = `ambiguous`, rc 2; the account is the last argument; no ref = the current workspace) |
| `cswitch 1\|2\|3 [pane]` | Herdr + bash only: wait until that pane's Claude is idle, `/exit` it, resume the same session on the given account. Defaults to the calling pane |
| `cautoswitch [--threshold 90] [--interval 300] [--once] [--dry-run]` | Watcher, started by hand in a herdr tab (`--once --dry-run` first to look). Per workspace: when the workspace default's 5h ≥ threshold and another account is lower on both 5h and 7d (lowest 5h wins), it writes that account as the workspace default (never the global file). Then, every tick, it `cswitch`es every squad pane (claude with `SQUAD_NAME`) that is off its workspace default, one at a time. An expired token is refreshed through one `claude -p` under that account. Logs to `cswitch.log` |

## Doing what the user asks

- **"Switch to c2" / "move to account 2"** → run `cswitch 2` (bash, inside Herdr). It detaches and waits for idle, so it is safe to run from the agent being switched — finish your reply right after; the restart happens once you go idle.
- **"Switch when usage passes N%"** → read the usage first. The status-line input carries `rate_limits.five_hour.used_percentage` and `rate_limits.seven_day.used_percentage`; the last captured copy is `~/.claude/statusline-input-debug.json`. Report the number and switch only if the condition holds.
- **"Make c2 the default"** → in herdr: `cdefault --ws 2` (running `c2` also does it); `cdefault 2` sets only the global fallback. `c` follows at once; plain `claude` and `herdr agent start --kind claude` follow the global default in new shells, or the workspace default through the new `.bashrc` line.
- **"Log in c3"** → c3 has no login yet; the user runs `! c3 auth login` (interactive).
- **Which account am I on?** → `CLAUDE_CONFIG_DIR` unset = account 1; `~/.claude-2` = account 2, `~/.claude-3` = account 3 (WSL; Windows uses `~/.claude-b` for 2, and has no c3).

## Where things live

- **Windows bash:** `~/.claude-accounts/bin/` + `lib.sh`, loaded from `~/.bash_profile`.
- **PowerShell:** `~/.claude-accounts/claude-accounts.ps1`, dot-sourced from both PowerShell profiles. No `cswitch` there.
- **WSL:** installed by `~/.claude-accounts/install-wsl.sh`; see `~/.claude-accounts/HANDOFF.md`.
- **Default account:** global file `~/.claude-accounts/default` (`1|2|3`, shared by bash and PowerShell) plus one file per herdr workspace in `~/.claude-accounts/workspace-default/<workspace id>`.
- **Account in the herdr spaces panel:** every write of a workspace default (`c1/c2/c3`, `cswitch`, `cdefault --ws`, `cautoswitch`) also reports the display-only token `account=c<N>` to herdr (`herdr workspace report-metadata`, source `claude-accounts`); it never renames a workspace and never changes an exit code. The panel shows it through the `$account` token in the `[ui.sidebar.spaces] rows` of `~/.config/herdr/config.toml` (that row is set). A workspace with no default write yet shows nothing; `cdefault N` (global) reports nothing.
- **Usage popup (Herdr `prefix+u`):** `usage-popup.sh` fetches all three accounts' 5h/7d usage live from `api.anthropic.com/api/oauth/usage` (what `/usage` shows) with each account's own `.credentials.json` token — no session needed. It never refreshes an expired token (that could break Claude Code's login); it falls back to the status-line cache `usage-1|2` written by `record-usage.sh`. This is also the quickest way to answer "what's my usage?": run `echo x | ~/.claude-accounts/usage-popup.sh`. Key binding: `[[keys.command]]` in Herdr's `config.toml`.
- **Switch log:** `~/.claude-accounts/cswitch.log`.
- **`cswitch` keeps launch args:** it reads the pane's claude `/proc/<pid>/cmdline` (`--agent`, `--settings`, `--model`, `--plugin-dir`, …), resumes with them, and restores the herdr agent name. It drops `--session-id` from the reused args (claude 2.1.302 refuses it with `--resume`; the resume keeps the same session id). The original is kept as `bin/cswitch.orig`.

## Gotchas

- **A workspace with no default file falls back to the global default.** Before starting `cautoswitch` on a machine where panes already run on other accounts, set each live workspace (`cdefault --ws <ws> <N>`, ids from `herdr workspace list | jq -r '.result.workspaces[].workspace_id'`) and run `cautoswitch --once --dry-run` first; otherwise the first tick moves every off-global pane. Known limit: the panel itself and a cold herdr restart's effect on the token were not observed (the token may be gone until the next default write); a herdr server restart may reuse a workspace id and hand its old default to a new workspace; `cdefault` shows it.
- **Never set `CLAUDE_CONFIG_DIR=~/.claude` for account 1** — that moves its global config from `~/.claude.json` to `~/.claude/.claude.json` and loses MCP servers and project trust. Unset it instead.
- **Windows shares files by hardlink** (file symlinks need admin). A rename-style rewrite splits the link; `c2` re-joins them on launch, keeping the newer copy. Edit shared files via `~/.claude/`.
- **Not shared:** each account's `.claude.json`, so MCP servers added later with `claude mcp add` exist on one account only.
