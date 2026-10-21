# Test suites

## SUITE-1 Who runs the full suite
roles: tech-lead
topic: suites

Only the Tech Lead runs the full suite. `project.md` may name the runner; it locks only its browser files and skips phases the diff cannot affect.

## SUITE-2a Developer suites
roles: dev
topic: suites

Run only the test files you touched. The full suite is the Tech Lead's, and two suite runs never overlap.

## SUITE-2b QA suites
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: suites

Run only the test files the diff touches; the full suite is the Tech Lead's, and two suite runs never overlap.

## SUITE-3 When it runs
roles: tech-lead
topic: suites

You decide when the full suite runs: once for a batch of tasks, or at the end of the scope or iteration. A scope reaches the PO only with a passing run (`--tz` where `project.md` names it) on its integration sha.

## SUITE-4 Running and receipt
roles: tech-lead
topic: suites

Run it in the background and wait for its completion notice (never `pgrep -f` or `pkill -f`). Commit every fix first; never restart a run. Save a receipt in `$SCOPE_DIR/evidence/`: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the OK line.

## SUITE-5 A failing run
roles: tech-lead
topic: suites

On a failing run, name the task whose files fail; it returns to its Developer and counts as a return.

## SUITE-6 Reading the receipt
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: suites

QA reads the receipt when it covers the sha (same sha, clean, OK). With none, it checks the targeted tests and the diff, and never runs the suite.
