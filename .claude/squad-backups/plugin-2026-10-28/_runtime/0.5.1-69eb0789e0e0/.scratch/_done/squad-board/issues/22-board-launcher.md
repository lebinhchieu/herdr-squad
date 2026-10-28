Status: resolved
State: done (PASS qaw-board; in squad/dev-board-19 at 927c5a7, PO-merge candidate)
Task ID: BRD-22
Blocked by: 17
Files touched: `bin/squad-board-start` (new, bash like `squad-spawn`), `tests/test_squad_board_start.py` (new)

# BRD-22: `squad-board-start`, the one command that runs the board in its herdr tab

**Done when `squad-board-start` makes sure the board of this squad runs in a herdr tab labelled `board`, prints its URL (with token) as one line, and never starts a second one.** Spec stories 55 to 59; Squad wiring section. The two callers are `squad-start` (BRD-23) and the skill (BRD-24).

Read first: spec.md "Squad wiring", `bin/squad-spawn` (tab create, workspace args, `HERDR_ENV` check), `tests/test_squad_start.py` (the fake `herdr` on `PATH` pattern).

## Build
`squad-board-start [--squad S] [--restart]`; squad folder from `SQUAD_DIR`, else the only squad (copy `squad_dir` of `squad-start`, no new rule).
1. `HERDR_ENV` must be `1`, else exit 1 with the message `squad-spawn` uses. `python3` must exist, else exit 1 with one clear line.
2. **Find the running board:** `herdr tab list` for a tab with `label == "board"` in the caller's workspace (same `workspace_id` as the current pane, as `squad-spawn` does it). If found and not `--restart`: read the URL (step 4) and print it; start nothing.
3. **Start:** (with `--restart` first `herdr tab close` the old one.) `herdr tab create --cwd <git root> --label board --no-focus <workspace args>`, then `herdr pane run <pane> "SQUAD_DIR=<squad> <plugin>/bin/squad-board"` with the plugin path quoted for the shell (paths with spaces; the squad dir comes from the environment, never from agent text).
4. **Read the URL:** `herdr pane wait-output <pane> --regex 'squad-board: http://127\.0\.0\.1:[0-9]+/\?token=[0-9a-f]+'` with a timeout of about 10 s, then take the matching line from `herdr pane read`. On timeout exit 1 and print the last 20 lines of the pane so the PO sees why (port, Python, missing herdr).
5. Print exactly the URL on stdout, one line; everything else on stderr. Exit 0.

## Technical AC
1. Idempotent: two runs in a row leave one `board` tab; the second prints the same URL.
2. `--restart` closes the old tab and prints a new URL (new token).
3. The token only goes to stdout of this command and the tab's own screen: not into a file, a log, the squad folder or the process list (`ps` shows no token; the board prints it itself).
4. Tests with a fake `herdr` on `PATH` (as `test_squad_start.py`): found, not found, restart, board never prints a URL (timeout path), `HERDR_ENV` unset, two workspaces each with a `board` tab (only the caller's is used). Capture one real `herdr tab list`, `pane run`, `wait-output` output in `dev-evidence.md` to prove the fake has the real shape.
5. Real run once by the Developer in a throw-away herdr tab, closed afterwards: URL printed, page loads (`curl` the URL, 200), tab closed with `herdr tab close`.
6. `tests/test_instructions.py` still green.
7. **Suite receipt (process.md Safety):** `python3 tests/run_suite.py --receipt evidence/BRD-22 --tz` (the parallel runner from BRD-30, passed at 59f1081: merge `squad/dev-board-30` into your branch first, as its own merge commit; it touches only `tests/`). It writes `suite-default.txt` and `suite-tz.txt` with the first line `sha <rev> clean=yes|no` and the tail `Ran N tests ... OK`; a browser file that passed on retry is named in the body, say so in `dev-evidence.md`. QA whitebox checks the receipt and runs only targeted tests. Python 3.9-safe, no `.pyc` committed.

## Known limit (accepted)
One board per herdr workspace: two squads in the same workspace share the label `board`, and the second `squad-board-start` would reuse the first's. Say it in the README (BRD-25).
