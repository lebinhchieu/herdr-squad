# Evidence: 04 Plugin version patch bump
sha: pending
## Behaviour
- `.claude-plugin/plugin.json` version 0.6.0 -> 0.5.2 (one line). Diff: plugin.json plus ticket/evidence only.
- `git grep -n "0\.6\.0"` outside historic 03 ticket/evidence: only `tests/test_squadadopt.py:312` (fixture string, stays). `git grep -n "0\.5\.1"`: only historic ticket/evidence text. Nothing else keys off the version (changelog `## v8` is a process-snapshot number).
- Tests run and passing: test_squadadopt, test_process_history, test_squadruntime, test_squadsettings, test_squad_start (unittest, 137 tests), test_sizes (36, run from tests/).
