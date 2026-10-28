# QA whitebox 03: PASS on fb2091c (code af6da79)

Verdict: PASS. Full `--tz` suite green: 1474 tests OK, receipt `evidence/suite/suite-default.txt` + `suite-tz.txt` (line 1 `sha fb2091c… clean=yes`). Before: 55 failures.

## Technical AC
- T1 root causes: golden = 5adfc45 bumped plugin.json 0.4.1→0.5.0, header `plugin: <ver>` is hashed (Dev bisect 60d7f7a/2602f80 OK, 5adfc45 FAIL). Accepted; I re-composed all 54 keys at 2602f80 vs af6da79 (script /tmp/qaw_cmp.py, normalise() incl. mask): exactly 12 differ.
- T2 golden: the 12 keys are manager/{S,M,L}/{no,yes}, team-lead/{S,M,L}/{no,yes}. Diff lines I saw = task 02 only: lifetime row, CLOSE-1 intro line, CLOSE-2 "except the Manager", CLOSE-5 "retires every agent, the Managers last". team-lead = lifetime row only. Nothing else. golden.json diff is 12 lines changed (+12/-12); other 42 keys untouched.
- Mask `^(plugin: )\d+\.\d+\.\d+(?= )` (test_qab_optional.py:50) is line-anchored, rewrites only the version token; Dev's append-`x` (FAIL) and version-bump (OK) checks are consistent with it.
- T3: `test_no_pyc` assertion untouched (test_squadinbox.py not in diff). Only `-B` added to subprocess spawns (rulesview.py:20, test_dev_rules_size.py:30, test_qab_optional.py x3). No weakening. `bin/__pycache__` absent after my run.
- T4: done above.

## Business AC
1. `--tz` 0 failures: seen (receipt). (TZ_FILES empty, "skipped: no time files" is the runner's own output.)
2. 01/02 untouched (diff vs edf5d87: tests/ + ticket + evidence only); no test deleted/weakened; golden change reasoned above.

## Note (non-blocking, not a finding)
Many other test spawns of `bin/*` still lack `-B` (e.g. test_squad_close, test_squadinbox helpers); a hand `python3 -m unittest` of those files can still leave `bin/__pycache__`. `run_suite.py:46` sets PYTHONDONTWRITEBYTECODE so the suite is unaffected; outside the 55 failures and AC.
