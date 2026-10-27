# Evidence: 04 Plugin version patch bump
sha: 29edfe9
## Behaviour
- `.claude-plugin/plugin.json` version 0.6.0 -> 0.5.2 (one line). Diff: plugin.json plus ticket/evidence only.
- `git grep -n "0\.6\.0"` outside historic 03 ticket/evidence: only `tests/test_squadadopt.py:312` (fixture string, stays). `git grep -n "0\.5\.1"`: only historic ticket/evidence text. Nothing else keys off the version (changelog `## v8` is a process-snapshot number).
- Tests run and passing: test_squadadopt, test_process_history, test_squadruntime, test_squadsettings, test_squad_start (unittest, 137 tests), test_sizes (36, run from tests/).

## QA whitebox

### QA whitebox 04 — sha 29edfe9: PASS
- Diff 8e10686..29edfe9: plugin.json 0.6.0 -> 0.5.2 + ticket/evidence only (T1).
- git grep 0.6.0: only tests/test_squadadopt.py:312 fixture + historic 03 text. 0.5.1: historic text only. marketplace.json has no version. Nothing else keys off it (AC1).
- Full suite --tz on clean clone of 29edfe9, python3 -B: OK; receipt suite-default.txt (sha line clean=yes) (T2).
