# Notes: plugin-qab-drop-scope-size (QA blackbox)

## Now
- Respawned (cost rule) 2026-10-28 after step L + 13 check. No code folders (SAFE-10). Use `rtk proxy grep/diff`. `rm` on /tmp denied: scratch left for the PO.
- Verdicts sent: 01-12, 14, INT1-INT4 all PASS. 12 PASS on final 59e2741 (code c768b94; F1 AC 21 closed; evidence/12/qa-b.md Round 2). TL STATUS L: integration sha = 12 final 59e2741 (+ evidence-only merge 17b88b9).
- Step L: PASS sent (done).
- 13: checked cf3b5c0 (HANDIN from plugin-dev-dsz-13), evidence/13/qa-b.md written: AC 24, 25a-e, 29, F1 spawn text, lint all PASS. NOT sent yet: need (REV-3) Tech Lead DECISION naming final sha + clean --tz receipt on it for AC 10 (Dev receipt is c98a6d2 clean=no, 2 flake files). Then send PASS 13 to plugin-dev-dsz-13 (+STATUS to TL). Clone: /tmp/tmp.jreQ3pHPrb/r (needs git checkout for test_promotion_0_6_0).
- My copy of scratch squad: /tmp/tmp.d3gmRCkZgw/p (Manager's: /tmp/dsz-live/{sq,tree}); use SQUAD_DIR=<p>/.claude/squads/sq SQUAD_PLUGIN_DIR=/tmp/dsz-live/tree, `squad-team --home <scope> --plugin-root tree`.

## Open threads
- Ticket 13 promotion: AC 25 (CONTEXT.md **Team**/**Duty owner**/**Checker**, no **Size**; ADR 0018; `_removed.md` tombstones with replaced_by for every removed ID in changelog v9; v9 block; plugin 0.6.0). Evidence evidence/13/qa-b.md.
- (done) Live Manager run = step L (iterations/1.md), on integration sha after 12 merges, before 13; TL sends the sha. 3 briefs (open question + risk flag; new screen; one-line fix). I verify AC 1-6, 16, 18, 31, plus AC 29 for the Manager's proposal text (no whole-word "size").
- AC 10, 24, 25, exact owners of 9 and 28 from suite receipt; AC 24 sweep: `python3 -I /tmp/tmp.DqkLzlngXq/sweep.py W B` (last max 5034 B).

## Decisions that bind later work
- PO: P1 no (Manager never adds Designer/Architect mid-scope w/o PO yes); P2 all team shapes valid; token names `qa-white`, `qa-black`; no shim, old squads must migrate.
- Evidence to `$SCOPE_DIR/evidence/<task>/qa-b.md` (REV-11). Re-check only changed files on return (LC-3b).
- Method: scratch scope.md with `plugin: 0.6.0 abc1234`, `team:`; `<tree>/bin/squad-process compose <role> --home D --plugin-root <tree> --out F`; overlays need `--squad-dir D` with `scopes/x/scope.md` + `process.local.md` + `plugin.pin`; `upgrade --check --squad-dir D --old-root <git archive 2949573> --new-pin "0.6.0 abc1234def56"`; `adopt --squad-dir D --new-pin ... [--yes]` needs process.local.md. Spawn tests: run with `env -u SQUAD_DIR -u SCOPE_DIR ...` (else it hits the REAL squad), runtime copy named `_runtime/0.5.2-<sha>` while version is 0.5.2; suite's herdr stub (tests/test_squad_start.py FAKE_HERDR) for squad-start, needs HERDR_ENV=1, HERDR_LOG.
- Branch tests of ticket N alone show old text from unmerged tickets: merge onto the integration branch in a scratch clone.
- _runtime/0.5.2-* is a symlink to the REAL runtime: never rm under it.

## Pointers
- spec: tasks/spec.md (Business AC ~line 102); tech: tasks/tech-design.md; architecture.md; ADR draft tasks/adr-0018-team-replaces-size.md
- roster: roster.md (TL = plugin-tl-drop-scope-size, Tech Lead = plugin-tech-drop-scope-size, QAW = plugin-qaw-drop-scope-size, Dev 12 = plugin-dev-dsz-12b, Dev 11 = plugin-dev-dsz-11, Dev INT4 = plugin-dev-dsz-int4)
- evidence: evidence/{01-10,11,12,14,INT1,INT2,INT3,INT4}/qa-b.md
- Scratch (PO may delete): /tmp/qab-int4-composes, /tmp/tmp.5kNorT0TuN (12 branch), /tmp/tmp.0G0K7e8JJw (12 merged onto INT4 clone), /tmp/tmp.6zESLql7Gv, /tmp/tmp.rxX5gnieNS, /tmp/tmp.km6t2hNXcc, /tmp/tmp.1JrxpdXjeo, /tmp/tmp.191C8q393G (0.5.2 archive), /tmp/tmp.9eTzALISox, /tmp/tmp.tBFmkrf3KF, earlier /tmp/tmp.* and /tmp/qab*
