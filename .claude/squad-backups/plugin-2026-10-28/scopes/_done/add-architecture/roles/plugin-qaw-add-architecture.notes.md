# Notes plugin-qaw-add-architecture (QA whitebox, scope add-architecture, M)

## Now
- RETIRED. Tickets 01-04 all PASSED whitebox and sent: 01 sha 67e0d05, 02 a4a70ab, 03 5189427 (+ doc-only 8e10686), 04 29edfe9 (plugin.json 0.6.0 -> 0.5.2).
- Full suite `--tz` OK: 1556 tests on 5189427 (evidence/suite/) and again on 29edfe9 (evidence/04/suite-default.txt, sha line clean=yes). No QA blackbox for 04 (PO informed).
- promote.md checked (PROMO-8): matches CONTEXT.md, ADR 0017, README.

## Open threads
- None. If a Developer adds a commit after 29edfe9: confirm doc-only (git diff 29edfe9..new), else rerun suite on a clean clone (python3 -B tests/run_suite.py --receipt $SCOPE_DIR/evidence/<n> --tz).
- Left behind: /tmp/tmp.n62ivIvDWm (old clone from 03 run, rm was blocked); safe to delete.
- Never run squad-process without -B in a Dev worktree (leaves bin/__pycache__).

## Decisions that bind later work
- Facts header prints `architecture yes` only when on (flag-off byte-identical).
- Manager FINAL 02: 5 KiB Dev limit holds flag-off and flag-on M/L; flag-on S pinned exactly.
- ADR 0005 superseded by 0016: release unit = plugin.json version + changelog v8 + history/process-v8. Plugin version is now 0.5.2 (PO chose patch bump; changelog `## v8` is a snapshot number, not the plugin version).

## Pointers
- Scope: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/add-architecture (evidence/01..04/qa-w.md, evidence/suite/, promote.md)
- Agents: plugin-dev-add-architecture-1, -2, -3; Manager plugin-mgr-add-architecture.
