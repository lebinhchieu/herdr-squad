# Test suites

## SUITE-1 Who runs the full suite
roles: tech-lead
when: suite-owner = tech-lead
topic: suites

Only the Tech Lead runs the full suite. The default is targeted tests: touched files plus `grep -rl` hits over `tests/`. For a full run, send the Manager `ASK <task>: full suite? <why>`; it blocks nothing ([ITER-19]); run it when the PO says yes. `project.md` may redefine the default and name the runner.

## SUITE-1b Who runs the full suite, QA whitebox
roles: qa-whitebox
aware: manager
when: suite-owner = qa-white
topic: suites

You own the full suite for the scope; Developers and QA blackbox run only the test files they touch. Your default is targeted tests. A full run, once, needs your `ASK <task>: full suite? <why>` to the Manager; it blocks nothing ([ITER-19]); run it when the PO says yes. `project.md` may redefine the default and name the runner.

## SUITE-2a Suites, Developer
roles: dev
when: suite-owner = tech-lead
topic: suites

Run only the test files you touched; the full suite is the Tech Lead's; two suite runs never overlap.

## SUITE-2c Suites, Developer, QA whitebox
roles: dev
when: suite-owner = qa-white
topic: suites

Run only the test files you touched; the full suite is QA whitebox's; two suite runs never overlap.

## SUITE-2d Suites
roles: dev
when: suite-owner = dev
topic: suites

Run the test files you touched plus `grep -rl` hits. A full suite needs `ASK <task>: full suite? <why>` to the Manager; non-blocking ([ITER-19]); on yes, then once on your final sha, in background (never `pgrep -f`/`pkill -f`); commit fixes first, never restart; receipt in `$SCOPE_DIR/evidence/`: `sha <git rev-parse HEAD> clean=<yes|no>`, OK last.

## SUITE-2b QA suites
roles: qa-whitebox, qa-blackbox
when: suite-owner = tech-lead
topic: suites

Run only the test files the diff touches; the full suite is the Tech Lead's, and two suite runs never overlap.

## SUITE-2e QA blackbox suites, QA whitebox owns it
roles: qa-blackbox
when: suite-owner = qa-white
topic: suites

Run only the test files the diff touches; QA whitebox owns the full suite, and no two suite runs overlap.

## SUITE-2f QA blackbox suites, Developer owns it
roles: qa-blackbox
when: suite-owner = dev
topic: suites

Run only the test files the diff touches; the Developer owns the full suite on the final sha, and no two suite runs overlap.

## SUITE-3 When it runs
roles: tech-lead
when: suite-owner = tech-lead
topic: suites

Once [SUITE-1] allows it, you decide when the full suite runs: once for a batch of tasks, or at the end of the scope or iteration. A scope reaches the PO with a passing run (`--tz` where `project.md` names it) on its integration sha, or with the ask named as unanswered ([ITER-19]).

## SUITE-4 Running and receipt
roles: tech-lead
when: suite-owner = tech-lead
topic: suites

When [SUITE-1] allows a full run, run it in the background and wait for its completion notice (never `pgrep -f` or `pkill -f`). Commit every fix first; never restart a run. Save a receipt in `$SCOPE_DIR/evidence/`: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the OK line.

## SUITE-4b Running and receipt, QA whitebox
roles: qa-whitebox
when: suite-owner = qa-white
topic: suites

When [SUITE-1b] allows a full run, start it in the background and wait for its completion notice (never `pgrep -f` or `pkill -f`); commit each fix before a run and never restart one. Save the receipt in `$SCOPE_DIR/evidence/`: first line `sha <git rev-parse HEAD> clean=<yes|no>`, ending in the OK line.

## SUITE-5 A failing run
roles: tech-lead
when: suite-owner = tech-lead
topic: suites

On a failing run, name the task whose files fail; it returns to its Developer and counts as a return.

## SUITE-5b A failing run, QA whitebox
roles: qa-whitebox
aware: manager
when: suite-owner = qa-white
topic: suites

When the run fails, `FAIL` the task whose files fail; it counts as a return of that task ([LC-7c]).

## SUITE-3b When it runs, QA whitebox
roles: qa-whitebox
when: suite-owner = qa-white
topic: suites

Once every task of the scope has passed and [SUITE-1b] allows a full run, run it on the scope's final sha (`--tz` where `project.md` names it): a scope reaches the PO with a passing run, or with the ask named as unanswered ([ITER-19]).

## SUITE-6 Reading the receipt
roles: qa-whitebox, qa-blackbox
when: suite-owner = tech-lead
topic: suites

QA reads the receipt when it covers the sha (same sha, clean, OK). With none, it checks the targeted tests and the diff, and never runs the suite.

## SUITE-6b Reading the receipt, QA blackbox
roles: qa-blackbox
when: suite-owner = qa-white
topic: suites

Read the receipt QA whitebox saved when it covers the sha (same sha, clean, OK). With none, check the targeted tests and the diff; you never run the suite.

## SUITE-7 Base failures file
roles: tech-lead
when: suite-owner = tech-lead
topic: suites

You keep `$SQUAD_DIR/base-failures.md`, one row per test name, append only. Columns: test name, sha it fails on, one-line cause, first scope that saw it, fix ticket or the PO's keep. Create it on the first row.

## SUITE-7e Base failures file, QA whitebox
roles: qa-whitebox
when: suite-owner = qa-white
topic: suites

You keep `$SQUAD_DIR/base-failures.md`, one row per test name, append only. Each row holds the test name, the sha it fails on, a one-line cause, the first scope that saw it, and the fix ticket or the PO's keep. Create it on the first row.

## SUITE-7f Base failures file, Developer
roles: dev
when: suite-owner = dev
topic: suites

You keep `$SQUAD_DIR/base-failures.md` as [SUITE-7] says; read it with `squad-process rule SUITE-7`.

## SUITE-7b Base check before the first spawn
roles: tech-lead, qa-whitebox
aware: team-lead
topic: suites

If you keep the base-failures file ([SUITE-7]), before a task's first spawn, run its grep and test AC on the base sha. An AC that cannot pass there is fixed in the ticket first. A test that fails on base becomes a row of [SUITE-7].

## SUITE-7c Failing test, look it up
roles: dev, qa-whitebox, qa-blackbox
topic: suites

Look a failing test name up in `$SQUAD_DIR/base-failures.md` first. A listed name is not run on base again and is no `FAIL`. Run an unlisted name on base once and send it to the suite owner to add; never edit the file yourself ([SAFE-4]).

## SUITE-7d Old base failures at check-in
roles: manager
topic: suites

At a check-in, tell the PO of each row of `$SQUAD_DIR/base-failures.md` from an earlier scope with no fix ticket and no keep. The Manager runs no test and reads no other scope's folder ([SAFE-6], [SAFE-7]).
