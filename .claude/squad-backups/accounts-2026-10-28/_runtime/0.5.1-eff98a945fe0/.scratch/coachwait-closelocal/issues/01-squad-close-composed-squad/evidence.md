# 01 Evidence
sha: 31678a7
## Behaviour
- Composed squad (only `process.local.md`): `squad-close` exits 0, archives to `_done/` (`test_composed_squad_without_process_md_closes`; failed with `no squad folder` before the fix).
- Legacy (only `process.md`): exits 0 (`test_legacy_squad_with_only_process_md_closes`).
- Neither: exits 1, `no squad folder at <dir> (neither ...)`, folder untouched (`test_folder_with_neither_process_file_is_refused`).
- `python3 -B -m unittest tests.test_squad_close`: 79 tests OK.
- Scope close and goal close in a composed squad: archived to `scopes/_done`/`goals/_done`, Manager kept, merged worktree removed. Neither file (flat, scope, goal, whole squad): exit 1, nothing moved.

## Red run (old script from main, same tests)
`FAILED (failures=5)`: `test_composed_squad_without_process_md_closes`, and `test_composed_squad_scope_close_archives_scope_and_retires_agents` + `test_composed_squad_goal_close_archives_goal` (each also inherited by RetroCloseTest). Legacy and neither tests pass on old and new.
Green on the fix: 79 tests OK, `bash -n bin/squad-close` clean.

## QA whitebox review

### 01 QA whitebox, sha 31678a7 — PASS
- T1 bin/squad-close:48-50 same rule as squad-respawn:20-22; no parser; squadruntime.py untouched.
- T2/T3 tests/test_squad_close.py: composed (flat, scope, goal), legacy, neither (flat/scope/goal) assert archive + retire effects. I ran old script + new tests: 5 fails (composed only); new script: 79 OK.
- T4 `bash -n` clean; diff = squad-close, its test, ticket, evidence only. T5 only the guard + message changed.
- Non-blocking: evidence.md Behaviour says "73 tests OK", later "79" (stale number). Fix in a doc-only commit.

## QA blackbox review

### QA blackbox 01 — sha 31678a7 (exact sha via git archive into a scratch dir; scratch git repo with squads comp=process.local.md only, leg=process.md only, none=empty)

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 composed | `squad-close comp --scope s1`, `--goal g9`, `--force`, no flag; dry-run and real | exit 0; `== agents/branches/folder/manager`; scope/goal archived under `_done/`; whole squad `would move ... _done/comp` on dry-run | PASS |
| 1 legacy | same on `leg` (process.md only), scope/goal/whole, dry-run + real | exit 0, archived | PASS |
| 2 neither | `squad-close none --scope s1` (real and dry-run), `nosuch` | exit 1, `no squad folder at <dir> (neither process.md nor process.local.md)` — starts with the required text | PASS |
| 3 nothing else changes | main's `bin/squad-close` vs 31678a7, same 9 dry-run invocations on legacy squad | legacy output + exit codes byte-identical (scope/goal/whole); `comp --scope nosuch` -> `no scope folder at ...` exit 1 | PASS |
| 4 same detection | not observable blind (code); behaviour equals the composed/legacy/none split of spawn/respawn | n/a | left to QA whitebox |

Note: main's script on `comp` exits 1 `no squad folder at .../comp` for every call (bug reproduced), new sha fixes it.
Observation, not reproduced: two real runs `comp --scope s1` against the dev worktree (then at 31678a7) printed the OLD message without the suffix, exit 1. 8 later real runs (worktree after HEAD moved to fc29faa, and a clean archive of 31678a7) all passed. Likely the dev's red-run was using the worktree at that moment. Not a sha defect.
