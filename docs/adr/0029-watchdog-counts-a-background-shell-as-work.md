# 0029: The watchdog counts a background shell as work

Status: accepted. Extends 0028 (goal-based idle test) and 0022 (sleep-when-idle); neither text changes.

## Context
An agent that starts `run_suite.py` in the background ends its turn, so herdr reports `done` and the watchdog read it as idle: false nudges at 5 and 15 minutes, and with sleep-when-idle on the PC could suspend during a full suite. herdr already returns a per-agent `tokens.bg` (`⏵ 1 shell`) in `agent list`, written by the `herdr-bg` hook from Claude's own task output files.

## Decision
- The plugin ships the `herdr-bg` hook (`hooks/herdr-bg`, wired in `hooks/hooks.json` for PostToolUse `Bash|Monitor|TaskStop` and Stop). It needs bash, jq and herdr and is a silent no-op without them.
- An agent that herdr reports `idle`/`done` and that carries a `bg` token counts as working, for at most `SQUAD_WATCHDOG_BG_MAX` minutes (default 60; 0 = off). The clock is one stretch of "idle with a token": it resets when the agent works or the token clears, and does not re-arm while the same stretch lasts. `blocked` and `unknown` never turn busy.
- The rule feeds the idle test, the stop test and the machine-wide sleep check (other squads' agents too). The log says `bg busy:` and `bg cap:` once per stretch; `states_text` shows `<name> busy (bg shell)`.
- Rejected: a run_suite heartbeat file (covers only run_suite), a process-tree walk (Claude-internal tree, no `/proc` on Windows), an agent-declared busy marker (fails when the agent stalls). See `.claude/squads/plugin/scopes/watchdog-shell/evidence/01/01-solutions.md`.

## Consequences
- Without the hook or herdr the watchdog behaves as 0.9.5 (never worse).
- False busy is bounded: a forgotten dev server holds the watchdog quiet at most the cap per idle stretch. The token itself expires 1 h after the last hook event (`TTL_MS`), so a cap above 60 needs `TTL_MS` raised too.
- A user's own `herdr-bg` hook lines in `~/.claude/settings.json` run beside the plugin's until removed; the count is by unique task id, so the double run reads one shell.
- Plugin 0.9.6; changelog v19.
