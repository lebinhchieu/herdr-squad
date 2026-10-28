# Notes: accounts-qaw-autoswitch (QA whitebox), scope autoswitch (M, qa full) — RETIRED

## Now
- All whitebox work done. 01 PASS @ dac0c50, 02 PASS @ 3ce1fba, 03 PASS @ bc4e1e7 (round 1 FAIL @ 0a9790a: checklist steps 2/5, fixed).
- Suite on final/merge sha bc4e1e7: default run 1449 OK (receipt evidence/suite-default.txt, sha bc4e1e7 clean=yes); --tz run on plain clone 1523 OK, 0 fail, nothing skipped (evidence/suite-tz.txt, suite-tz-default.txt). 899 s cache test: no flake in 3 runs.
- Sent STATUS to Manager with results. Waiting only on QA-b's 03 verdict / Manager merge. A changed sha after that needs a suite re-run (REV-3b).

## Open threads
- None with Dev. Verdict files: evidence/01|02|03/qa-w.md. Non-blocking nit left: nested backticks in HANDOFF.md checklist item 5.

## Decisions that bind later work
- PO E1: off-default squad panes move silently; only panes with pending work get a wake prompt (clauses: cut-off/blocked, failed send, unanswered message; 30 min marker expiry; CSWITCH_WAKE=off = old behaviour).
- Unverified until live: bare `--resume` cost, clause 2 on a live batch, `blocked` herdr row (.derived). PO checklist in HANDOFF.md. Restart `cautoswitch` after install.
- windows/*.ps1 out of scope.

## Pointers
- Scope: .claude/squads/accounts/scopes/autoswitch/ (tasks/01.md design, 02, 03). Branch chain tip: squad/accounts/autoswitch/accounts-dev-autoswitch-3 (bc4e1e7). Manager: accounts-mgr-autoswitch.
- Probes: PYTHONDONTWRITEBYTECODE=1, clean clones in mktemp dirs (removed).
