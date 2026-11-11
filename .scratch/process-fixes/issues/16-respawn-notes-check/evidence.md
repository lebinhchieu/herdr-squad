# Evidence 16 respawn notes check

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 missing notes: one line, exit 1, nothing started | `test_missing_notes_refuse_with_one_line_and_start_nothing` | `cd tests && python3 -m unittest test_squad_respawn` |
| AC2 notes older than 10 min: stderr warning, goes on | `test_notes_older_than_10_minutes_warn_and_go_on` (also: fresh notes give no warning) | same |
| AC3 `--force` skips both | `test_force_skips_the_old_notes_warning`, `test_force_skips_the_missing_notes_check` | same |
| AC4 100-line warning points at `squad-process rule NOTE-1` | `test_warns_when_notes_are_over_100_lines` | same |
| AC5 one test per AC; `--dry-run` as before | the four tests above + `test_dry_run_is_unchanged_without_notes`; `test_the_hand_off_passes_the_dry_run_flag` | same |

## Behaviour

- `bin/squad-respawn` parses `--dry-run` and `--force` from any position after the name. A real run (no `--dry-run`, no `--force`) first needs `roles/<name>.notes.md`: missing prints one line (file, `squad-process rule NOTE-1`, how to skip) and exits 1 before any herdr call. Older than 10 minutes (`find -mmin +10`) prints a warning on stderr and goes on.
- `--dry-run` skips both checks, so its output and exit code are as before. `--force` skips both on a real run. The pinned (< 0.6.0) hand-off still passes the original arguments on.
- The 100-line warning now says `see squad-process rule NOTE-1` (finding 9b).
- Existing respawn tests now write fresh notes first (`put_notes` in `test_squad_respawn.py`; two setup lines in `test_squadruntime.py`), because a respawn without notes now refuses.
- Ran: `test_squad_respawn` (26), `test_squadruntime` (68), `test_squad_usage_hook`, `test_squad_manager_guard`, `test_squad_start`, `test_rules_wording`, `test_squad_spawn` (1 failure: `test_a_failed_agent_start_leaves_the_old_overrides_file`, the same failure on the base commit, see evidence 09, 11). SQ-10: `test_windows_safe` 14 OK, `test_utf8_helpers` 14 OK, `test_instructions` 16 OK. Full suite not run (QA whitebox asks Chieu).
