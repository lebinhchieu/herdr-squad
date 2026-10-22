# Test suites

## SUITE-1 Who runs the full suite
roles: tech-lead
when: size = L
topic: suites

Only the Tech Lead runs the full suite. `project.md` may name the runner; it locks only its browser files and skips phases the diff cannot affect.

## SUITE-1b Who runs the full suite, M
roles: qa-whitebox
aware: manager
when: size = M
topic: suites

You run the full suite for the scope, once, on the final sha; Developers and QA blackbox run only the test files they touch. `project.md` may name the runner.

## SUITE-2a Suites, Developer
roles: dev
when: size = L
topic: suites

Run only the test files you touched; the full suite is the Tech Lead's; two suite runs never overlap.

## SUITE-2c Suites, Developer, M
roles: dev
when: size = M
topic: suites

Run only the test files you touched; the full suite is QA whitebox's; two suite runs never overlap.

## SUITE-2d Suites, S
roles: dev
when: size = S
topic: suites

Run the test files you touched, then the full suite once on your final sha ([SUITE-4]).

## SUITE-2b QA suites
roles: qa-whitebox, qa-blackbox
when: size = L
topic: suites

Run only the test files the diff touches; the full suite is the Tech Lead's, and two suite runs never overlap.

## SUITE-2e QA blackbox suites, M
roles: qa-blackbox
when: size = M
topic: suites

Run only the test files the diff touches; QA whitebox owns the full suite, and no two suite runs overlap.

## SUITE-3 When it runs
roles: tech-lead
when: size = L
topic: suites

You decide when the full suite runs: once for a batch of tasks, or at the end of the scope or iteration. A scope reaches the PO only with a passing run (`--tz` where `project.md` names it) on its integration sha.

## SUITE-4 Running and receipt
roles: tech-lead
when: size = L
topic: suites

Run it in the background and wait for its completion notice (never `pgrep -f` or `pkill -f`). Commit every fix first; never restart a run. Save a receipt in `$SCOPE_DIR/evidence/`: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the OK line.

## SUITE-4b Running and receipt, M
roles: qa-whitebox
when: size = M
topic: suites

Start the run in the background and wait for its completion notice (never `pgrep -f` or `pkill -f`); commit each fix before a run and never restart one. Save the receipt in `$SCOPE_DIR/evidence/`: first line `sha <git rev-parse HEAD> clean=<yes|no>`, ending in the OK line.

## SUITE-5 A failing run
roles: tech-lead
when: size = L
topic: suites

On a failing run, name the task whose files fail; it returns to its Developer and counts as a return.

## SUITE-5b A failing run, M
roles: qa-whitebox
aware: manager
when: size = M
topic: suites

When the run fails, `FAIL` the task whose files fail; it counts as a return of that task ([LC-7c]).

## SUITE-3b When it runs, M
roles: qa-whitebox
when: size = M
topic: suites

Run it once every task of the scope has passed, on the scope's final sha (`--tz` where `project.md` names it): a scope reaches the PO only with a passing run.

## SUITE-6 Reading the receipt
roles: qa-whitebox, qa-blackbox
when: size = L
topic: suites

QA reads the receipt when it covers the sha (same sha, clean, OK). With none, it checks the targeted tests and the diff, and never runs the suite.

## SUITE-6b Reading the receipt, M
roles: qa-blackbox
when: size = M
topic: suites

Read the receipt QA whitebox saved when it covers the sha (same sha, clean, OK). With none, check the targeted tests and the diff; you never run the suite.
