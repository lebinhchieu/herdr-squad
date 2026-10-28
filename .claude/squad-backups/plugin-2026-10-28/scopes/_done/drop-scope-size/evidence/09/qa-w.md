# QA whitebox 09 (code sha 95bfcf2, evidence 472d2e9, branch squad/plugin/drop-scope-size/plugin-dev-dsz-9, base 6ec3a75)

## Passed (run by me)
- Diff read vs ticket AC (design 07, AC 23, C8, REV-6): `team` and `size` on every scope object and rollup row; error/no_data rows None on both; chips via textContent.
- Tests OK: test_squadreport_collect 45, _rollup 18, _rollup_ui 11, _ui 41, _tasks 13, test_instructions 29, test_squadruntime 64, test_team_models 20, test_team_duties 39, test_squad_start 48, test_squad_spawn 65. `squad-process lint` empty, exit 0 (= base). No stray http.server left after the run.
- Red, accepted by the TL (tl-review.md) and owned by 03 (03 owns squad-migrate:77-190): test_squad_migrate ToPerScopeTest, 2 tests (`size:\n` assert; migrate's `re.sub(^size:)` finds no line in the `team:` template). I confirmed the 2 failures. I re-run test_squad_migrate at 03; it must be green there.

## Findings (style/robustness, one return, REV-17)
- F1 `tests/test_squadreport_rollup_ui.py:209-218` (RollupTeamChip): the server is started in `setUpClass` (209) but `tearDownClass` (218) does not run when `setUpClass` raises. `_wait_port` (212) raising RuntimeError, or the Chrome `subprocess.run(..., timeout=90)` raising TimeoutExpired, leaves the `http.server` process running and the temp dir behind (SAFE-3 "close what you open"). Pass: register the kill/cleanup right after Popen with `cls.addClassCleanup(...)` (kill by PID, wait, `tmp.cleanup()`), or wrap the rest of setUpClass in try/except that runs the same teardown and re-raises.
- F2 `tests/test_squadreport_rollup.py:198` (`test_null_in_data_json_becomes_empty_string`): `with tempfile.TemporaryDirectory() as t:` creates a directory nothing uses (`t` unused; `row_from` takes a dict). Pass: drop the `with`.

## Forward notes
- 03: migrate must write `team:` (or drop the size sub) so ToPerScopeTest is green; tests assert `team:\n`.
- Size filter in rollup.js:178 only matches old sizes (design). Fine.

## Re-check (LC-3b) on 0bccec6 (evidence-only 6a25f51)
- F1 closed: `addClassCleanup(tmp.cleanup)` right after creation, `addClassCleanup(_stop)` right after Popen; LIFO order stops the server (kill by PID, wait) before the temp dir goes. F2 closed: unused tempdir dropped.
- Diff 95bfcf2..0bccec6 = those two test files only. test_squadreport_rollup 18 OK, rollup_ui 11 OK, no http.server left, lint empty exit 0, evidence check ok.
- Verdict: PASS.

## Re-check on final sha ce6b3a1 (evidence d892341; TL DECISION names ce6b3a1)
- Diff 0bccec6..ce6b3a1 (bin none; templates: scope.md `qa: full` after `team:`, report.js `team ?`, rollup.js `–` for an empty row; tests: test_instructions template-lines test, ui chip, rollup_ui). Read in full, no finding.
- Tests OK: test_instructions 30, test_squadreport_ui 41, _rollup_ui 11, _collect 45, _rollup 18, test_squadruntime 64, test_squad_start 48, test_squad_spawn 65, test_windows_safe 11. Lint empty, exit 0 (= base). Evidence check ok. No http.server left.
- Verdict: PASS (the 2 test_squad_migrate reds stay with 03).
