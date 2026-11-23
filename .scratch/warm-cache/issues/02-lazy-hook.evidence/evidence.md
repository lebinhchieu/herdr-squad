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
| AC1 | `python3 tests/test_hooks_json.py` OK; hook file mode 755 |  |  |
| AC2 | `python3 tests/test_lazy_hook.py` test_matching_session... OK |  |  |
| AC3 | test_other_session..., test_second_prompt... OK |  |  |
| AC4 | read: unlink in try/except OSError |  |  |
| AC5 | session_id from tests/fixtures/squad-notify/subagent-stop.json |  |  |
| AC6 | 3 tests OK |  |  |
| AC7 | windows_safe 14, utf8_helpers 14, instructions 16 OK |  |  |

## Behaviour

- Real field name: `session_id`, from the recorded real capture `tests/fixtures/squad-notify/subagent-stop.json` (also used by `bin/squad-usage-hook`: `jq '.session_id'`). The test input uses that field. It is a capture of a SubagentStop event, not UserPromptSubmit; `session_id` is a common field of all hook events (the Stop hook reads it the same way). No UserPromptSubmit capture exists in the repo.
- Marker not deletable: the text is printed anyway, no raise; a leftover marker would fire again until removed.
- Results (each run as `python3 tests/<file>.py`): test_lazy_hook 3 OK; test_hooks_json 5 OK; test_away_hook 4 OK (grep -rl hits for squad-away-hook / hooks.json); test_windows_safe 14 OK; test_utf8_helpers 14 OK; test_instructions 16 OK.
