# Evidence 14 squad-usage counts a Bash first action and shows the line

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 Bash fallback sets first action; reads never | `test_a_state_changing_bash_call_is_the_first_action_when_no_action_tool_ran` (a read first, then a listed call; 3 counted and 6 not counted commands; no command = read) | `cd tests && python3 -m unittest test_squad_usage` |
| AC2 order: earlier of tool or Bash wins; reads only = None, 180k | `test_whichever_of_an_action_tool_or_a_bash_action_comes_first_sets_the_line` | same |
| AC3 table columns `1st act`, `line` after `last ctx`; `--check` unchanged | `test_table_shows_the_first_action_context_and_the_line` (header, `-`, 180k cap, no-transcript row width); the existing `--check` tests are untouched | same |
| AC4 one test per AC, small fixture | `turn()` got a `cmd` argument; three new tests above | same |
| T10 real roster | table below | `python3 bin/squad-usage --squad-dir $GOAL_DIR` |

## Behaviour

- AC1: `is_action` in `bin/squad-usage` counts a Bash call whose first word (basename) is in `ACTION_BASH`, or `git commit` / `git merge`. One leading `cd DIR &&` is skipped. An env prefix, `git -C d commit`, `ls squad-spawn`, `echo git commit`, `cat x && squad-close` are reads. A missing `input` or `command` is a read.
- AC2: one pass, the first call of either kind sets `first_action`; a later one does not move it. Subagent lines are skipped as before.
- AC3: new columns right after `last ctx`; `-` when no first action; `line` = `respawn_line`. The `no transcript` row has two more `-`. A footnote line explains both columns. Existing tests that read the table by index moved `out` from column 5 to 7.
- T7: `summarize_agent` keeps the newest session's `first_action`, so the row shows the newest session's line.
- Real roster (goal process-fixes, read-only):

```
agent                       model/effort            turns  peak ctx  last ctx  1st act  line  out   expiries  compactions  subagents
plugin-mgr-process-fixes    claude-sonnet-5-5/high  386    153k      153k      87k      137k  201k  3         0            0
plugin-coach-process-fixes  claude-sonnet-5-5/high  21     73k       73k       59k      109k  34k   0         0            0
```

  The Manager row has a first action (87k) and a line (137k) below 180k; before this change its line was 180k. Scope roster (line-visible): `plugin-qab-line-visible` has no action yet and shows `-` and `180k`.
- Tests run (targeted): `test_squad_usage` 26 OK; hits of `first_action|respawn_line|last ctx|ACTION_TOOLS` over `tests/` = only that file; also `test_squad_manager_guard` 25, `test_squad_usage_hook` 10, `test_squad_respawn` 21, `test_crlf_squad_files` 6 (reads the table). SQ-10 files: `test_windows_safe` 14, `test_utf8_helpers` 14, `test_instructions` 16, all OK. Full suite not run.
