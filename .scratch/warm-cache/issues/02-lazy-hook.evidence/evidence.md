
sha: ee5835c
## Review

Checks: see `## Checks`.

AC trace:
- AC1 | bin/squad-lazy-hook, hooks/hooks.json (second UserPromptSubmit entry), `ls -l` mode 755 | test_hooks_json.py, test_away_hook.py green
- AC2 | tests/test_lazy_hook.py::test_matching_session_gets_text_and_marker_goes | `python3 tests/test_lazy_hook.py`
- AC3 | test_other_session_or_no_marker_is_silent_and_keeps_marker, test_second_prompt_is_silent | same
- AC4 | `marker.unlink()` inside try/except OSError, text printed either way | read bin/squad-lazy-hook
- AC5 | session id field named in Behaviour | grep session_id tests/fixtures/squad-notify/subagent-stop.json
- AC6 | three tests, one per behaviour | `python3 tests/test_lazy_hook.py`
- AC7 | no network, subprocess, herdr; pathlib | test_windows_safe, test_utf8_helpers, test_instructions

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 tests/test_hooks_json.py` OK; hook file mode 755 | ls-tree 100755, hooks.json diff one entry, test_hooks_json OK | live: mode 755, two UserPromptSubmit entries |
| AC2 | `python3 tests/test_lazy_hook.py` test_matching_session... OK | test_lazy_hook 3 OK, home order read | live: C5 text, marker gone, Manager role, home order |
| AC3 | test_other_session..., test_second_prompt... OK | scratch runs: bad JSON, empty marker, unset env silent rc 0 | live: different session, no marker, bad stdin, 2nd prompt silent |
| AC4 | read: unlink in try/except OSError | chmod a-w roles: text once, marker stays, rc 0 | live: chmod 555 roles: text printed, rc 0 |
| AC5 | session_id from tests/fixtures/squad-notify/subagent-stop.json | session_id in subagent-stop.json; confirm live | read Behaviour: session_id, no UPS capture; live check later |
| AC6 | 3 tests OK | 3 tests, test_hooks_json 5 OK | live: test_lazy_hook 3 OK, test_hooks_json 5 OK |
| AC7 | windows_safe 14, utf8_helpers 14, instructions 16 OK | windows_safe 14, utf8 14, instructions 16 OK | covered by QA whitebox |

## Behaviour

- Real field name: `session_id`, from the recorded real capture `tests/fixtures/squad-notify/subagent-stop.json` (also used by `bin/squad-usage-hook`: `jq '.session_id'`). The test input uses that field. It is a capture of a SubagentStop event, not UserPromptSubmit; `session_id` is a common field of all hook events (the Stop hook reads it the same way). No UserPromptSubmit capture exists in the repo.
- Marker not deletable: the text is printed anyway, no raise; a leftover marker would fire again until removed.
- Results (each run as `python3 tests/<file>.py`): test_lazy_hook 3 OK; test_hooks_json 5 OK; test_away_hook 4 OK (grep -rl hits for squad-away-hook / hooks.json); test_windows_safe 14 OK; test_utf8_helpers 14 OK; test_instructions 16 OK.

## QA whitebox

### QA whitebox 02 — sha ee5835c — PASS

Checked in a throwaway detached worktree (removed after). No herdr, no live names.

#### Checks (my column)
| AC | Check | Result |
|---|---|---|
| AC1 | `git ls-tree ee5835c bin/squad-lazy-hook` = 100755; read file (utf8_stdio, main in try/except, exit 0); `git diff main ee5835c -- hooks/hooks.json` = one added entry, away hook untouched; `python3 tests/test_hooks_json.py` | OK |
| AC2 | `python3 tests/test_lazy_hook.py` (3 OK); read hook: home order SCOPE/GOAL/SQUAD, marker roles/<name>.lazy, text matches design.md C5 | OK |
| AC3 | scratch dir runs: stdin `notjson`, stdin `[1]`, empty marker, SCOPE_DIR/SQUAD_NAME empty, non-UTF8 marker: all silent rc=0; other session keeps marker (test) | OK |
| AC3 | SQUAD_DIR-only home gives text and removes marker | OK |
| AC4 | `chmod a-w roles/`, matching session: text printed, marker stays, rc=0 | OK |
| AC5 | `session_id` in tests/fixtures/squad-notify/subagent-stop.json (SubagentStop capture; AC allows "a capture"); named in Behaviour | OK, see follow-up |
| AC6 | 3 tests, one per behaviour; test_hooks_json not edited, 5 OK | OK |
| AC7 | no network/subprocess in hook; pathlib; `python3 tests/test_windows_safe.py` 14, `test_utf8_helpers.py` 14, `test_instructions.py` 16 OK; `test_away_hook.py` 4 OK; `grep -rl 'squad-away-hook\|hooks.json\|squad-lazy-hook\|UserPromptSubmit' tests/` hits = the three files run | OK |
| evidence | `squad-evidence checks .../02-lazy-hook.evidence/evidence.md` exit 0 | OK |

#### Findings
None breaking.

#### Follow-ups (not FAIL, SQ-4)
- No real UserPromptSubmit capture in the repo; `session_id` is a common hook field and the SubagentStop capture shows it. Worth confirming once live (first real lazy respawn) that UserPromptSubmit input carries `session_id`.
- Evidence folder is `02-lazy-hook.evidence/` (old style, still read, EVID-1) while the ticket reads "evidence next to it"; SQ-20 check passed on it.

## QA blackbox

### QA blackbox: ticket 02 (squad-lazy-hook), sha ee5835c

Method: `live`. The hook was run as a black box (stdin JSON, env vars, temp dir under /tmp, no herdr, no live names). The temp dir was removed afterwards. Source code was not read. Registration was checked via `jq` on `hooks/hooks.json`.

| AC | How | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 executable, second UserPromptSubmit entry | live | `ls -l bin/squad-lazy-hook`; `jq .hooks.UserPromptSubmit hooks/hooks.json` | mode 755; two entries: `squad-away-hook` (unchanged) then `squad-lazy-hook` | pass |
| AC2 match gives C5 text, deletes marker, every role | live | marker `roles/n.lazy`=SESS1, stdin `{"session_id":"SESS1"}`, `SQUAD_ROLE=manager`, scope path with a space | one JSON `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"You were respawned ... read your notes <home>/roles/n.notes.md ... rules attached (<home>/roles/n.rules.md); read no other process file. Then answer this message."}}`, exit 0, marker gone | pass |
| AC2 home order SCOPE > GOAL > SQUAD | live | markers in all three homes; ran with all set, then without SCOPE, then SQUAD only | each run used and consumed only the first home's marker | pass |
| AC3 silent: different session | live | marker SESS1, stdin session OLD | no output, exit 0, marker kept | pass |
| AC3 silent: no marker; name unset; home unset; stdin not JSON / empty / array / `{}` / binary; empty marker | live | each case in turn | no output, exit 0 each time, marker left alone | pass |
| AC3 second prompt | live | matched prompt, then the same stdin again | second run silent, exit 0 | pass |
| AC3 extra: name `../evil` | live | marker outside roles/ | silent, marker untouched | pass |
| AC4 marker cannot be deleted | live | `chmod 555 roles/`, matching prompt | text printed, exit 0, empty stderr, marker remains | pass |
| Extra: CRLF / no-newline marker, unicode name and path (`LANG=C`) | live | markers `SID\r\n`, `SID`, `ré.lazy` in `dự án/` | text printed and marker consumed in each | pass |
| AC5 real field name | shot | read the Developer's `## Behaviour` | `session_id`, from a recorded SubagentStop capture; no UserPromptSubmit capture in the repo, and the Developer says so | pass (see follow-up) |
| AC6 tests | live | `python3 tests/test_lazy_hook.py`; `python3 tests/test_hooks_json.py` | 3 OK; 5 OK | pass |
| AC7 windows-safe / utf8 / instructions | shot | the Developer's quoted results (14 / 14 / 16 OK) were not re-run by me | n/a | covered by QA whitebox |

Verdict: PASS.

Follow-ups (not blocking):
- The one first-hand check that `session_id` in a real UserPromptSubmit input equals the id `squad-spawn --session-id` passes belongs to the first live lazy respawn after merge (ticket 04 integration). If the ids differ, the hook stays silent by design, which is safe but means no instruction.
