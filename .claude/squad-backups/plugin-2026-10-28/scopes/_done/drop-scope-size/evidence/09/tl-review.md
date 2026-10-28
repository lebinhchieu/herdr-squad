# TL review 09 (final code sha 95bfcf2, branch squad/plugin/drop-scope-size/plugin-dev-dsz-9, base 6ec3a75)
- Bin/template diff read vs design 07 (AC 23, C8 payload shape): both `team` and `size` on every row; error rows None on both (test asserts one rule); chips use textContent (no XSS).
- Run: lint exit 0; test_squadreport_{collect,rollup,tasks,ui,html,digest,embed}, test_instructions all OK.
- Expected red until 03 merges: test_squad_migrate ToPerScopeTest (2 tests). Integration task runs it against merged template.
- Open: evidence.md is in the code commit; Dev adds evidence-only commit, then `squad-evidence check --base 95bfcf2`.

## Evidence check
- Evidence sha 472d2e9 (evidence-only on 95bfcf2): `squad-evidence check --base 95bfcf2` exit 0 (run by me). Final code sha stays 95bfcf2 unless QAs find something.

## Final (after QAW FAIL, 2 test-only findings)
- Final code sha 0bccec6 (95bfcf2 + test-only: http.server cleanup, unused tempdir; bin/ and templates/ identical). Evidence sha 6a25f51, `squad-evidence check --base 0bccec6` exit 0 (run by me). lint exit 0; test_squadreport_rollup_ui OK.
- Re-check ce6b3a1 (evidence d892341, check --base ce6b3a1 exit 0): template has `team:` + `qa: full` (arch.md:48), chip `team ?`/rollup `–`, test_instructions + UI tests OK. F1 closed. Final sha: ce6b3a1 code / d892341 evidence. Known gap: rollup Size filter cannot select a team scope -> later task.
- DONE: code ce6b3a1, final evidence e7a7910 (evidence-only, check --base ce6b3a1 exit 0). Both QA PASS on ce6b3a1 per Dev.
