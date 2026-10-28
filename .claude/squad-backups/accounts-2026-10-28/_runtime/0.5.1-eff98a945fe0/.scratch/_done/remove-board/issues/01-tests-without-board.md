Status: done
Blocked by: none
Task ID: RB-01
Files touched: `tests/test_squadinbox.py`, `tests/test_squadinbox_answer.py`, `tests/fixtures/inbox/` (new golden file), `bin/squadinbox.py` (comments only), `tests/run_suite.py`, `tests/test_run_suite.py`

# RB-01: Make the tests and the runner independent of the board

**Done when nothing outside the board's own files loads `bin/squad-board`, names a `test_board_*` file or watches a board path, and the full suite is still green with the board still present.** This must land before RB-03 deletes the board. Requirement: `.scratch/remove-board/spec.md` (R-16), `iterations/1.md` default 1.

## Why this exists (not in the first plan)
- `tests/test_squadinbox.py` and `tests/test_squadinbox_answer.py` load `bin/squad-board` (`load_board()`) as an independent oracle for the `escalations.md` reader (`BoardParityTest`, `RowWriterTest`, `AnswerTest` helpers). Deleting the board breaks about 25 call sites.
- `tests/run_suite.py` builds `TZ_FILES`, `BOARD_SOURCES`, `TZ_WATCH`, `BROWSER_WATCH` from `test_board_*` and `bin/squad-board*`; `tests/test_run_suite.py` pins them.

## Part A: inbox tests
1. **Golden first, on a tree that still has the board.** Run the board's `read_first_table` and `clean_cell` on the inputs `BoardParityTest` uses (`fixtures/inbox/home/escalations.md`, `no-table/escalations.md`, `""`, `"| a |\n|---|\n"`, the three `clean_cell` cells) **plus** a short row, a CRLF file and a file with no final newline. Save the results as `tests/fixtures/inbox/board-reader-golden.json`; its docstring/README line says "captured from the board's reader at 39ab34a, the oracle the board's removal deletes" (do not write the literal `squad-board` anywhere in the golden file or its README line). Do not commit the capture script (it needs the board).
2. `BoardParityTest` becomes `ReaderGoldenTest`: `squadinbox.first_table`/`clean_cell` must equal the golden. Same inputs, same assertions.
3. `load_board()` is deleted. One helper `rows_of(path)` in `test_squadinbox.py` (imported by the answer tests) returns `[dict(zip(header, cells))]` from `squadinbox.first_table(read_text(path))`, `[]` without a header. Replace every `load_board().read_first_table(...)`.
4. **Prove the helper equals the old oracle before dropping it:** while the board is still there, make `rows_of` also call the board's reader and assert equal on every call; run both test files green; note the result in `dev-evidence.md`; then remove the wrapper. (This is the only time the board is loaded.)
5. Docstrings/comments in both test files and `bin/squadinbox.py` lines 46, 74, 84, 142 stop pointing at the board; reword to say what the code does ("the escalations.md table reader"). No behaviour change in `bin/squadinbox.py` (comments only; `git diff` shows no code line).

## Part B: runner
6. `TZ_FILES = ()`, `TZ_WATCH = ()`, `BOARD_SOURCES` deleted, `BROWSER_WATCH = ("tests/run_suite.py",)`. Flags, receipt file names and receipt format unchanged (`CLAUDE.md` → Running tests and `agents/dev.md` keep working untouched).
7. **`--tz` with no time files** (`TZ_FILES` empty and no `--also`): the time pass is not run (no `Ran 0 tests ... OK`); `suite-tz.txt` is `<head line>\nskipped: no time files (TZ_FILES is empty and no --also given)\n` and the same line is printed. With `--also test_x` it runs as before. Default run still sets `SQUAD_REQUIRE_CLAUDE=1` under `--tz`.
8. `tests/test_run_suite.py`: every behaviour test still passes without a real board file: the time-file stubs are named `test_time_probe.py` and passed with `--also`; `IfChangedTest.setUp` drops `test_board_state.py`/`bin/squad-board` and its checks use the `--also` stub as the time file. Delete `reach`, `assert_watched`, `test_watch_lists_hold_everything_...` and `test_the_pin_fails_when_one_entry_is_dropped`: with no real time or browser sources there is nothing to pin (say so in the commit message). Add one test for AC7.
9. Do not remove the browser phase, `--browser-streams`, `--retries` or the lock: role instructions and process.md describe them (a later, PO-approved cleanup; see `promote.md` follow-ups).

## Technical AC
1. `git grep -nE 'squad-board|test_board_|load_board|BOARD_SOURCES|board_fixture'` in the six files of this ticket is empty.
2. Standing: receipt on the HANDIN sha (`python3 tests/run_suite.py --receipt <dir> --if-changed <base>`; this ticket edits `tests/run_suite.py`, so the runner will not skip the browser phase), `test_squadinbox`, `test_squadinbox_answer`, `test_run_suite` green on their own.
3. Test count: no inbox test is deleted except `BoardParityTest` (renamed); the diff of the two inbox test files shows only the oracle swap, docstrings and the helper.
4. Weakening is stated: `dev-evidence.md` lists which assertions are now "writer against squadinbox's own reader" instead of "against an independent reader", and the golden file is what keeps them honest.
- Receipt hygiene: run targeted tests with `PYTHONDONTWRITEBYTECODE=1`; `rm -rf bin/__pycache__` (gitignored, so `clean=yes` misses it; `test_no_pyc` fails on it) before the receipt run; `dev-evidence.md` quotes the receipt's real tail.

## Comments
