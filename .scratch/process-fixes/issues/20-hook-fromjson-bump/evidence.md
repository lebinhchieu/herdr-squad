# Evidence 20 hook fromjson and version 0.8.1

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 dedupe reads the log with `-R` and `fromjson?` (and `objects`, TA1) | `bin/squad-usage-hook` line 24; hand check below | `cd tests && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_usage_hook` |
| AC2 corrupt line + valid event: the hook does not fire again (control: other session fires) | `test_the_dedupe_skips_corrupt_blank_and_non_object_lines` | same |
| AC3 version 0.8.1, no live 0.8.0 | `.claude-plugin/plugin.json`; the greps in Behaviour; v13 changelog entry (TA4) | `grep -rn '0\.8\.0' .claude-plugin bin templates README.md` |

## Behaviour

- Filter now: `jq -R -e --arg s "$session" --arg r "$rule" 'fromjson? | objects | select(.session == $s and .rule == $r)' "$log"`. On a log with a corrupt line, a blank line, a valid event and `5`: the old filter exits 5, the new filter exits 0. The test log has corrupt, blank, valid event, `5`, `[]`, `null`, `"x"`: the hook exits 0 and appends nothing; with the event for another session it exits 2 and appends one line.
- `.claude-plugin/plugin.json` says `0.8.1` (marketplace.json has no version).
- `grep -rn '0\.8\.0' .claude-plugin bin templates README.md`: no hits. The whole-repo grep (excluding .git, .worktrees, .claude, .scratch) leaves two lines: `skills/squad-process-update/changelog.md:23` (v12 history, "Plugin 0.8.0") and `tests/test_squadscaffold.py:78` (the `--new-pin "0.8.0 1111111"` fixture, not a plugin version).
- `skills/squad-process-update/changelog.md` has a v13 entry on top (Plugin 0.8.1): removed COST-1, COST-9; changed COST-3, COST-8b, NOTE-3 and the hook's Developer text, each with `why:`.
- Lint: `bin/squad-process lint --plugin-root . --squad-dir $SQUAD_DIR` exit 0.
- SQ-10 and targeted tests (`test_squad_usage_hook`, `test_squadscaffold`, `test_processlint`, `test_windows_safe`, `test_utf8_helpers`, `test_instructions`, `test_old_language_inventory`, `test_squadruntime`, `test_squadupgrade`, `test_squad_start`, `test_squad_respawn`, `test_squad_spawn`, `test_rules_wording`): 410 tests, 1 failure: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` (`assertNotEqual(returncode, 0)` got 0). The same test fails alone on the line-visible base 172a373 (checked in a `git archive` copy), so it is not caused by this scope.
