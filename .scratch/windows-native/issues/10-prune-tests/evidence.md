# Evidence: 10 Prune tests (phase 1 and 2)

## Behaviour

Tests only. No product code changed by this ticket's prune commits. Code sha: `9e814b1`.

Phase 1 cut 100 tests from 22 files. Phase 2 cut 58 more: 53 from 18 files, then 5 after "06 final" (`test_squad_log_message` -4, `test_squad_usage_hook` -1). `test_log_append_stress` has `RECORDS` 200 to 50 (8 writers and the 9000-byte record kept, no test removed). Every cut has a row in `removed.tsv`: rule, reason, and the test that still covers it. Full list and the kept and held files: `prune-report.md` (copy in `$SCOPE_DIR/evidence/10/`).

| AC | Result |
|---|---|
| 1 Counts | 158 `def test_` lines removed in `tests/`; `removed.tsv` has 158 rows. After QA FAIL: the PI-08 test in `test_instructions` was restored (it pins M2, M3). |
| 2 No new skips | `git log --grep='^10: prune' --no-merges -p -- tests`: 0 added skip lines (40 prune commits, one per file). |
| 3 Section (c) files | Not edited; listed under "Kept on purpose" in the report. |
| 4 Sample rows | Each row names a surviving test; see `removed.tsv`. |
| 5 No product edits | The prune commits touch `tests/` and `.scratch/` only. `bin/` differences against main come from merged tickets (06 `squad-log-message`, `squad-usage-hook`, `squadio.py`; `squad-start`), not from this ticket. |
| 6 Evidence check | `squad-evidence check ... --base 5ad5cb5`, see the HANDIN. |
| 7 Full suite | Not run by the Dev (suite owner runs it). |

Linux (WSL Debian, per file, `tools/lx.py`): every touched file passes except failures that were there before and are not caused by the prune (`after-phase2-linux.txt`): `test_run_suite` 3 failures, `test_ca_install::test_gitignore_names_the_state_files` 1,  `test_squadreport_ui` had one error in the batch run (`test_banner_bold_wraps`, not in baseline) and passed 27/27 on re-run, so it is a timing flake. Last run of `test_squad_log_message` (19 tests), `test_squad_usage_hook` (9) and `test_log_append_stress` (4): OK.

Held (R1), untouched: `test_squadrules`, `test_squadcompose`, `test_sizes`, `test_team_duties`, `test_small_files_equivalence`.
