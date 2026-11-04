# Evidence 37: squad-board --demo (wrapper, without the label step)

## Behaviour
`bin/squad-board --demo [--port N] [--no-open]` copies the fixture to `/tmp/squad-board-demo-*` (times = now), extends the copy
in code (`bin/squadboard_demo.py:extend`), points HOME, USERPROFILE and CLAUDE_CONFIG_DIR into the copy, drops `SQUAD_*`,
does `chdir` into the copy, sets `GIT_CEILING_DIRECTORIES`, prints `demo: sample data in <path>` and runs `squadboard.main`
on goal `alpha`. The copy is removed in `finally` (Ctrl-C and SIGTERM). The fixture is not edited.
Run by hand on port 8791-8793: goal `alpha` and scope `checkout` answer every panel route with rows, `unknown == []`.

## Open gaps (HANDIN)
- T37.AC6, AC12 (label, page checks) and T37.TA4: wait for the label step (37b, after 34 and 36). Not built.
- SIGKILL leaves the copy in the temp dir (out of scope).
- `test_squadboard_list::test_T04_AC1_rows_order_and_done_list` fails on the clean base too (last_active 09:30:49 vs 09:30:00); not caused by 37.

## AC table
| Id | Shown by |
|---|---|
| T37.AC1 | bin/squadboard_demo.py:run (refusals, exit codes); tests/test_squadboard_demo.py::Flags::test_T37_TA5_AC1_exit_codes |
| T37.AC2, AC3 | test_squadboard_demo.py::RunningDemo::test_T37_TA2_AC2_AC5_every_panel_has_content (goal and scope views). Empty-board texts: panel API rows > 0 |
| T37.AC4 | same test, nine stages in `checkout` |
| T37.AC5 | same test: question + blocked agent, working/idle/blocked, 11 h gap, DST |
| T37.AC6 | OPEN (label step) |
| T37.AC7 | ::test_T37_TA1_AC7_AC8_nothing_real (REALSQUAD name in no API answer) |
| T37.AC8 | ::test_T37_TA6_AC8_AC10_read_only_and_cleaned |
| T37.AC9 | bin/squadboard_demo.py:build (new copy per start); test_T37_TA1_copy_removed_when_main_raises |
| T37.AC10 | Flags::test_T37_TA5_AC10_sigterm_removes_copy |
| T37.AC11 | ::test_T37_TA3_AC11_ages_are_recent ("40 min") |
| T37.AC12 | OPEN (QA blackbox against the running demo; needs 35/36) |
| T37.TA1 | ::test_T37_TA1_AC7_AC8_nothing_real, Flags::test_T37_TA1_copy_removed_when_main_raises |
| T37.TA2 | ::test_T37_TA2_AC2_AC5_every_panel_has_content (routes read from templates/board/*.js by pattern, fails if < 6) |
| T37.TA3 | ::test_T37_TA3_AC11_ages_are_recent |
| T37.TA4 | OPEN until 37b |
| T37.TA5 | Flags::test_T37_TA5_AC1_exit_codes, ::test_T37_TA5_AC10_sigterm_removes_copy, ::test_T37_TA5_help_documents_demo |
| T37.TA6 | ::test_T37_TA6_AC8_AC10_read_only_and_cleaned (git status, fixture hash, HOME hash) |
| T37.TA7 | grep run: test_board_fixtures, test_squadboard_{active,agents,files,inbox,list,server,tasks}, test_squad_{respawn,start}, test_squadruntime; test_windows_safe, test_no_bare_bash, test_old_language_inventory pass |
