Status: resolved
State: done (PASS qaw-board; in squad/dev-board-19 at 927c5a7, PO-merge candidate)
Task ID: BRD-25
Blocked by: 17, 19 (so the README can drop the "reads the flat layout only" limit)
Files touched: `skills/squad-init/SKILL.md`, `README.md`, `tests/test_instructions.py` (a check that the init skill ignores the logs in every option)

# BRD-25: `squad-init` ignores the board logs; README documents the board

**Done when `squad-init` leaves `messages.jsonl` and `activity.jsonl` git-ignored whichever way the user keeps the squad folder, and the README says what the board is and how to open it.** Spec story 63; Squad wiring.

## Build
1. **squad-init, step 6:** the "commit durable files only" option already writes `*.jsonl`. The "commit everything" option ignores nothing, so the logs (which hold message text) would be committed. Change that option: write `<root>/.claude/squads/.gitignore` with the single line `*.jsonl` and say so. "Ignore everything" needs nothing. Ask no new question. If `git check-ignore` already matches `.../messages.jsonl`, report the rule and write nothing, as the step says for process.md.
2. **README:** one short "Squad board" section: what it shows (one line), that `/squad:squad-start` opens it in a `board` herdr tab and prints the URL, `/squad:squad-board` prints or restarts it, it listens on 127.0.0.1 only, the URL's token is needed for Jump, bars grow from when the recorder first runs, needs Python 3 + herdr + jq + git, logs are git-ignored. Remove the "reads the flat layout only" Known-limits bullet (BRD-19 made it read both). Add the accepted limit from BRD-22 (one board per herdr workspace). Under 25 lines; link the spec for the rest.

## Technical AC
1. A test in `tests/test_instructions.py`: the init skill mentions `*.jsonl` in the commit-everything option (text check; the skill is instructions, not code).
2. README claims match the code: each command and flag it names exists (`grep`); the port number is the one in `bin/squad-board`.
3. No other text in README or the skill changes.
4. **Suite receipt (process.md Safety):** `python3 tests/run_suite.py --receipt evidence/BRD-25 --tz` (the parallel runner from BRD-30, passed at 59f1081: merge `squad/dev-board-30` into your branch first, as its own merge commit; it touches only `tests/`). It writes `suite-default.txt` and `suite-tz.txt` with the first line `sha <rev> clean=yes|no` and the tail `Ran N tests ... OK`; a browser file that passed on retry is named in the body, say so in `dev-evidence.md`. QA whitebox checks the receipt and runs only targeted tests. Python 3.9-safe, no `.pyc` committed.
