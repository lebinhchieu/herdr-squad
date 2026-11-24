# Evidence 24 version 0.7.0

## Behaviour
- Changed `.claude-plugin/plugin.json` line 4: `"version"` 0.6.7 -> 0.7.0. Nothing else changed.
- `git grep -n 0.6.7` (before): only `plugin.json:4`. No test or doc pins 0.6.7, so no other edit.
- `grep -rl plugin.json tests/` hits 7 files; ran each (from `tests/`, `python3 -m unittest <name>`) with 0.7.0:

| file | tests | result |
|---|---|---|
| test_squad_start | 43 | OK |
| test_squadupgrade | 29 | OK |
| test_promotion_0_6_0 | 3 | OK (accepts version >= 0.6.0) |
| test_squad_respawn | 21 | OK |
| test_squadruntime | 68 | OK |
| test_squad_spawn | 81 | 1 failure |
| squadtest.py | helper, no tests | n/a |

- The one failure, `SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` (`returncode 0 == 0`), is not from the version: it fails the same way with plugin.json at 0.6.7 (re-run on the unchanged file).
