## v2 — 2026-10-15
- snapshot: history/process-v2.md

### Tighten the wording of every section
- sections: all
- change: reword
- why: roles read process.md at every start, so wording is tightened in all sections and no rule changed; the rule for editing the file now lives in the Manager's instructions
- old: snapshot
- new: snapshot

### Long suites: lock for browser files, time pass only when needed
- sections: ## Safety
- change: rule
- why: only the browser files need the lock and the runner skips phases the diff cannot affect, so suite runs no longer queue behind each other; the `flock ... nice -n 10` command text goes because the runner owns the lock, and the Developer now runs the suite in the background and waits for its completion notice (never `pgrep -f` or `pkill -f`)
- old:
```
- **Long suites: run once, read the receipt.** For a suite longer than ~2 minutes, one full run at a time for the whole squad, under a lock: `flock /tmp/<squad>-suite.lock nice -n 10 <suite command>` (a project may ship a runner that takes the lock and writes the receipts; `project.md` names it). The Developer runs the full suite once, on the final sha after every fix is in (while building, only the files it touched), and saves a receipt whose first line is `sha <git rev-parse HEAD> clean=<yes|no>` and whose tail is the suite's OK line. QA checks the receipt (same sha as the `HANDIN`, clean tree, OK), then runs only the targeted tests for the files in the diff and reads the diff; it runs the full suite itself only when the receipt is missing or its sha differs (an integration task is no exception). Targeted runs are free; the full suite is never started in the background while you wait on something else.
```
- new:
```
- **Long suites: run once, read the receipt.** A suite over ~2 minutes runs once per task. `project.md` names the runner; it locks only its browser files and skips phases the diff cannot affect.
  - The Developer runs the full suite once, on the final sha after every fix, in the background, waits for its completion notice (never `pgrep -f` or `pkill -f`) and saves a receipt: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the suite's OK line. While building, only touched files.
  - QA checks the receipt (same sha as the `HANDIN`, clean tree, OK, its skipped-phase lines), then runs only targeted tests for the diff's files and reads the diff. It runs the full suite only when the receipt is missing or its sha differs, integration tasks included. Targeted runs are free.
```
