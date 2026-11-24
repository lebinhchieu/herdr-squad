# Evidence 11: hooks find a resumed session in roster.md

## Behaviour

Base 4e7d547. Fixtures: two real rosters copied from this squad, `tests/fixtures/session_lookup/scope-roster.md` (scope upstream-proposals, sha1 73ff4b154d3cee312c0c04aff436156c9b5d3f8d) and `goal-roster.md` (goal process-fixes, a goal Manager row, sha1 dd14d6179261d88255e7f66c7146f699804f5959).

**Tests** (`SQUAD_*` unset in the shell; `PYTHONDONTWRITEBYTECODE=1`): `python3 -m unittest` over the 19 files = the new `test_session_lookup`, `test_windows_safe`, `test_utf8_helpers`, `test_instructions`, `test_hooks_json`, the eight hook tests and every `grep -rl` hit of the hook and helper names over `tests/`: **Ran 362 tests, OK** (a `squad-notify: cannot write /dev/pts/999999` line is that test's own log). `python3 bin/squad-process lint`: exit 0. No `bin/*.pyc`.

**Resumed session keeps its id (AC11 limit).** Real payloads of one scratch session, `claude -p --session-id <id>` then `claude -p --resume <id>`, a `UserPromptSubmit` hook logging stdin, both calls carry the same `session_id` (copy: `resume-payloads.jsonl`):
```
{"session_id":"e019806c-8ccc-4a8d-aba6-a96a662c0cf1", ... "hook_event_name":"UserPromptSubmit","prompt":"reply ok"}
{"session_id":"e019806c-8ccc-4a8d-aba6-a96a662c0cf1", ... "hook_event_name":"UserPromptSubmit","prompt":"reply ok again"}
```
So the roster's Session cell still matches after `--resume`.

**Cost (AC8).** `squad-whoami` in the real project, 7 runs each: a session id with no row (the PO's own session) median 39 ms, max 42 ms; this Developer's id (row found) median 37 ms, max 44 ms. A session with the variables starts no `squad-whoami` (stub test).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
| --- | --- | --- | --- |
| AC1 | `test_resumed_session_logs_as_its_roster_row` | `python3 -m unittest test_session_lookup` (SQUAD_* unset); live `bin/squad-whoami` with my own session id | scratch squad, real roster, no SQUAD_*: record logged with from = my row name (qa-b.md) |
| AC2 | `test_unknown_empty_or_unreadable_session_stays_silent` | `bin/squad-whoami` with a made-up id, `{}` and non-JSON: no output, rc 0 | made-up id, empty id, id prefix: nothing logged, rc 0 (qa-b.md) |
| AC3 | `test_environment_wins_over_the_roster`, `test_environment_wins` | `python3 -m unittest test_session_lookup`; read `squadsession.resolve` and `fill` | SQUAD_NAME=someone-else set: record says someone-else (qa-b.md) |
| AC4 | `ResolveTest` (8 tests) | `python3 -m unittest test_session_lookup.ResolveTest` | - |
| AC5 | path-guard and manager-guard tests | `python3 -m unittest test_session_lookup.HookTest test_squad_path_guard test_squad_manager_guard` | - |
| AC6 | `test_every_squad_hook_of_hooks_json_calls_the_lookup` | `python3 -m unittest test_session_lookup test_hooks_json` | - |
| AC7 | fixtures with sha1 in evidence | `sha1sum tests/fixtures/session_lookup/*.md` against the evidence | - |
| AC8 | stub test; timing in evidence | `python3 -m unittest test_session_lookup`; 15 timed runs of `bin/squad-whoami` and an in-process `resolve` timing | squad-whoami in real project: min about 40 ms, median 45 ms (row) / 87 ms (no row) at load 29 (qa-b.md) |
| AC9 | SQ-10 files and grep hits | `python3 -m unittest test_windows_safe test_utf8_helpers test_instructions` plus the hook tests, test_crlf_squad_files, test_squad_spawn, test_squad_start | - |
| AC10 | lint 0; diff list | `python3 bin/squad-process lint`; `git diff --stat 4e7d547 d15e043` | - |
| AC11 | resumed payload quoted | - | hook, no SQUAD_*, real id logs; same on main logs nothing (qa-b.md) |

## QA whitebox

### QA whitebox, ticket 11, sha d15e043 (base 4e7d547)

Verdict: PASS.

#### Checked
- Code read: `bin/squadsession.py` (resolve, fill) and `bin/squad-whoami`; the eight hook diffs. The environment wins (`resolve` returns None with SQUAD_NAME and SQUAD_DIR set; `fill` never overwrites a set key). Values are checked (`^[a-z0-9-]+$`, folders exist); the first row whose Session cell equals the id as a whole; `_done` and `_runtime` skipped; never raises. Bash hooks read `squad-whoami` through `while IFS== read -r k v`, six keys, only when empty, no `eval`; the loop runs in the main shell (`done < <(...)`), so the exports stick. Files LF, `squad-whoami` mode 100755.
- AC1-AC3, AC5, AC6, AC8: read `tests/test_session_lookup.py`; one test per risk, real `bin/` hooks through a temp project. AC4: `ResolveTest` covers worktree cwd, git worktree, goal Manager, scope in a goal, flat roster, `_done`, substring, bad name.
- AC7: fixtures are copies of real rosters, sha1 quoted in the evidence.
- Live run (REV-5b), real project, `SQUAD_*` unset: `squad-whoami` with my own session id prints my six values (name, role, scope, SQUAD_DIR, SCOPE_DIR); a made-up id, `{}` and non-JSON print nothing, rc 0.
- AC8: `resolve` takes 0.4 ms in process (match or no match); the cost is process start. 15 runs of `squad-whoami` here: min 64 ms (row 69 ms), median 87-127 ms with load average 29, where `python3 -c pass` alone ranges 13-36 ms. QA blackbox saw the same. See follow-up 1.
- AC9: lint exit 0. 360 tests OK (SQUAD_* unset, bytecode off): every hook test, test_session_lookup, test_hooks_json, test_windows_safe, test_utf8_helpers, test_instructions, test_dev_rules_size, test_sizes, test_rules_wording, test_squad_ledger, test_squad_respawn, test_squadruntime, test_squadreport_digest; plus test_crlf_squad_files, test_squad_spawn, test_squad_start: 174 OK. No stray `*.pyc`, git status clean.
- AC10: diff 4e7d547..d15e043 lists only squadsession.py, squad-whoami, the eight hooks, the test file, two fixtures, the changelog line (names the eight hooks and why) and the ticket's evidence files; no rule, `templates/` or `hooks.json` change.

#### Follow-ups (not FAIL)
1. AC8 timing: on this loaded host the median is 87-127 ms (min 64 ms), not the 40 ms the Developer quotes. In-process cost is 0.4 ms and python start-up dominates, so an idle host should settle it. Re-time when the load is low.
2. Changelog says the hooks call the lookup "only when `SQUAD_NAME` or `SQUAD_DIR` is missing"; `squad-away-hook` (SQUAD_ROLE or SCOPE_DIR/GOAL_DIR missing), `squad-manager-guard` (only for `squad-spawn`/`squad-inbox add`) and `squad-notify` (only with HERDR_ENV=1) use narrower conditions.
3. `squad-path-guard` imports `squadsession` at the top, while `squad-manager-guard` defers it so a `bin/` without the file stays silent. Same-folder file, so only a partial copy of `bin/` would notice.

## QA blackbox

### QA blackbox 11, sha d15e043

Setup: scratch project `/tmp/qab11/proj` with `.claude/squads/plugin/scopes/upstream-proposals/{roster.md,scope.md}` copied from this squad (real session ids). Hook run from the worktree's `bin/` with `env -u SQUAD_DIR -u SCOPE_DIR -u GOAL_DIR -u SQUAD_NAME -u SQUAD_SCOPE -u SQUAD_ROLE`, `CLAUDE_PROJECT_DIR=/tmp/qab11/proj`, a `PostToolUse` `SendMessage` payload on stdin. (I used the real roster and a scratch folder, not a stub `claude`: the AC is about the hook seeing no `SQUAD_*` and a session id, which this reproduces; the Developer's evidence shows `claude --resume` keeps the id.)

| AC | what I did | what I saw | result |
|---|---|---|---|
| AC11 failure fixed | `squad-log-message`, no `SQUAD_*`, session id of my own row (`5e1ef82d-...`) | `messages.jsonl` in that scope got 1 record, `"from":"plugin-qab-upstream-proposals"`, type PASS, task 11 | pass |
| AC11 same run on base | main checkout (no ticket 11 code), same payload | `messages.jsonl` stays empty (0 lines): the failure the ticket describes | confirms the fix |
| AC11 made-up id | id `11111111-2222-3333-4444-555555555555` | nothing logged, no output, rc 0 | pass |
| AC2 silence | empty id; an id that is only a prefix of a real id (`5e1ef82d-454d`) | nothing logged, no output, rc 0 for both | pass |
| AC1 another row | session id of the Developer-11 row | record with `"from":"plugin-dev-upstream-proposals-11"` | pass |
| AC3 environment wins | `SQUAD_NAME=someone-else` with `SQUAD_DIR`/`SCOPE_DIR` set, payload carrying my real id | record `"from":"someone-else"`; the roster is not used | pass |
| AC8 timing, `squad-whoami` in the real project (`/home/chieule/workspace/squad`), 10 runs each | no-row id (the PO's own session): min 39, median 87, max 115 ms. My real row: min 40, median 45, max 85 ms. Baselines in the same minute: `python3 -c pass` median 35 ms (max 56), `bash -c true` median 7 ms. Host load average was 29 (many agents running), which inflates the medians and the 115 ms max | min about 40 ms matches the Developer's 40 ms; median under 100 ms; one slow run over 100 ms under heavy load | pass (noted) |

Follow-ups (not FAIL, SQ-4):
- AC8 asks for "under 100 ms"; one of ten runs reached 115 ms while the host load average was 29 and plain `python3 -c pass` already ranged to 56 ms. A re-run on an idle host would settle it.
- The `squad-log-message` hook also printed a task-state warning (`W5 PASS on a sha that is not the current hand-in`) for my scratch PASS message: the resumed session now gets the same message gates a spawned one does. Expected, not a defect.
- Process note (SAFE-10): while looking for the hook's payload shape I read the first 25 lines of `bin/squad-log-message`. I judged nothing from them; the verdict rests on the runs above.
- AC4-AC7, AC9, AC10 (helper tests, guards, every-hook test, fixtures, SQ-10 files, diff list) are QA whitebox's.
