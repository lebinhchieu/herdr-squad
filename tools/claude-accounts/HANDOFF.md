# Two Claude accounts on WSL — handoff

**Source: `tools/claude-accounts/` of the squad repo. Run `bash tools/claude-accounts/install.sh --dry-run` from the main checkout inside WSL, read the plan, then run it with `--force` the first time (it backs the originals up to `.install-backup/`)** (see `README.md`), open a new shell, then `c2 auth login` with your second account. That's the whole setup.

## Commands

| Command | Does |
|---|---|
| `c1` / `c2` | Start Claude on account 1 / 2; args pass through (`c2 --resume <id>`) |
| `c` | Start Claude on the default of this herdr workspace, else the global default |
| `cdefault` / `cdefault 2` / `cdefault --ws [<workspace id|panel number|label>] 2` | Show the effective default here / set the global default / set one herdr workspace's default (ref = id, panel number or label, first match in that order; two equal labels = `ambiguous`, rc 2; the account is the last argument; no ref = the current workspace) |
| `cswitch 1\|2 [pane]` | Herdr only: wait for the pane's Claude to go idle, `/exit`, resume the same session on that account |
| `cwake <pane>` | Herdr only: once the pane is idle (60 s gate), send it ONE short wake prompt; a pane without `SQUAD_NAME` (a person's own pane) or without a live claude is skipped. `cwake --mark <pane>` samples whether the pane has pending work and writes its marker. Called by `cswitch` and `cautoswitch`; rarely by hand |

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

- **Restart `cautoswitch` after install:** it is a long-running python process; an `install.sh` run replaces the file on disk but the running tick loop keeps the old code (no wake step) until restarted. `cwake`, `cswitch` are read fresh each call.
- **No workspace file = global default.** On a machine where panes already run on other accounts, run `cdefault --ws <ws> <N>` for each live workspace (ids from `herdr workspace list`), then `cautoswitch --once --dry-run`, before the first real tick; otherwise it moves every off-global pane.
- **Panel token, not observed:** the spaces panel itself, and whether a cold herdr restart drops the tokens (they would come back at each workspace's next default write). A workspace with no default write yet shows nothing.
- **In herdr, `cdefault N` changes only the global file**, not the current workspace; use `cdefault --ws N` (current workspace) or `cdefault --ws <ws> N`.

## Autoswitch: who is woken after a switch (built 2026-10-23)

**Rule (PO, E1): every off-default squad pane moves to the new account silently; only a pane with pending work is woken, once, after its workspace's batch is back.** A bare `--resume` sends no prompt, so an idle pane is not asked anything.

- **Move:** `cautoswitch` runs `cswitch` on each off-default squad pane, one at a time (unchanged). `cswitch` never wakes. It now waits for `--until idle --until done`, so `/exit` is never typed into a `blocked` permission dialog; a blocked pane is waited on (up to the 10 min `cswitch` already allows).
- **Pending work** is sampled by `cwake --mark` from the pane's session transcript (`~/.claude*/projects/<cwd>/<session>.jsonl`, last 200 lines), herdr `agent get` and `messages.jsonl`. A pane is pending when ANY of:
  1. **Cut off:** herdr says `blocked`, or the last assistant record is a `tool_use`, or a user record follows the last `end_turn`. Sampled by `cswitch`'s detached block right after the pane went idle/done and before `/exit`, so a pane that was only mid-turn when the tick started (it finishes its turn first) is not marked.
  2. **Failed send:** the pane's own transcript has a `SendMessage` whose result failed (`toolUseResult.success == false`, or the result text is JSON with `success:false`, or `is_error:true`) since the batch started (first `-> account` line of the workspace in `cswitch.log`, at most 30 min old), with no later successful `SendMessage` to the same recipient. Sampled by `cautoswitch` after the batch, because failures happen while other panes are down.
  3. **Unanswered message:** `messages.jsonl` (`SCOPE_DIR`, else `GOAL_DIR`, else `SQUAD_DIR` of the pane) has a row `to == <name>` newer than the pane's last `end_turn`.
- **Marker:** a pending pane gets `~/.claude-accounts/wake-pending/<pane>` = `epoch name reason` (reasons `blocked`, `cut-off`, `failed-send`, `unanswered-message`, comma-joined). A marker older than 30 min (from its first write) is deleted unsent with a log line. Keep the dir: the installer treats it as state.
- **Wake:** `cautoswitch` runs the wake step after its per-pane loop, per workspace. It skips a workspace while one of its panes is inside the 15 min "cswitch in flight" window; it samples clause 2 for each pane that is back on target; then calls `cwake <pane>` for each marked pane that is back, oldest marker first, `CSWITCH_WAKE_GAP` seconds apart (default 3). A pane whose move `FAILED` or is still off-default keeps its marker, is not woken, and does not hold up the others; the next tick retries the move and wakes it only if it is back within the 30 min.
- **`cwake <pane>`:** `herdr agent wait <pane> --until idle --timeout 60000` (override `CWAKE_TIMEOUT_MS`); idle → `herdr agent prompt` with the wake text, log `<ts> <pane> <name> wake sent`, marker deleted. Not idle in 60 s → no prompt, log `WAKE SKIPPED <pane> state=<s>` and `... wake skipped`, marker deleted, no retry. No `SQUAD_NAME` (a person's own pane) or no live claude (retired) → skipped and logged, never prompted. The `(<old> -> <new>)` account numbers are in the text only when this `cautoswitch` process did the move.
- **Wake text:** "Your Claude account changed (1 -> 2) and this session was resumed. A message sent to you or by you in the last minutes may have failed ("not reachable"). Resend what failed and carry on; if nothing is pending, answer with one line." `CSWITCH_WAKE_TEXT` replaces it.
- **Switches:** `CSWITCH_WAKE=on` (default) | `off`. `off` = the old behaviour: move every off-default pane, sample nothing, write no marker, wake nobody (`cwake` does nothing). Set it in the `cautoswitch` tab's environment. `cautoswitch --dry-run` writes no marker and sends no prompt.
- **Fail direction:** an unreadable transcript, `messages.jsonl` or herdr call = not pending, one line in `cswitch.log`; it never wakes everyone.
- **Not built:** no wake from `cswitch`; no PostToolUseFailure hook (a failed send is read from the sender's transcript instead); no task-file signal (an idle Dev waiting on QA would always look pending).

### Unverified until a live sample

- **Bare `--resume` cost:** not measured. Expected: the resume loads the local transcript and waits at an empty prompt with no model call. If it did cost a turn, it costs the same for every moved pane; the rule only avoids a second turn on idle panes.
- **Clause 2 on a live batch:** the failure shape (`toolUseResult.success:false`, no `is_error`) was read from a real failed `SendMessage` in a transcript from 2026-10-16 and is covered by stub tests, but clause 2 has not yet fired in a real account switch. The `blocked` herdr row used in the tests is `.derived` (no real one was on disk).
- **Whole chain on live panes:** all tests use stub `herdr`/`claude`; no live pane was touched.

### PO live-probe checklist (first real batch)

1. Throwaway pane first: start a squad-style claude (`SQUAD_NAME` set) in a spare herdr pane of the workspace, off the workspace default.
2. `cautoswitch --once --dry-run`: it prints the tick status line (`HH:MM:SS ok: <ws> -> cN ...`) and `[dry-run] would cswitch ...` for that pane (plus `[dry-run] would set ... default` if over the threshold); `cswitch.log` gets no `wake`/`WAKE` line and `ls ~/.claude-accounts/wake-pending` is unchanged.
3. Pick one **idle** pane. Run `~/.claude-accounts/usage-popup.sh` (or `squad-usage`) and note the totals; run the real tick (`cautoswitch --once`); after the pane is back, compare again. No increase beyond the move itself = a bare `--resume` costs nothing.
4. `grep -E 'wake|WAKE' ~/.claude-accounts/cswitch.log`: only panes that had pending work show `wake sent`; idle panes show nothing; your own panes never.
5. Clause 2 live sample: from a squad pane (the sender) message a pane that is down during the batch (the send fails with "not reachable"). The marker is deleted at the wake and the `wake sent` line carries no reason, so prove clause 2 one of two ways: (a) any time after the batch (the transcript survives the wake), run `cwake --mark <sender pane> --clauses 2 --since <epoch of the first `-> account` line in cswitch.log>` and `cat ~/.claude-accounts/wake-pending/<sender pane>`: it must end in `failed-send`; then `rm` that marker, or the next tick wakes the sender again; or (b) after the real tick, read the sender's transcript for the failed `SendMessage` (`toolUseResult.success:false`) and check the sender's pane received the wake prompt while it had no cut-off turn or unanswered message (otherwise `wake sent` could come from clause 1 or 3). Report whether it fired.
6. Rollback if wrong: restart `cautoswitch` with `CSWITCH_WAKE=off`.

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
