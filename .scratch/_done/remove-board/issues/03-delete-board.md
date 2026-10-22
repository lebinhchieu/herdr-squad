Status: done
Blocked by: none (RB-01 + RB-02 passed: 57b5e9f, 110e50f)
Task ID: RB-03
Files touched: deletions only, plus one line in `tests/test_squadprocess.py` (CliTest env gets `PYTHONDONTWRITEBYTECODE=1`, TL ruling); `bin/__pycache__` is untracked

# RB-03: Delete the board

**Done when every board file is gone and the suite is green.** Requirement: `spec.md` R-01, R-16. Start your branch by merging the passed RB-01 and RB-02 branches (the Manager gives the shas; `git merge` is allowed inside your own branch) and run `git merge-base --is-ancestor` on both before you start.

## Delete (`git rm`)
- `bin/squad-board`, `bin/squad-board.html`, `bin/squad-board-start`
- `skills/squad-board/` (the `/squad:squad-board` command)
- `tests/test_board_*.py` (20 files), `tests/test_squad_board_start.py`, `tests/board_fixture.py`
- `tests/fake_herdr.py` (only the board tests and `run_suite.py` named it; `test_squad_spawn.py` has its own `_fake_herdr` method)
- `tests/fixtures/board/` (49 files)
- `docs/squad-board-guide.html`, `docs/img/squad-board-*.png` (and `docs/img/` if it is then empty)

## Keep (do not touch)
`tests/fixtures/inbox/`, `tests/fixtures/squad-notify/`, `hooks/po-inbox/fixtures/contract-home.ts` (the word is a scope name or path inside data), `bin/squad-migrate` and its `activity.jsonl` handling, `bin/squad-log-message`, `.scratch/**`, `docs/adr/*` (RB-04), `README.md`/`CONTEXT.md` (RB-02, RB-04).

## Technical AC
1. `git ls-files` shows none of the paths above. `git diff --stat main` for this branch outside the merged RB-01/RB-02 content is deletions only.
2. `git grep -nIiE 'squad-board|squad_board|board_fixture|fake_herdr|test_board_|fixtures/board|squad-board-start|squad-board-guide' -- . ':!.scratch' ':!.claude' ':!skills/squad-process-update/history' ':!docs/adr' ':!CONTEXT.md'` is empty outside the allow-list below. Anything left in the excluded places belongs to RB-04/RB-05 or is history; say which in `dev-evidence.md`.
   **Allow-list (data, kept on purpose):** `tests/fixtures/squad-notify/{notification-permission_prompt,stop,subagent-stop}.json`, `hooks/po-inbox/fixtures/contract-home.ts`, `tests/test_squad_respawn.py` (a name string near line 145 and a comment near line 223), `tests/fixtures/inbox/home/escalations.md` (lines 19-20), and the `FAKE_HERDR` / `_fake_herdr` names inside `tests/test_squad_{close,label,respawn,retire,spawn,start}.py` (the grep is case-insensitive: these are those tests' own herdr stub strings, not `tests/fake_herdr.py`). Any other hit means fix the file; never edit an allow-listed fixture to empty the grep. `dev-evidence.md` names every allow-listed hit.
3. Full suite on the final sha with `--receipt <dir> --if-changed <base>` where `<base>` = main; `test_squadinbox`, `test_squadinbox_answer`, `test_run_suite`, `test_squad_start`, `test_squad_migrate` green on their own. Test count drops by exactly the deleted files' tests; `dev-evidence.md` gives the before/after counts from the two receipts.
4. `bin/squad-migrate` on a fixture with `messages.jsonl` + `activity.jsonl` still carries both (existing test).
- Receipt hygiene: run targeted tests with `PYTHONDONTWRITEBYTECODE=1`; `rm -rf bin/__pycache__` (gitignored, so `clean=yes` misses it; `test_no_pyc` fails on it) before the receipt run; `dev-evidence.md` quotes the receipt's real tail. The suite may recreate `bin/__pycache__` after a run: `ls bin/__pycache__` after it and clear it before any further run; say in `dev-evidence.md` whether it reappeared and which test imports caused it.

## Comments
