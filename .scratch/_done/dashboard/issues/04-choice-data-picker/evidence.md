# Evidence 04 choice data picker

## Behaviour
`bin/squadboard_list.py` adds two routes: `/api/squads` (picker) and `/api/scopes` (`goal=` or `scope=`; 400 `selection required` without).
Run on the board fixture (clock 2026-11-04T10:00Z, recorded herdr file):

| name | kind | needs you | stuck | tasks | agents | last active |
|---|---|---|---|---|---|---|
| questions | scope | 1 | 0 | 0 of 0 | 0 | 2026-11-03T18:33:14Z |
| checkout | scope | 0 | 2 | 2 of 9 | 2 | 2026-11-04T09:30:00Z |
| alpha | goal | None | 0 | 0 of 0 | 0 | 2026-11-03T18:30:35Z |
| beta | goal | None | 0 | 0 of 0 | 0 | 2026-11-03T18:30:35Z |
| gamma | goal | None | 0 | 0 of 0 | 0 | 2026-11-03T18:30:35Z |
| a-very-long-scope-name-t | scope | None | 0 | 0 of 0 | 0 | 2026-11-03T18:30:35Z |
| broken-parked | scope | None | 0 | 0 of 0 | 0 | 2026-11-03T18:30:35Z |
| parked | scope | None | 0 | 0 of 0 | 0 | 2026-11-03T18:30:35Z |
| search | scope | None | 0 | 0 of 2 | 0 | 2026-11-03T18:30:35Z |

- Done list: 20 rows, newest close first; first is `closed-release`, closed_at `2026-11-03T10:00:00Z` (folder mtime, `closed_approx: true`).
- Saved choice check: `?check=gone` gives `{"name": "gone", "exists": false, "kind": null, "where": null, "message": "saved choice gone not found"}`.
- Goal `alpha` via `/api/scopes?goal=alpha` lists its 4 scopes and the Scopes table as written.
- Picker time on 29 rows: about 0.01 s (test asserts under 1.5 s). Git: 2 calls per squad; no transcript opened; fixture tree unchanged after a request.
- Tests: `python3 -m unittest discover -s tests -p test_squadboard_list.py` (12 pass); also pass: test_windows_safe, test_no_bare_bash, test_old_language_inventory, test_squadboard_server, test_board_fixtures.
