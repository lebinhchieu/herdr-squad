## Behaviour
`squad-start` no longer has `--touches`, `--yes` or the overlap stop (exit 3). New scope.md and goal.md have no `touches:` line. Old files that carry the line still load: lone start, `--in-goal`, `--resume` of a scope and of a goal all exit 0, files unchanged.

Tests run from `tests/` (targeted, no full suite):
`python3 -m unittest test_squad_start test_templates test_squadruntime test_team_models test_squad_team test_squad_spawn test_old_language_inventory test_windows_safe test_utf8_helpers test_instructions`
Result: 321 tests, 1 failure: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file`. It fails the same on a clean `git archive` of main 7d4b71d, so it is not from this change. SQ-10 files (test_windows_safe, test_utf8_helpers, test_instructions): all pass.
