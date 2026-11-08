## Behaviour

AC1: `.claude-plugin/plugin.json` line 4 changed `"version": "0.7.6"` to `"version": "0.7.7"`. Run: `git diff --stat` -> `.claude-plugin/plugin.json | 2 +-`. JSON loads, `version` = `0.7.7`.

AC2: `grep -rn "0\.7\.6" tests bin hooks skills agents docs templates README.md CLAUDE.md .claude-plugin`
- Before the change:
```
.claude-plugin/plugin.json:4:  "version": "0.7.6",
```
- After the change: no output (grep exit 1).

AC3: ran the test files that reference `plugin.json` or `0.7.`: `cd tests && python3 -m unittest test_squad_start test_squadupgrade test_promotion_0_6_0 test_squadruntime test_squadscaffold test_squad_spawn test_squad_respawn test_team_cli`
```
Ran 278 tests in 74.462s
FAILED (failures=1)
FAIL: test_a_failed_agent_start_leaves_the_old_overrides_file (test_squad_spawn.SpawnDryRunTest)
```
That one failure is not from the bump: with plugin.json set back to `0.7.6` it fails the same way
(`python3 -m unittest test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` -> `FAILED (failures=1)`, `0 == 0` on the exit code of a fake `herdr` that should exit 1). The other 277 tests pass.

## Review

AC trace:
- AC1 | `git diff --stat` and the json load above | `git diff`; `python3 -c "import json;..."`
- AC2 | grep outputs above | the grep in AC2, before and after
- AC3 | unittest output above | the unittest command in AC3

Findings (fresh-context sonnet review): none. One-line diff, JSON valid, no other 0.7.6 pin, marketplace.json has no version field. The `0.7.0` strings in test_team_cli.py and test_squadscaffold.py are fixtures, not the plugin version.
