# Evidence: 02 02 herdr-bg into the plugin

## Behaviour

Branch `squad/plugin/watchdog-shell/plugin-dev-watchdog-shell-1`, commit b43a730.

Differences from `~/workspace/terminal-setup/bin/herdr-bg` (`diff`, only these three):
1. `hook`: first line `command -v jq >/dev/null 2>&1 || return 0`.
2. `summary` counts unique task ids (`seen[$1]++ { next }`), so one task recorded twice reads `1 shell`.
3. Header comment: dependencies, no-op without them, 1 h TTL vs `SQUAD_WATCHDOG_BG_MAX`, known limits.

Tests, run from `tests/`: `test_hooks_json` 5 OK, `test_herdr_bg` 6 OK, `test_windows_safe` 14 OK, `test_utf8_helpers` 14 OK, `test_instructions` 16 OK.

## Review

AC trace:
- AC1 | `git ls-files -s hooks/herdr-bg`, `bash -n`, `diff` | run in worktree
- AC2 | `tests/test_hooks_json.py::test_herdr_bg_on_bash_monitor_taskstop_and_stop`; `grep -n "chieule\|terminal-setup" hooks/hooks.json hooks/herdr-bg` empty | `cd tests; python3 -m unittest test_hooks_json`
- AC3 | `tests/test_herdr_bg.py` tests a to e | `cd tests; python3 -m unittest test_herdr_bg`
- AC4 | the five files above | `cd tests; python3 -m unittest <name>`
- AC5 | no version file in `git diff main --stat` | -

See `## Checks`.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `git ls-files -s hooks/herdr-bg` 100755; `bash -n` clean; diff vs terminal-setup = 3 named changes | `git ls-tree b43a730 hooks/herdr-bg` 100755; `bash -n` ok; `diff terminal-setup/bin/herdr-bg hooks/herdr-bg` = header, `seen[$1]++`, jq guard only | live: mode 100755, `bash -n` clean (diff is whitebox's): pass |
| AC2 | `cd tests; python3 -m unittest test_hooks_json` 5 OK; grep chieule/terminal-setup empty | `python3 -m unittest test_hooks_json` 5 OK in worktree b43a730; grep -n chieule and grep -n terminal-setup on hooks/hooks.json hooks/herdr-bg: empty; `git diff main b43a730 -- hooks/hooks.json` | live: hooks.json parsed, both entries timeout 5, no async, grep empty: pass |
| AC3 | `cd tests; python3 -m unittest test_herdr_bg` 6 OK (a, b, c, d, e env, e jq) | `python3 -m unittest test_herdr_bg` 6 OK; mutants: delete `seen[$1]++` line -> test_d FAILS, delete jq guard -> test_e_no_jq FAILS; live run with real session id and tasks dir (temp state dir): live .output kept, missing .output dropped | live: stub herdr run of a to e plus 2nd task, Monitor, ended task, no pane, herdr fails: pass |
| AC4 | windows_safe 14, utf8_helpers 14, instructions 16 OK | `python3 -m unittest test_hooks_json test_herdr_bg test_windows_safe test_utf8_helpers test_instructions` 55 OK | n/a, tests are whitebox's |
| AC5 | no version bump in diff | `git diff --stat main b43a730` has no plugin.json or changelog | live: no version file in diff: pass |

## QA whitebox

### QA whitebox 02: herdr-bg into the plugin
Sha b43a730 (based on main 804c29c). Verdict: PASS. Checks table: `checks.md` (my column).

Checked in a detached worktree (removed after), against `tasks/02.md` technical AC:
- AC1: mode 100755, `bash -n` ok, diff vs `terminal-setup/bin/herdr-bg` = header comment, `seen[$1]++ { next }` in `summary`, `command -v jq ... || return 0` in `hook`. Nothing else.
- AC2: hooks.json valid; PostToolUse `Bash|Monitor|TaskStop` and a Stop group added, timeout 5, not async; existing groups untouched; no user path in the files; new `test_hooks_json` test present.
- AC3: `test_herdr_bg` 6 OK. Mutation on a scratch copy: removing the dedupe line fails test_d, removing the jq guard fails test_e_no_jq. So both tests bite.
- AC4: the five files run together, 55 OK.
- REV-5b live run: real session id and real tasks dir (`/tmp/claude-1000/.../tasks`), temp state dir, HERDR_ENV unset (no herdr call). A task with a live `.output` and no exit marker stayed in the state file; a task whose `.output` is gone was dropped. Reconcile behaves on real files.
- `squad-evidence checks` on the ticket evidence: exit 0.

Follow-ups (not findings, no return):
1. `herdr-bg list` still prints a row per recorded line, so a task recorded twice shows twice in the popup while the token says `1 shell`. Dedupe only in `summary` was the agreed design.
2. `reconcile` keeps duplicate rows, so the state file holds both until the task ends. Harmless.

## QA blackbox

### QA blackbox 02: herdr-bg into the plugin (commit b43a730)

Method: ran `hooks/herdr-bg hook` from the worktree as a black box. Stub `herdr` on PATH logs argv; `HERDR_ENV=1`, `HERDR_PANE_ID=pane-9`, `HERDR_BG_STATE_DIR` in a temp dir; the `.output` files lie under the default `/tmp/claude-<uid>/<proj>/<session>/tasks/`. Payloads are the ticket's samples. Scratch dirs removed afterwards. No source read.

| AC | shot/live | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 mode, syntax | live | `git ls-files -s hooks/herdr-bg`; `bash -n` | `100755`; clean | pass |
| AC1 diff vs terminal-setup | - | not mine (code check, QA whitebox) | - | n/a |
| AC2 wiring | live | parsed `hooks/hooks.json`; grep `chieule\|terminal-setup` | PostToolUse `Bash\|Monitor\|TaskStop` and a matcher-less Stop group, both `"${CLAUDE_PLUGIN_ROOT}/hooks/herdr-bg" hook`, timeout 5, no async; existing SendMessage, Bash and both Stop groups still there; grep empty | pass |
| AC3a bg Bash, live output | live | Bash payload `backgroundTaskId=b1`, `b1.output` running | argv `pane report-metadata pane-9 --source herdr-bg --token bg=⏵ 1 shell --ttl-ms 3600000`, exit 0 | pass |
| AC3b exit marker + Stop | live | appended `[exited with code 0]` to the outputs, Stop payload | argv `pane report-metadata pane-9 --source herdr-bg --clear-token bg`, exit 0 | pass |
| AC3c TaskStop | live | TaskStop `task_id=b2` with b1, m1 still live | token drops `2 shell · 1 monitor` to `1 shell · 1 monitor` (that task is removed, the rest stay) | pass |
| AC3d same payload twice | live | fed the b1 payload twice | both runs `bg=⏵ 1 shell` | pass |
| AC3e no HERDR_ENV | live | unset `HERDR_ENV` | exit 0, empty output, empty argv log | pass |
| AC3e no jq | live | PATH of symlinks, no `jq` (with `id`, `date`, `awk`, ...) | exit 0, empty output, empty argv log, for a bg Bash payload and for Stop | pass |
| AC4 | - | repo guard tests: QA whitebox | - | n/a |
| AC5 | live | no version file in `git diff main --stat` (hooks, tests, ticket files only) | none | pass |
| Unhappy: 2nd task, Monitor | live | b2 then a Monitor payload `taskId=m1` | `2 shell`, then `2 shell · 1 monitor` | pass |
| Unhappy: Bash without run_in_background | live | `ls` payload | token re-sent unchanged, nothing recorded | pass |
| Unhappy: bg payload, task already ended | live | `.output` holds the exit marker | clear-token sent, no token | pass |
| Unhappy: Stop in a session with no state | live | fresh session id | clear-token sent, exit 0 | pass |
| Unhappy: no `HERDR_PANE_ID`, empty stdin, herdr not on PATH, herdr exits 3 | live | each alone | exit 0, empty output, no argv | pass |

Follow-ups (not AC):
1. Malformed stdin (`not json{`) prints a `jq: parse error` line on stderr, exit 0. Claude Code always sends valid JSON, so no effect in use.
2. With no `jq` and no `id` on PATH and the default tasks glob, it prints `herdr-bg: line 15: id: command not found` on stderr, exit 0. The ticket's thin PATH list has no `id`; with `HERDR_BG_TASKS_GLOB` set it is silent. Any real machine has `id`, so low value.

Verdict: PASS for b43a730.
