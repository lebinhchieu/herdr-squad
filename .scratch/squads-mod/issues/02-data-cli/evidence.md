# 02 evidence

## Review

AC trace (tech-ac.md T1.x, S1-S4, G1-G3; spec AC1-AC4 data side). Run: `cd tests && python3 -m unittest test_squadtree test_squadcommands`.

| AC | Test | How run |
|---|---|---|
| T1.1 golden | `test_squadtree.TreeTests.test_T1_1_golden_herdr_readable_and_down` (tree.json herdr up, tree-herdr-down.json herdr down; Tech Lead DECISION 02) | unittest; regen: `python3 tests/test_squadtree.py --regen` |
| T1.2 / S1 read-only | `test_T1_2_read_only_run_changes_nothing` | unittest |
| T1.3 discovery | `test_T1_3_discovery` (SQUAD_DIR, worktree, none, flat, bad --repo, bad flag exit 2) | unittest |
| T1.4 / T1.4b | `test_T1_4b_field_shape_and_facts_equal_the_board` | unittest |
| T1.5 | `test_T1_5_light_rows_...`, `test_T1_5b_...` | unittest |
| T1.6 | `test_T1_6_herdr_runs_once_...` | unittest |
| T1.7 perf | measured below | `time python3 bin/squad-tree --repo .` |
| T1.8 | `NextStepTests.test_T1_8_*` | unittest |
| T1.9 a-j | `test_squadcommands.CommandTests.test_T1_9*` | unittest |
| T1.10 / T1.11 | `test_T1_10_T1_11_broken_files_and_hostile_text_do_not_crash` | unittest |
| T1.12 | `test_T1_12_the_copied_texts_run_for_real` | unittest |
| G1 / G2 / S2-S3 | stdlib only; `encoding="utf-8"`; `squadio.utf8_stdio()`; names go through NAME_RE | SQ-10 run below |

## Behaviour

- Real run on this repo (3 squads, 25 scopes, herdr absent): 0.10 s.
- Defect found by T1.12: `squad-report ... --squad NAME` refuses (`no such squad`) without `$SQUAD_DIR`, i.e. in Chieu's plain shell. So `report` and `report-status` texts carry the squad folder path: `squad-report api --squad /abs/.claude/squads/plugin`.
- `report-status` answers by exit code (0 fresh, 3 stale, 4 missing); the test accepts those.
- SQ-10: `python3 -m unittest test_windows_safe test_utf8_helpers test_instructions` plus the new files: 64 tests OK.
- `test_squadboard_list` has one failure at the base commit too (`last_active` from real branch times); `test_squadboard_demo` browser tests fail on `1 d ago` (clock). Neither touched by this diff.
