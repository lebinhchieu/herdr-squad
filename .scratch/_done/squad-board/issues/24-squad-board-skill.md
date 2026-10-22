Status: resolved
State: done (PASS qaw-board; in squad/dev-board-19 at 927c5a7, PO-merge candidate)
Task ID: BRD-24
Blocked by: 22
Files touched: `skills/squad-board/SKILL.md` (new), `tests/test_instructions.py` (only if it needs the new skill listed)

# BRD-24: the `/squad:squad-board` skill

**Done when `/squad:squad-board` prints the board's URL, and `/squad:squad-board restart` starts it afresh, using `squad-board-start`.** Spec story 58.

## Build
- Frontmatter like `skills/squad-start/SKILL.md`: `name: squad-board`, a description saying when to use it (open, recover, restart the board; the URL was lost), `disable-model-invocation: true`.
- Body, short: 1) check `HERDR_ENV` is `1`; 2) pick the squad as `squad-start` does (name given, else the only one); 3) run `squad-board-start --squad <squad>` (`--restart` when the user says restart or the board looks dead, i.e. the page does not load); 4) show the URL line as printed and say it ends in the token and that Jump needs it; 5) if the command fails show its output as is.
- Nothing else: no extra flags, no board docs copied (README holds them).

## Technical AC
1. File exists with valid frontmatter; `test_instructions.py` (stale-name scan over every `skills/*/SKILL.md`) green.
2. The skill names no path that does not exist in the plugin; `bin/squad-board-start` is the only command it runs.
3. Dev checks once in a real herdr session that `/squad:squad-board` shows a working URL (evidence: the line and the HTTP status from `curl`).
4. **Suite receipt (process.md Safety):** `python3 tests/run_suite.py --receipt evidence/BRD-24 --tz` (the parallel runner from BRD-30, passed at 59f1081: merge `squad/dev-board-30` into your branch first, as its own merge commit; it touches only `tests/`). It writes `suite-default.txt` and `suite-tz.txt` with the first line `sha <rev> clean=yes|no` and the tail `Ran N tests ... OK`; a browser file that passed on retry is named in the body, say so in `dev-evidence.md`. QA whitebox checks the receipt and runs only targeted tests. Python 3.9-safe, no `.pyc` committed.
