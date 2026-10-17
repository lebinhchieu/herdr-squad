# Two Claude accounts on WSL — handoff

**Source: `tools/claude-accounts/` of the squad repo. Run `bash tools/claude-accounts/install.sh --dry-run` from the main checkout inside WSL, read the plan, then run it without `--dry-run`** (details: its `README.md`), open a new shell, then `c2 auth login` with your second account. That's the whole setup.

## Commands

| Command | Does |
|---|---|
| `c1` / `c2` | Start Claude on account 1 / 2; args pass through (`c2 --resume <id>`) |
| `c` | Start Claude on the default of this herdr workspace, else the global default |
| `cdefault` / `cdefault 2` / `cdefault --ws [<workspace id|panel number|label>] 2` | Show the effective default here / set the global default / set one herdr workspace's default (ref = id, panel number or label, first match in that order; two equal labels = `ambiguous`, rc 2; the account is the last argument; no ref = the current workspace) |
| `cswitch 1\|2 [pane]` | Herdr only: wait for the pane's Claude to go idle, `/exit`, resume the same session on that account |

**Usage pattern:** ask Claude "if 5-hour usage > 90%, run `cswitch 2`". The status-line JSON carries `rate_limits.five_hour.used_percentage` and `seven_day`, so Claude can read the condition.

## How it works

**Account 1 is plain `~/.claude`** with `CLAUDE_CONFIG_DIR` unset — so it keeps using `~/.claude.json`.

- **Account 2 is `~/.claude-2`** with `CLAUDE_CONFIG_DIR` pointing at it. It owns only its login (`.credentials.json`) and `.claude.json`.
- **Everything else is symlinked** to `~/.claude`: `CLAUDE.md`, `settings*.json`, `.mcp.json`, `statusline-command.sh`, `skills`, `plugins`, `hooks`, `themes`, `output-styles`, `agents`, `commands`, `projects`.
- **`projects` being shared** is what makes cross-account `--resume` work and keeps auto-memory identical.
- **The default account** is the global `~/.claude-accounts/default` (`1|2|3`) plus, in herdr, one file per workspace in `~/.claude-accounts/workspace-default/<workspace id>`. `c` reads them on every call (workspace first, else global); your shell rc exports `CLAUDE_CONFIG_DIR` from the effective default at startup, so plain `claude` — and `herdr agent start --kind claude` — follow it in shells opened afterwards.

## Default account per herdr workspace (design decision, 2026-10-17)

- **Decision (PO, E1 = a):** the default Claude account is per herdr workspace (`HERDR_WORKSPACE_ID`). Running `c1`/`c2`/`c3` (also through `cswitch`) sets that workspace's default; the global `~/.claude-accounts/default` is the fallback outside herdr and when a workspace has no entry, and `cdefault N` still sets it. `cautoswitch` only writes workspace defaults.
- **Storage:** `~/.claude-accounts/workspace-default/<workspace id>`, one file per workspace holding `1|2|3`, written atomically; entries of workspaces that `herdr workspace list` no longer shows are deleted on the next write.
- **Known limit:** a herdr server restart could reuse an id and hand its old default to a new workspace.
- **Panel token:** each workspace-default write also runs `herdr workspace report-metadata <id> --source claude-accounts --token account=c<N> --seq <epoch ms>` (display-only; never a rename; a failure or a hang of more than 3 s changes nothing). The herdr spaces panel shows it through `$account` in `[ui.sidebar.spaces] rows` of `~/.config/herdr/config.toml`, which is set (`herdr server reload-config` reloads it). The token is readable in `herdr workspace get|list`. `cdefault N` (global) reports nothing.
- **Consequences:** the `claude-accounts` skill and this file described one global default, so both are updated by T5. A workspace with no entry falls back to the global default; set each live workspace before starting `cautoswitch` and run `--once --dry-run` first.
- **Settled (PO, E2 = a):** the PO starts `cautoswitch` by hand in a herdr tab; there is no autostart.

### Hazards

- **No workspace file = global default.** On a machine where panes already run on other accounts, run `cdefault --ws <ws> <N>` for each live workspace (ids from `herdr workspace list`), then `cautoswitch --once --dry-run`, before the first real tick; otherwise it moves every off-global pane.
- **Panel token, not observed:** the spaces panel itself, and whether a cold herdr restart drops the tokens (they would come back at each workspace's next default write). A workspace with no default write yet shows nothing.
- **In herdr, `cdefault N` changes only the global file**, not the current workspace; use `cdefault --ws N` (current workspace) or `cdefault --ws <ws> N`.

## Agent skill

**The `claude-accounts` skill teaches any agent what c1 / c2 mean**, so "switch to c2" or "make c2 the default" just works.

- **Where:** `~/.claude/skills/claude-accounts/SKILL.md` — shared by both accounts through the `skills` link.
- **Getting it into WSL:** the `cp -r .../skills` step in Notes below brings it along.
- **What it covers:** the commands, how to read usage before a conditional switch (`~/.claude/statusline-input-debug.json`), how to tell which account a session is on, and the gotchas.
- **WSL tweak:** it lists Windows paths too (`~/.claude-b`, PowerShell, hardlinks); on WSL account 2 is `~/.claude-2`, as the skill already notes.

## Herdr usage popup

**Press `prefix+u` in Herdr for a popup with both accounts' 5h / 7d usage and reset times — fetched live, no running session needed.**

- **Live source:** `~/.claude-accounts/usage-popup.sh` calls `https://api.anthropic.com/api/oauth/usage` (header `anthropic-beta: oauth-2025-04-20`) with each account's `accessToken` from `<config dir>/.credentials.json`.
- **Expired token:** not refreshed on purpose (refresh could rotate the token out from under Claude Code); the popup says so and falls back to the cache.
- **Fallback cache:** `statusline-command.sh` backgrounds `~/.claude-accounts/record-usage.sh SESSION_ID FIVE FIVE_RESETS WEEK WEEK_RESETS`, which writes `usage-1|2`.
- **Binding:** a `[[keys.command]]` `type = "popup"` entry in Herdr's `config.toml`.
- **WSL:** copy `record-usage.sh` and `usage-popup.sh` from `/mnt/c/Users/84084/.claude-accounts/`, change `python -I` to `python3 -I` and `~/.claude-b` to `~/.claude-2` in the popup, and add the binding to `~/.config/herdr/config.toml` with `command = "~/.claude-accounts/usage-popup.sh"`.

## Differences from the Windows version

- **Symlinks instead of hardlinks.** Windows needed admin for file symlinks, so it used hardlinks plus a re-link-on-launch step. WSL doesn't, so that step is gone.
- **Folder renamed** `~/.claude-b` → `~/.claude-2`.
- **`python3`** instead of `python`; no `cygpath`/`mklink`.
- **No PowerShell launchers.** Windows also has `~/.claude-accounts/claude-accounts.ps1` (dot-sourced from both PowerShell profiles; no `cswitch`). WSL only needs bash.

## Notes

- **WSL's `~/.claude` is separate from Windows'.** Your skills, `CLAUDE.md`, settings and memory are not there yet. Copy them first (e.g. `cp -r /mnt/c/Users/84084/.claude/{CLAUDE.md,settings.json,skills,output-styles} ~/.claude/`), then run the installer. Windows paths inside `settings.json` (status line, hooks) will need rewriting for Linux.
- **Per-account leftovers:** MCP servers added later via `claude mcp add` (user scope) live in each account's `.claude.json`, so they don't sync. Since `settings.json` is shared, `model` / `env` in it apply to both accounts.
- **`cswitch` is untested end-to-end.** Try it on a throwaway pane first; it logs to `~/.claude-accounts/cswitch.log`.
- **Terms of service:** using two subscriptions to get around usage limits may get either account flagged — your call.
