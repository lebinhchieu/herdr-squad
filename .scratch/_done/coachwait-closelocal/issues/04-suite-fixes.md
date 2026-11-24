# 04 Fix 02's suite failures on the integrated tree
Status: ready-for-agent
Type: task

Duties: put design notes in this file; business AC are the ticket; `BLOCKED 04` on a doubt. Cite [REV-13b] hand-in, [EVID-2d] evidence. Defect class (returned 02): a change to squad-spawn output or the composed rules breaks tests outside the ones you ran; before hand-in run `python3 -m unittest` for every test file that grep finds mentioning `squad-spawn`, `warning:` or the golden (`test_utf8_helpers`, `test_squadsettings`, `test_qab_optional`, plus the 3 you touched). QA whitebox runs the full suite after. Commit this file as `.scratch/coachwait-closelocal/issues/04-suite-fixes.md`, evidence next to it. Base: integration sha ea196bb (`--base`), no re-merge needed.

Read QA's findings first: `$SCOPE_DIR/evidence/02-qa-w.md` (the SUITE section).

## Business AC
1. `tests/test_utf8_helpers.py::test_spawn_dry_run_and_stubbed_run_for_every_role_with_a_space_and_emoji_path` and `tests/test_squadsettings.py` (`test_local_file_wins_over_an_old_full_file`, `test_old_layout_keeps_the_file_and_warns_once`) pass: pass `--prompt` in the spawn calls they make (preferred; keeps the warning rule intact) or assert the new warning; do not weaken `warning:` counts otherwise.
2. `tests/test_qab_optional.py` goldens (`test_every_role_matches_the_4901cab_golden`, manager and tech-lead, all sizes/qab) refreshed for the ITER-6/ITER-6c text change, by the pattern in `git show 6ebcfbd` (task 03 there). Only manager and tech-lead goldens change; show the golden diff is just the 02 wording.
3. No change to behaviour in bin/ or templates/ beyond what 02 already did. If a fix needs one, `BLOCKED 04`.
4. Three suite failures are NOT yours (fail on main / environment): test_squadinbox `test_no_pyc`, test_process_conversion (`.scratch/composed-process` mapping.md moved to `_done`), test_po_inbox_mod `test_plugin_test_passes` (passes alone). Leave them.

## Technical AC (QA whitebox)
T1. The three test fixes pass `--prompt` (or assert the warning exactly once); no `warning:` count weakened, no test deleted or skipped.
T2. Golden refresh: diff touches only manager and tech-lead goldens and only the ITER-6 / ITER-6c wording; shown in evidence.
T3. `git diff ea196bb` lists only tests, goldens and ticket/evidence; bin/ and templates/ untouched.
T4. Whole test files green: test_utf8_helpers, test_squadsettings, test_qab_optional, test_squad_spawn, test_retro_rules. I rerun the full suite once on the final sha.
