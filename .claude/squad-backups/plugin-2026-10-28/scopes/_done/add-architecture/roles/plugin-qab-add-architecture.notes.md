# plugin-qab-add-architecture notes (retired)

## Now
All three tickets PASSed by QA blackbox and sent to the Developers; no open threads.

## Open threads
- Scratch dir /tmp/tmp.I1ysXt2Voh (+ /tmp/qab_scratch pointer) not removed: safety check blocked rm. PO/Manager to delete.

## Decisions that bind later work
- 01 sha 67e0d05 PASS; 02 sha a4a70ab PASS (2de2487 full check, a4a70ab re-check); 03 sha 5189427 PASS.
- Manager ruling: compose facts header prints `architecture yes` only when on.
- Note on 02: CORE-3 text not edited (WHO-2e carries the owner delta); old WHO-2d/SIZE-22 irreversible rows still print in yes scopes, overridden by WHO-2e/SIZE-22a.

## Pointers
- Evidence: $SCOPE_DIR/evidence/01/qa-b.md, 02/qa-b.md, 03/qa-b.md
- Method: scratch squad with scopes S/M/L x architecture yes/no/absent x design yes/no; `squad-process compose <role> --home --now <fixed>` vs `git archive` of base; `squad-process lint`; `squad-spawn architect --dry-run`.
- Tool quirks: cd into worktrees is denied (use absolute paths); diff/log of worktrees denied; use /usr/bin/diff (rtk wraps diff); avoid `;;` in case statements.
