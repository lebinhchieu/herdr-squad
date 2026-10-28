# BA notes: drop-scope-size

## Now
- tasks/spec.md is final (E4 applied, architecture amended). QA blackbox agreed AC 1-31 on condition of E1-E6; all applied in spec.md (REV-8 closed). Manager and Team Lead told.
- Nothing pending on my side except replies to new asks.

## Open threads
- PO P1/P2 (E3) still open; spec follows my proposals (P1: PO confirms Designer/Architect adds; P2: all 128 shapes valid).
- PO E5 (Read for QA blackbox on scope folder) open; if enabled, point QA at tasks/spec.md instead of pasting.
- Optional: Manager may want the agreement logged in iterations/1.md (offered, not asked).
- PROMO-3a hand-over lines are in spec.md "Hand-over to promotion"; give to Tech Lead when promotion task starts.

## Decisions that bind later work
- team: tokens: ba, tech-lead, team-lead, qa-white, qa-black, designer, architect. when: presence keys: ba, tech-lead, team-lead, qa-white, qa-black, design, architecture. Role/agent names (qa-whitebox, qa-blackbox) and term QA unchanged.
- No shim, no dual support: old squads migrate with `squad-process adopt`; engine rejects size:/design:/architecture:/qa-b: lines and old when: keys. Pinned scopes (<0.6.0) untouched. Brief `size:` is ignored.
- No command writes first `team:` (Manager edits scope.md); blank = undecided, `team: none` = minimal.
- AC numbers 1-31 stable (tickets cite them); 24-25 and 26-28 sit out of order on purpose.
- Live Manager run on 3 briefs needed for QA blackbox (AC 1-6,16,31); suite receipt covers AC 10,24,25 and owners in 9,28.

## Pointers
- spec: $SCOPE_DIR/tasks/spec.md; architecture.md; tasks/tech-design.md; tickets .scratch/drop-scope-size/issues/
- Agents: mgr plugin-mgr-drop-scope-size, arch plugin-arch-..., tech plugin-tech-..., tl plugin-tl-..., qaw plugin-qaw-..., qab plugin-qab-...
