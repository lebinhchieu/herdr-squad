# Evidence 13: GOAL-6b follows SUITE-1

## Review

AC trace:

- AC1 | `templates/squad/process/goal.md` line 69 (`git diff 1fc0022 -- templates/squad/process/goal.md`: 1 line changed) | `git diff --stat 1fc0022`
- AC2 | `grep -rn 'full suite' templates/` (hits below) | run from the worktree root
- AC3 | `tests/test_dev_rules_size.py` (budget +59 B), plus hit files below | `python3 -B -m unittest discover -s tests -p <file>` with the squad env vars unset

AC2 hits, all checked:

- suites.md:8 (SUITE-1) states the ask rule itself.
- suites.md:16 (SUITE-1b), 37 (SUITE-2d) require the ASK and Chieu's yes.
- suites.md:23, 30, 44, 51, 58 (SUITE-2 variants, SUITE-3) say who owns the suite and that others run only touched files; no run without the ask.
- suites.md:65 (SUITE-4b) says "Once [SUITE-1] allows it".
- sizes.md:70 names who owns the full suite per team; no run.
- goal.md:69: was the contradiction; fixed (AC1). No other hit contradicts.

Tests run (each file alone, grep hits of `GOAL-6b` / `goal.md` in `tests/`):

- test_dev_rules_size: 9 OK after budget update. It failed before it: GOAL-6b grew every composed Manager size by 59 B, so the 6 pinned limits moved +59.
- test_small_files_equivalence, test_templates, test_instructions, test_squadcompose, test_squad_close, test_squad_team, test_squad_start, test_squadinbox, test_squad_watchdog, test_squadruntime: OK.
- test_squadboard_list: 1 failure, `test_T04_AC1_rows_order_and_done_list` (`last_active` is now, not 2026-11-04). Same failure on 1fc0022 without my change; not related.
- No full suite run.

## Behaviour

- AC1: `grep -n 'GOAL-6b' -A5 templates/squad/process/goal.md` now ends: "the suite owner then follows [SUITE-1]: targeted tests by default, a full run only after Chieu's yes ([WHO-2b], [WHO-2c], [WHO-2f])." Saw: one line changed.
- AC2: `grep -rn 'full suite' templates/` after the change: goal.md:69 no longer says "runs the full suite after"; no other line runs it without the ask.
- AC3: commands above; all touched and hit files OK except the pre-existing failure.
