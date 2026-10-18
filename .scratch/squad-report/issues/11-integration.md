Status: ready-for-agent
Type: task
Task ID: 11
Touches: none of its own (merge commits and evidence only); a fix found here goes back to the ticket that owns the file
Harness: targeted tests of every merged ticket, then the Tech Lead's `python3 tests/run_suite.py --receipt $SCOPE_DIR/evidence/11 --tz`
Blocked by: 01-09 passed (and 10 if issued)

# 11: Integration branch and full suite

**Done when one branch holds the passed branches of tickets 01-10 and the full suite with `--tz` is green on its final sha.** Process: `process.md` → Inside a goal (integration task) and Safety → Suites. One Developer, fresh name, `--base` main.

## What (Developer)
1. Branch from main; for each passed branch run `git merge-base --is-ancestor main <sha>` and `git log --oneline main..<sha>`, paste both in `dev-evidence.md`, then `git merge` it in order 01, 02, 03, 04, then 05-09 (any order), 10. A conflict means stop and `BLOCKED`; do not resolve a conflict in a file another ticket owns.
2. Run the targeted tests of all merged tickets (the Harness lines of 01-09) together; commit every fix before handing in.
3. Real-data smoke on the merged branch (read-only, temp `--out`): `bin/squad-report` on a copy of `_done/win-compat` (scope), `bin/squad-report rollup` over the two real `data.json`s produced, `bin/squad-report query <scope> digest`, open both `report.html`/`index.html` over `file://` with `playwright-cli` (screenshots in evidence), `squad-close --dry-run` writes nothing. Close every browser session.
4. `git diff --stat main` lists only the files named in tickets 01-10; `git status` clean; `ls bin/__pycache__` cleared before the receipt run.

## What (Tech Lead)
Runs `tests/run_suite.py --receipt <evidence dir> --tz` in the background on the final sha, once, and saves the receipt; a failing test names the ticket whose files fail and it returns to its Developer.

## Technical AC
1. Receipt: first line `sha <final sha> clean=yes`, `OK` tail, no skipped phase (`--tz`).
2. Merge evidence for each branch is in `dev-evidence.md`; the diff stat matches the ticket file lists.
3. Smoke outputs (step 3) are in `dev-evidence.md`; the `squad-usage` hook still runs (a `squad-usage --check` call on a fixture prints as before).
4. Primary behaviour only (qa: light).
