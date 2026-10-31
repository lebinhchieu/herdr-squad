# 08: Check the unverified Windows items

Status: needs-info
Type: research
Blocked by: 01
Source: findings.md W8 to W11

Each item below was seen or suspected but not proven. Answer each with evidence, fix what is real, and drop the rest from `findings.md`.

1. **Hook shell (W8).** `hooks/hooks.json` has no `shell:` key; the commands are `"${CLAUDE_PLUGIN_ROOT}/bin/…"`. Does this Claude Code build run them under bash on Windows when PowerShell is the primary shell? Evidence: a hook that writes its `$0` and `$SHELL` to a file, fired by a real tool call. Same command text through `bash -c` with a backslash path worked.
2. **Mixed path forms (W9).** `squad-start` exports `SQUAD_DIR=C:/…`; `squad-spawn` derives `/c/…` via `readlink -f`; `SQUAD_PLUGIN_DIR` is backslashes. All worked in the paths tried. Grep the scripts for `[[ $a == $b ]]` and `case` comparisons between those forms; normalise (one `cygpath -u`) or prove none exist.
3. **cwd case (W10).** `~/.claude/projects` holds both `C--Users-84084-Workspace-…` and `…-workspace-…` for one folder. Does `squadtranscript.agent_sessions` (matches project folders by name) miss sessions started with another case? Test with `squad-usage` / `squad-report` on a scope whose Manager was started from a differently cased cwd.
4. **Parallel bash start (W11).** Git Bash printed `fatal error - add_item ("\??\C:\Program Files\Git", "/", ...) failed, errno 1` once, while a long test run was active. Try 10 parallel `bash -c true` while another suite runs; if it reproduces, `squad-spawn` needs a retry or a single-flight guard.
5. **Long paths.** Covered by 04; re-check after it lands.

## AC
- [ ] One line per item in `findings.md`: confirmed (with ticket) or cleared (with evidence).

## Comments
