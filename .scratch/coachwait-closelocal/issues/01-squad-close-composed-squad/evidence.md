# 01 Evidence

## Behaviour
- Composed squad (only `process.local.md`): `squad-close` exits 0, archives to `_done/` (`test_composed_squad_without_process_md_closes`; failed with `no squad folder` before the fix).
- Legacy (only `process.md`): exits 0 (`test_legacy_squad_with_only_process_md_closes`).
- Neither: exits 1, `no squad folder at <dir> (neither ...)`, folder untouched (`test_folder_with_neither_process_file_is_refused`).
- `python3 -B -m unittest tests.test_squad_close`: 73 tests OK.
