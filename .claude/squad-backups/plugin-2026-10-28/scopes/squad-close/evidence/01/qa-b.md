# QA blackbox 01 — commit 3ffabe7 (Dev worktree bin/squad-close)
Setup: scratch repo, squad `s` (copy of plugin squad + process.md; scopes squad-close/other with Managers, goal G with Manager, runtimes 0.4.0/0.5.0/0.6.0 pinned by plugin.pin / scope other / scope squad-close / goal G), stub `herdr` (agent get -> live, logs calls), stub `claude`. Old `bin/squad-close` (main) run alongside for comparison.

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 scope | `squad-close s --scope squad-close` (agents live) | dev/qaw/qab `retired` (3 `herdr pane close`); no pane close for Manager; `kept plugin-mgr-squad-close (Manager stays; squad-retire plugin-mgr-squad-close ends it)`; folder archived | PASS |
| 1 goal | `--goal G` | no Manager close; `kept plugin-mgr-G (Manager stays; squad-retire plugin-mgr-G ends it)` (old: `would retire plugin-mgr-G`) | PASS |
| 2 squad | `squad-close s` | all 6 agents retired, then Managers last (other, squad-close, G): 9 pane closes; all 3 runtimes removed | PASS |
| 3 no flag, dry-run | `--help`; `--scope/--goal --dry-run` | usage has no new flag; dry-run prints the kept line (scope + goal) | PASS |
| 4 folder moves | scope, goal, squad runs | `scopes/_done/squad-close`, `goals/_done/G`, `_done/s` exist, source gone | PASS |
| 5 pin kept | scope close; goal close (real + dry) | scope: `kept 0.5.0-5adfc45151ab (plugin-mgr-squad-close still runs from it; the next scope or squad close prunes it)` (old build had it held by scope only); goal: same for 0.6.0 (old build removed 0.6.0); squad close prunes all | PASS |
| 5 later prune | then `--scope other` in the same squad | `removed 0.5.0-5adfc45151ab (5.2 MB)`; 0.4.0 (plugin.pin) and 0.6.0 (goal G) kept | PASS |
| 6 header/usage | usage line only (header = code, not read) | usage unchanged and has no Manager text; header NOT checked (blind) -> whitebox | n/a here |
| 7 tests | not mine (whitebox) | | n/a |

Non-blocking: in scope and goal close the pin gets a second line `kept <pin> (running)` right after the "still runs from it" line, so the same runtime is listed twice.
Not tested: a goal that holds scopes with live agents (goal fixture layout unknown).
Verdict: PASS on the running behaviour.
