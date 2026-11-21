# Evidence: 04 integration of 02 + 03 and promotion (ADR 0029)

## Review

AC trace (Dev) | see `## Checks`
AC1 | git log / git diff --stat | `git log --merges -1`; `git diff --name-only 8116a58 HEAD`
AC2 | 11 test files | `python3 tests/<f>.py`, test_squad_watchdog via `cd tests; python3 -m unittest test_squad_watchdog`
AC3 | live-bg-present.json, live-bg-cleared.json, live-tick-cleared.log | commands below
AC4 | docs/adr/0029-... | grep per fact below
AC5 | grep on .claude-plugin/ | below
AC6 | HANDIN names one sha | message

Branch squad/plugin/watchdog-shell/plugin-dev-watchdog-shell-1. `squad-evidence checks` exit code is in the HANDIN.

### Behaviour
**Merge (AC1).** 02 final 8116a58, then `git merge --no-ff 53ba1d2` (03), clean, no conflict, merge commit ddb0831. `git diff --name-only 8116a58 HEAD` = 03's files (plugin.json, README.md, bin/squad-watchdog, bin/squadboard_agents.py, changelog.md, 2 test files, 03's evidence.md) + the ADR + the ticket copy; nothing else.

**Tests (AC2)**, on the merge result, all OK, no skip: test_hooks_json 5, test_herdr_bg 6, test_squad_watchdog 78, test_squadboard_agents 10, test_squad_start 49, test_squad_log_message 25, test_squadtask 15, test_squadboard_inbox 12. SQ-10: test_windows_safe 14, test_utf8_helpers 14, test_instructions 16.

**Live contract (AC3)**, own pane, temp state/tasks dirs, `herdr` stubbed on PATH for the tick so no real Manager is messaged (stub log never created = no nudge):
- a. `b1.output` empty, PreToolUse-style Bash payload with `run_in_background` piped to `hooks/herdr-bg hook`.
- b. `herdr agent list > live-bg-present.json`. My row: `"name": "plugin-dev-watchdog-shell-5", "agent_status": "working", ... "tokens": {"bg": "⏵ 1 shell"}`.
- c. Note: my own row is `working` (I am running the check), so the watchdog rule (idle/done + token) cannot fire on it. The same file holds a real unedited row `plugin-tl-watchdog-shell`, `agent_status: done`, `tokens: {"bg": "⏵ 1 shell"}`. I used it: scratch home, roster = that agent, goals G1 `in progress`; `tick --herdr-json live-bg-present.json` at 10:00 and 10:10 gave exactly one log line `bg busy: plugin-tl-watchdog-shell has a background shell (⏵ 1 shell); counted as working for at most 60 min`, no `idle start`, rc 0, no herdr send.
- d. `[exited with code 0]` appended, Stop payload to the hook, `herdr agent list > live-bg-cleared.json`: my row `working`, no `tokens` key. For the idle line my row's status cannot be idle, so a copy with only `agent_status` set to `done` for my row went to `tick`: `live-tick-cleared.log`: `idle start: nobody works and goals are open (G1 x: in progress). Agents: plugin-mgr-x gone, plugin-dev-watchdog-shell-5 idle`.
- e. Cleanup: `herdr pane report-metadata "$HERDR_PANE_ID" --source herdr-bg --clear-token bg` rc 0; temp dirs removed; env vars unset. The team lead's own token in the JSON is theirs, not touched.

**ADR (AC4).** `docs/adr/0029-watchdog-counts-a-background-shell-as-work.md` is the fenced block of promote.md verbatim; no fact needed a fix, so the diff against the block is empty. Facts, each checked on the merged tree:
- `hooks/hooks.json:24` matcher `Bash|Monitor|TaskStop` and `:33` `Stop`, both run `hooks/herdr-bg hook`.
- `hooks/herdr-bg:18` `TTL_MS=3600000`; header "Needs bash, jq and herdr", silent no-op outside herdr.
- `bin/squad-watchdog:69` `BG_MAX_MIN = 60`; `:228-233` empty/invalid → 60, 0 → off.
- `bin/squad-watchdog:431` `bg busy:`, `:433` `bg cap:`; `:290` `busy (bg shell)`.
- `.claude-plugin/plugin.json` `"version": "0.9.6"`; `changelog.md:1` `## v19 — 2026-11-21`.

**Version (AC5).** `grep -rn "0\.9\.5" .claude-plugin/` empty; plugin.json says 0.9.6.

Not run: the full suite (Tech Lead's, after ASK).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `git diff --name-only 8116a58 HEAD`: 03's files + ADR + ticket copy; merge ddb0831 clean | - | - |
| AC2 | 11 files OK (counts in Behaviour) | - | - |
| AC3 | live-bg-present.json, live-bg-cleared.json, live-tick-cleared.log; one `bg busy:`, no idle start, then `idle start` after clear | - | - |
| AC4 | ADR equals promote.md block; fact greps in Behaviour | - | - |
| AC5 | `grep -rn "0\.9\.5" .claude-plugin/` empty | - | - |
