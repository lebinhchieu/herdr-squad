Status: resolved
State: done (PASS qaw-board; in squad/dev-board-19 at 927c5a7, PO-merge candidate)
Task ID: BRD-23
Blocked by: 22
Files touched: `bin/squad-start`, `skills/squad-start/SKILL.md`, `tests/test_squad_start.py`

# BRD-23: `squad-start` opens the board next to the Manager

**Done when a real `squad-start` also runs `squad-board-start`, puts the URL in its JSON output, and a board that cannot start never stops the Manager from starting.** Spec story 55, 57.

## Build
1. After the Manager is up (both the normal path and `--resume`), run `squad-board-start` with the same `SQUAD_DIR`. Not in `--dry-run`. A scope inside a goal has no Manager of its own and the goal's start already opened the board: the call is idempotent, so make it anyway.
2. Add `"board": "<url>"` to the printed JSON (`null` when it did not start). On failure print one line on stderr (`board not started: <reason>; run /squad:squad-board`) and still exit 0. The Manager and its folder stay.
3. `SKILL.md` step 7 tells the user the board URL (open it in the browser) beside the tab of the Manager; if `board` is null, say so and point at `/squad:squad-board`. Keep it two lines; do not copy the board's docs in.

## Technical AC
1. Tests in `test_squad_start.py` with the fake `herdr`: board started (URL in JSON), board failing (exit 0, `board` null, stderr line, Manager still created), `--dry-run` starts nothing, `--resume` also opens it.
2. Existing `squad-start` tests unchanged and green; `test_instructions.py` green (the skill must not name a removed file).
3. `squad-board-start` is found next to `squad-start` (`PLUGIN/bin`), not through `PATH`.
4. **Suite receipt (process.md Safety):** `python3 tests/run_suite.py --receipt evidence/BRD-23 --tz` (the parallel runner from BRD-30, passed at 59f1081: merge `squad/dev-board-30` into your branch first, as its own merge commit; it touches only `tests/`). It writes `suite-default.txt` and `suite-tz.txt` with the first line `sha <rev> clean=yes|no` and the tail `Ran N tests ... OK`; a browser file that passed on retry is named in the body, say so in `dev-evidence.md`. QA whitebox checks the receipt and runs only targeted tests. Python 3.9-safe, no `.pyc` committed.
