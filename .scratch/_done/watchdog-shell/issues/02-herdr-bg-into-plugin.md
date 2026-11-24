# 02 herdr-bg into the plugin
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: hooks/herdr-bg (new), hooks/hooks.json, tests/test_herdr_bg.py (new), tests/test_hooks_json.py
Goal: `../iterations/2.md`; report `../evidence/01/01-solutions.md` (option A). Branch from repo `main` (804c29c). Ticket 03 runs in parallel and reads the token this hook writes; neither edits the other's files.

First commit (FILE-11): copy `$SCOPE_DIR/tasks/02.md` and `03.md` to `.scratch/watchdog-shell/issues/` as `02-herdr-bg-into-plugin.md` and `03-watchdog-reads-bg-token.md` (this branch only; 03's Developer adds no ticket file, so no add/add conflict).

## What and why
Chieu's `herdr-bg` (bash + jq, in `~/workspace/terminal-setup/bin/herdr-bg`) records each background shell and monitor of a Claude session and reports a herdr pane token `bg=⏵ N shell`. The watchdog (ticket 03) reads that token, so the hook must ship with the plugin. Move = copy into the plugin; the terminal-setup copy stays (its `popup` key in `~/.config/herdr/config.toml` still uses it).

## Design notes (Tech Lead)
- Location `hooks/herdr-bg`, not `bin/` (decided, LC-9): it is bash, not a squad CLI; `bin/` tests scan Python and every `squad-*` name there is an agent-facing command. `git check-attr eol hooks/herdr-bg` is already `lf` from `* text=auto eol=lf`; do NOT edit `.gitattributes` (`test_windows_safe` pins its two lines).
- Faithful copy: the whole script (`hook`, `list`, `popup`) so both copies write one state format. Freeze the contract (LC-12), the popup and the watchdog depend on it: default `STATE_DIR` (`${XDG_STATE_HOME:-$HOME/.local/state}/herdr-bg`), TSV columns `id kind epoch label`, `--source herdr-bg`, token key `bg`, `TTL_MS=3600000`, env overrides `HERDR_BG_STATE_DIR`, `HERDR_BG_TASKS_GLOB`.
- Only three differences from the source are allowed, each named in `## Behaviour` of the evidence:
  1. `hook`: first line `command -v jq >/dev/null 2>&1 || return 0` (no jq = silent no-op, not a "command not found" on the host's stderr).
  2. `summary` counts unique task ids (awk `!seen[$1]++`), so the same task recorded twice reads `1 shell`. Reason: Chieu's two `~/.claude/settings.json` hook lines stay live until he removes them, and Claude Code runs both hooks of one event in parallel, so an append-time check would race.
  3. Header comment: dependencies (bash, jq, herdr), no-op without them, and a line "the token expires `TTL_MS` (1 h) after the last hook event; the watchdog's `SQUAD_WATCHDOG_BG_MAX` cannot exceed that without raising it here".
- Known limits, not AC (put one line each in the header comment): `sed -i "/^$id\t/d"` is GNU sed (macOS leaves the row until `reconcile`); two parallel hooks of one session can lose a row (no lock). Native Windows without git-bash is unverified.
- Wiring (`hooks/hooks.json`): `PostToolUse` matcher `Bash|Monitor|TaskStop` and a `Stop` entry (no matcher), command `"${CLAUDE_PLUGIN_ROOT}/hooks/herdr-bg" hook`, `timeout` 5, not async: the same as Chieu's settings lines 67 and 174. Add them as new groups; the existing `Bash` PostToolUse group (`squad-merge-record`) and both Stop groups stay as they are.
- README: ticket 03 owns every README edit of this goal (one file, one owner). This ticket does not touch it.

## Samples (REV-4)
- Hook payload shapes the script reads (live, the same hook has run on this machine for weeks): Bash `{"session_id","tool_name":"Bash","tool_input":{"command","run_in_background":true},"tool_response":{"backgroundTaskId":"b1"}}`; Monitor `tool_response.taskId`; TaskStop `tool_input.task_id`. Stop `{"session_id","hook_event_name":"Stop"}`.
- `~/workspace/terminal-setup/bin/herdr-bg.test.sh` is a working stub test of the same script: port its cases to Python (do not copy the shell file in).
- Task output, live: a running shell's `/tmp/claude-1000/*/<session>/tasks/<id>.output` has no `[exited with code` line; an ended one ends with `[exited with code N]`.

## Technical AC
1. `hooks/herdr-bg` is mode 100755 (`git ls-files -s hooks/herdr-bg`); `bash -n hooks/herdr-bg` is clean; the HANDIN quotes `diff` against `~/workspace/terminal-setup/bin/herdr-bg` and the only differences are the three named above.
2. `hooks/hooks.json` is valid JSON with the two entries above; `grep -n "chieule\|terminal-setup" hooks/hooks.json hooks/herdr-bg` is empty. `tests/test_hooks_json.py` gains one test: both entries exist (command, timeout 5, no async) and `hooks/herdr-bg` is a file. The 4 existing tests stay green unedited.
3. `tests/test_herdr_bg.py` (new, `unittest`, stub `herdr` on PATH that logs argv, `HERDR_BG_STATE_DIR` and `HERDR_BG_TASKS_GLOB` inside a temp dir, `HERDR_ENV=1`, `HERDR_PANE_ID` set), one test per risk, no matrix:
   - (a) Bash payload with `backgroundTaskId` + live `<id>.output` → argv has `pane report-metadata <pane> --source herdr-bg --token bg=⏵ 1 shell --ttl-ms 3600000`.
   - (b) the `.output` then holds `[exited with code 0]`, a Stop payload → argv has `--clear-token bg`.
   - (c) `TaskStop` for the id → `--clear-token bg`.
   - (d) the same Bash payload fed twice → token text still `⏵ 1 shell`.
   - (e) `HERDR_ENV` unset → exit 0, empty stdout and stderr, empty argv log. Same with `jq` not on PATH (PATH with only a dir that holds `bash`-less essentials: use a temp dir with symlinks to `bash`, `date`, `mktemp`, `grep`, `awk`, `sed`, `mv`, `touch`, `mkdir`, `head`, `cat`, but no `jq`).
   - The class skips with a clear reason when `bash` or `jq` is missing, and fails instead when `SQUAD_REQUIRE_CLAUDE=1` (the pattern of `tests/test_po_inbox_mod.py`).
4. SQ-10 does not apply (no `bin/` change, no printed `bin/` text). The Developer runs: `test_hooks_json`, `test_herdr_bg`, `test_windows_safe`, `test_utf8_helpers`, `test_instructions` (cheap, guard the repo), and quotes the result in `## Behaviour`.
5. No version bump here (rides 03, SQ-5).

## Dry-run on base 804c29c (SQ-15)
- `test_hooks_json` 4 OK. `test_windows_safe` 14, `test_utf8_helpers` 14, `test_instructions` 16 OK.
- `grep -n "chieule\|terminal-setup" hooks/hooks.json` empty; `git ls-files -s hooks/herdr-bg` empty; `tests/test_herdr_bg.py` absent (the new AC fail on base as they must).
- Known failing on base: none.

## Deploy plan (Tech Lead writes, Chieu runs; LC-13)
1. Merge 02 and 03 together; update the plugin (0.9.6).
2. Hooks load at session start: restart live Claude sessions (or wait for the next one).
3. Only then remove the two `herdr-bg hook` entries from `~/.claude/settings.json` (lines 67 and 174, PostToolUse `Bash|Monitor|TaskStop` and Stop). Doing it earlier loses the token until the restart; doing it later is harmless (counted once).
4. Keep `~/workspace/terminal-setup/bin/herdr-bg` for the `popup` key, or repoint `~/.config/herdr/config.toml` line 73 to the plugin copy.
5. Rollback: re-add the two settings lines, revert the merge. No data to migrate; the state dir is untouched.
6. Check after deploy: in a session run a background `sleep 120`; `herdr agent list` shows `tokens: {"bg": "⏵ 1 shell"}` for it; after the sleep ends and the next tool call, the token is gone.

## Evidence
`evidence.md` next to this ticket (EVID-1), `## Behaviour` with the diff summary and the test output.
