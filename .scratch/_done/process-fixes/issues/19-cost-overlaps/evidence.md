# Evidence 19 cost overlaps

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 COST-9 deleted, no live pointer | `test_cost_3_carries_the_cost_hook_and_cost_1_and_9_are_gone` (no `## COST-9 ` in a composed role); grep below | `cd tests && python3 -m unittest test_rules_wording` |
| AC2 COST-1 merged into COST-3 (hook trigger, compaction, `squad-respawn`, "never a percent"; `_removed.md` entries) | same test (4 strings in COST-3 of a composed qa-whitebox, `_removed.md` regex for COST-1 and COST-9) | same |
| AC3 COST-8b: "next quiet point", no "at any context length", `CACHE_TTL_S` kept | `test_bundle_long_wait_and_experiment_rules` (old two asserts kept, three added) | same |
| AC4 no bare "new task" in COST-3 | same new test (`assertNotIn("new task")`) | same |
| AC5 lint before and after; wording and upgrade tests pass | `bin/squad-process lint --plugin-root . --squad-dir $SQUAD_DIR`; test_processlint, test_squadupgrade, test_squadrules | see Behaviour |

## Behaviour

- COST-3 now reads: "`squad-usage --check` fires `fresh` at your respawn line: context at first action (first edit, write or message) + 50k, at most 180k; limits are absolute tokens, never a percent. Start fresh then, after a compaction, on a Stop-hook cost message, or when a new ticket or PO wait makes old context useless: write `roles/<you>.notes.md`, then `squad-respawn <you>`." (57 words, `roles:` line unchanged, 8 roles.)
- COST-8b now ends: "...write notes and run `squad-respawn` at the next quiet point (a merge, a close, or no role building)."
- `_removed.md` has `## COST-1 (removed in v13)` and `## COST-9 (removed in v13)`, `replaced_by: COST-3`. `notes.md:21` NOTE-3 points at [COST-3].
- Lint before: `bin/squad-process lint --plugin-root . --squad-dir $SQUAD_DIR` exit 0. Lint after: exit 0 (a first draft of COST-3 had 63 words and failed the 60-word check; shortened to 57).
- `grep -rnE 'COST-9|COST-1\b' templates bin hooks agents skills README.md CONTEXT.md docs` outside `_removed.md` and `changelog.md`: no hits. `.claude/squads/*/process.local.md` hits of the two IDs: none.
- Tests run (PYTHONDONTWRITEBYTECODE=1 for the final run): test_rules_wording, test_processlint, test_instructions, test_old_language_inventory, test_windows_safe, test_utf8_helpers: 107 tests OK. Plus test_squadrules, test_squadupgrade, test_squadruntime, test_squadcompose, test_squadinbox: 240 tests OK (a first run failed `test_no_pyc` only because my earlier runs wrote `bin/__pycache__`; removed, rerun OK). The frozen `tests/fixtures/upgrade/*/cost.md` copies are not edited.
