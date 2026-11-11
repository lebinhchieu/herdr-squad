# Evidence 17 respawn event log

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 one line `{ts, agent, role, rule:"respawn"}` before the spawn (T1, T2: old line byte-identical) | `test_a_respawn_appends_one_event_line_before_the_spawn` | `cd tests && python3 -m unittest test_squad_respawn` |
| AC2 no line: refused (missing notes), no live agent, `--dry-run` | `test_no_event_when_the_run_is_refused_or_a_dry_run` (one test, three assertions). A hand-off (pinned run) never reaches the logging code: the exec comes before it (`test_the_hand_off_passes_the_dry_run_flag` already covers that path) | same |
| AC2/T4 a spawn that fails still leaves the line (the line comes before `squad-spawn`) | `test_a_spawn_that_fails_leaves_the_event` | same |
| AC3/T6 hook + guard read a mixed file | `test_the_hook_and_the_manager_guard_still_read_a_file_with_the_respawn_line` | same |
| T3 lock | `test_a_held_lock_does_not_hang_the_event_and_the_line_is_written_without_flock` (PATH without `flock`, `.lock` dir held: ~5 s, line written) | same |
| T5 unwritable log | `test_an_unwritable_log_warns_once_and_the_respawn_goes_on` | same |
| AC4 one test per AC | the tests above | same |

## Behaviour

- `bin/squad-respawn` appends `{"ts":"<UTC ms>Z","agent":<name>,"role":<role>,"rule":"respawn"}` (built with `jq -nc --arg`) to `$home/usage-events.jsonl` (scope, else goal, else squad folder) after the notes check and the live-pane check, before the rename and the `squad-spawn` call. Same append block as `bin/squad-usage-hook`: `flock`, else the atomic `mkdir` lock (stale after ~5 s). A write failure prints one warning on stderr and the respawn goes on. The pinned hand-off, refusals and `--dry-run` log nothing.
- `grep -rn usage-events bin/` outside the hook, the guard and this script: no hits (`squad-report` does not read the file). Neither reader was changed.
- Mixed-file test: hook line, guard line, then the respawn line (no `session`). `seen_keys` for `sid-1` is still `{manager-x}`; the Stop hook for `sid-1` is deduped (exit 0), for `sid-2` it still fires (exit 2).
- Comment at `bin/squad-respawn` (stat fallback) now matches the code: age shows `>10` when `stat` gives no number (QA whitebox follow-up from 16).
- Ran (SQ-10 and hits): `test_squad_respawn` 33, `test_windows_safe`, `test_utf8_helpers`, `test_instructions`, `test_squad_usage_hook`, `test_squad_manager_guard`, `test_squadruntime`, `test_squad_start`: 196 OK together. Full suite not run.
