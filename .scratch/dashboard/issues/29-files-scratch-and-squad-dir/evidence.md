# Evidence 29: Files folder rows and ticket rows

## Behaviour
`bin/squadboard_files.py` only (plus `tests/test_squadboard_files.py`). Ticket rows come from `squadtickets.scope_tasks` (ticket 28, merged at a3889c2); What = ticket title. Folder rows are a separate `folders` list (`.scratch`, squad folder), not in `rows`. PO confirmed O2 (E11): folder rows kept.
Tests run: `test_squadboard_files.py` (12 OK), `test_squadboard_panels.py` (48 OK) = the two hits of `grep -rl "squadboard_files\|api/files" tests/`.
Old tests changed: `test_T14_AC1_TA1_TA2...` (also asserts `folders`). None skipped.

## AC table
| AC | Where shown |
|---|---|
| T29.AC1, AC2 | `squadboard_files.py` `_folder_row`, `list_files` (folders for scope and goal); test `test_T14_AC1_TA1_TA2` (names, What, abs, no folder in rows) |
| T29.AC3 | folders built before the file walk, always; panel empty-note text is ticket 30 (open gap for 29: data only) |
| T29.AC4 | `test_T29_AC4_flat_scope_tasks...` (flat `tasks/NN.md`), `test_T29_AC4_AC5_AC9...` (`.scratch/<slug>/issues`) |
| T29.AC5 | `test_T29_AC4_AC5_AC9...` (`.scratch/other` not listed) |
| T29.AC6 | `_folder_row` resolve + `_under`; missing `.scratch` gives no row. test `test_T29_AC6_AC3_TA3` (no `.scratch`, symlinked `.scratch`: no row) |
| T29.AC7, AC10 | panel side (ticket 30); data: folders are not in `rows`/`files_seen` |
| T29.AC9 | `_Walk.listed` set; same test asserts unique paths |
| T29.AC11 | `w.add(..., t["title"])`; same test asserts What = title |
| T29.AC8 | existing T14 tests green |
| T29.TA3 (600 files) | `test_T29_AC6_AC3_TA3` (folders not counted in the cap); existing cap test covers 500 rows |
| T29.TA6 | `/api/file` test over every row in `rows` still 200 |
