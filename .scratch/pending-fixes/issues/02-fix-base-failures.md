# Fix the tests that fail on main: squadboard date fixtures, test_no_bare_bash, po_inbox_mod plugin test
Duties: Developer builds and writes design notes and technical AC with QA whitebox; QA whitebox code check; QA blackbox behaviour check; hand in to both QAs
Files: tests/test_squadboard_list.py, tests/test_squadboard_demo.py, tests/test_squadboard_panels.py, tests/test_no_bare_bash.py (or its list), hooks/po-inbox/ (plugin test)
Status: ready
After: none

Ticket path: .scratch/pending-fixes/issues/02-fix-base-failures.md (the Developer commits this text there on its branch, FILE-11).
Touched files are an estimate (LC-9b); a change re-issues this file.
Status: needs-triage
Type: task
Source: tl-always E4 (a), Chieu asked for one fix ticket in the next scope (SQ-17). Triage: tl-always evidence/suite-triage.md, "Fails on base too".

## Problem
These fail on main a3a44d8 and in every full-suite run, so each scope re-checks and excuses them:
- `tests/test_squadboard_list.py` T04_AC1, `test_squadboard_demo.py` T37_AC9 and T37_AC11, `test_squadboard_panels.py` T12 and T14: fixture dates go stale ("18 d ago", last_active), listed in 5 earlier scopes.
- `test_no_bare_bash`: `test_herdr_bg.py` (came with the watchdog-shell merge a3a44d8) is not in its conversion list.
- `test_po_inbox_mod` `test_plugin_test_passes`: the bun plugin test fails on main.

## AC (draft; the next scope's Tech Lead or Developer settles the technical AC)
- AC1 Each named test passes on the fix sha, with no new skips and no test deleted.
- AC2 The squadboard tests no longer depend on today's date (a fixed clock or relative dates); `## Review` names how.
- AC3 `## Review` names the cause of each of the other two (code defect or stale test).
- AC4 Targeted tests (`grep -rl` hits for the touched files) pass.

## Base dry run (SQ-15, main 432b8ea, Manager)
Outputs: $SCOPE_DIR/evidence/base/<file>.txt (run as `python3 -m unittest discover -s tests -p <file>.py`).
Fail on base, as this ticket says (the targets): test_squadboard_list::test_T04_AC1_rows_order_and_done_list; test_squadboard_demo::test_T37_AC11_no_age_in_days_in_the_rendered_demo; test_squadboard_panels::test_T12_AC1_AC3_AC5_AC10_inbox_row_options_recommended_copy_exact_and_no_write_labels and ::test_T14_AC1_AC2_TA3_rows_with_kind_and_local_time_links_open_in_vscode_not_a_new_tab; test_no_bare_bash::test_no_test_outside_the_conversion_list_launches_a_bare_bash; test_po_inbox_mod::test_plugin_test_passes.
T37_AC9 passed on base (date-dependent; AC2 still covers it).
Known failing on base: tests/test_squadboard_demo.py::test_T37_TA6_AC8_AC10_read_only_and_cleaned (git status saw a transient untracked `.claude/` while squad agents were spawning; not in scope, no FAIL).

## Comments
