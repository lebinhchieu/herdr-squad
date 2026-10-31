# 14-final: integration phase 2

## Behaviour

Base bf7897b (14b final, contains main a55b0fc). Merged with `git merge --no-ff`, no conflicts, in this order:

| Order | Branch | Final sha | Merge commit |
|---|---|---|---|
| 1 | plugin-dev-solve-windows-26 (14d) | c070952 | 2e09462 |
| 2 | plugin-dev-solve-windows-27 (14e) | 700f649 | fac323e |
| 3 | plugin-dev-solve-windows-23 (14h sleeps) | d889f2c | 83f7212 |
| 4 | plugin-dev-solve-windows-24 (05) | eac3d93 | bd375e1 |
| 5 | plugin-dev-solve-windows-25 (08) | 2907e1a | 5279a9c |

Static checks (suite not run; the Tech Lead runs one full `--tz`):
- Diff stat: `bf7897b..merge` is 23 files. File list equals the union of the five branch diffs (SAME_FILESET). Branch stats: 6, 10, 1, 3, 3 files. The merges add nothing beyond the branches.
- `git grep` for `test_win_utf8_process`, `child_argv`, `popen_script`, `run_child` in code: no references. `tests/test_squad_start.py:16` defines its own local `run_child` (it calls `winlaunch.run_script`). The `test_utf8_helpers.py:195` hit is a docstring. Other hits are only in `.scratch` notes.
- No-write compile (`ast.parse`) of all 16 changed `.py` files: OK.
- `def test_` counts match 14b/14d/14e evidence: start 43, inbox 55, answer 32, team 26, report_cli 19, report_query 14, winlaunch 9, utf8_helpers 14, inbox_win 7, crlf 6, windows_safe 14.
- Tickets 05 and 08 set to `Status: done`, one comment line each.
- 05: PO to look at the toast once after merge.

## Review

Fresh-context sonnet review of `bf7897b..HEAD`, static only. No blocking findings. Notes:
1. `bin/squad-notify:113`: `herdr notification show` output is parsed as JSON; if it prints nothing, one stderr line is logged and the exit is still 0. Check once on real Windows (same visit as the toast look).
2. `tests/winlaunch.py` on nt passes a script without `#!` through unchanged (documented); `test_no_bare_bash` still catches bare `bash` statically.
3. `test_utf8_helpers.py` imports `InboxBase`; it has no test methods, so nothing runs twice.
No fixes needed.
