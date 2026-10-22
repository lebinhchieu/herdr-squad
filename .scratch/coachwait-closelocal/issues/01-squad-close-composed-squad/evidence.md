# 01 Evidence

## Behaviour
- Composed squad (only `process.local.md`): `squad-close` exits 0, archives to `_done/` (`test_composed_squad_without_process_md_closes`; failed with `no squad folder` before the fix).
- Legacy (only `process.md`): exits 0 (`test_legacy_squad_with_only_process_md_closes`).
- Neither: exits 1, `no squad folder at <dir> (neither ...)`, folder untouched (`test_folder_with_neither_process_file_is_refused`).
- `python3 -B -m unittest tests.test_squad_close`: 73 tests OK.
- Scope close and goal close in a composed squad: archived to `scopes/_done`/`goals/_done`, Manager kept, merged worktree removed. Neither file (flat, scope, goal, whole squad): exit 1, nothing moved.

## Red run (old script from main, same tests)
`FAILED (failures=5)`: `test_composed_squad_without_process_md_closes`, and `test_composed_squad_scope_close_archives_scope_and_retires_agents` + `test_composed_squad_goal_close_archives_goal` (each also inherited by RetroCloseTest). Legacy and neither tests pass on old and new.
Green on the fix: 79 tests OK, `bash -n bin/squad-close` clean.
