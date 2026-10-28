# QA blackbox 01 — sha 31678a7 (exact sha via git archive into a scratch dir; scratch git repo with squads comp=process.local.md only, leg=process.md only, none=empty)

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 composed | `squad-close comp --scope s1`, `--goal g9`, `--force`, no flag; dry-run and real | exit 0; `== agents/branches/folder/manager`; scope/goal archived under `_done/`; whole squad `would move ... _done/comp` on dry-run | PASS |
| 1 legacy | same on `leg` (process.md only), scope/goal/whole, dry-run + real | exit 0, archived | PASS |
| 2 neither | `squad-close none --scope s1` (real and dry-run), `nosuch` | exit 1, `no squad folder at <dir> (neither process.md nor process.local.md)` — starts with the required text | PASS |
| 3 nothing else changes | main's `bin/squad-close` vs 31678a7, same 9 dry-run invocations on legacy squad | legacy output + exit codes byte-identical (scope/goal/whole); `comp --scope nosuch` -> `no scope folder at ...` exit 1 | PASS |
| 4 same detection | not observable blind (code); behaviour equals the composed/legacy/none split of spawn/respawn | n/a | left to QA whitebox |

Note: main's script on `comp` exits 1 `no squad folder at .../comp` for every call (bug reproduced), new sha fixes it.
Observation, not reproduced: two real runs `comp --scope s1` against the dev worktree (then at 31678a7) printed the OLD message without the suffix, exit 1. 8 later real runs (worktree after HEAD moved to fc29faa, and a clean archive of 31678a7) all passed. Likely the dev's red-run was using the worktree at that moment. Not a sha defect.
