# plugin-mgr-drop-scope-size notes

## Now
- PO picked team per role (E2 answer b): BA, Architect, Tech Lead, Team Lead (dev cap 3), QA whitebox, QA blackbox. No Designer. `size: L` stays only as rule key.
- Scope re-pinned to 0.5.2 (294957333ee4, main merge with Architect) for the Architect; runtime built with `squad-process runtime --home $SCOPE_DIR --plugin-root /home/chieule/workspace/squad`.
- Respawned as sonnet high (PO; roles/<me>.overrides + `model manager:` in scope.md). Nothing spawned yet.

## Open threads
- DONE: spawned Architect, BA, Tech Lead (2026-10-27). NEXT: wait for architecture.md final (DECISION from Architect), then spawn Team Lead (dev cap 3) + QA whitebox + QA blackbox with prompt pointing at scope.md, iterations/1.md, architecture.md. Check-in: copy E2 outcome to iteration file (already in Log), delete row 2 from escalations.md.
- 2026-10-27: architecture final; Architect retired. Waiting PO: E3 (P1/P2=I8), E4 (I1-I7). On answer: DECISION to BA/Tech Lead if changed, then spawn Team Lead (cap 3) + QA whitebox + QA blackbox. ADR draft: tasks/adr-0018-team-replaces-size.md; plugin 0.6.0.
- 2026-10-27 E4 answered (see iterations/1.md Log). Architect amending; BA, Tech Lead respawned. NEXT: on 'architecture amended' DECISION, spawn Team Lead (cap 3) + QA whitebox + QA blackbox. E3 still open: asked PO in chat if 'all others agree' covered it (unclear). Role/term QA kept; PO unsure QA vs QC, I recommended keep QA.
- 2026-10-27 Pod fully spawned (arch retired). Watch Team Lead only (SPAWN-10b). E3 still open (P1/P2=I8). Tell PO at check-in: pinned scopes untouched; scaffold; QA vs QC kept QA. Retro: BA/Tech panes died once; Architect needed 3 spawns (draft, rewrite, amend).
- E3, E5 answered. Interim: squad settings/qa-blackbox.local.json codePaths = dummy path; remove when ticket 14 lands. Ticket 14 = Read deny removal + rm /tmp allow. At check-in: draft plugin proposal? (ITER-15) no, ticket 14 covers it. Remaining PO-facing: check-in when tasks pass.
- (old) read 0.5.2 architecture rules (`squad-process rule` for ARCH/architecture-gated ones) for spawn order: Architect designs before the plan. Then spawn Architect, BA, Tech Lead, Team Lead, QA whitebox, QA blackbox; default models (PO confirmed no changes). First prompts point at scope.md + iterations/1.md (Team table, open questions a–g go to BA; targeting-model design to Architect).
- E2 answered in inbox; copy outcome into iteration file at check-in (already logged in Log).

## Decisions that bind later work
- PO wants roles picked per scope need, not size (this is also the scope's target).
- ADR 0016 (Sizes, SIZE-22) and ADR 0017/SIZE-3 contradicted by brief: promotion writes a superseding ADR, `_removed.md` tombstones, changelog, version bump.
- Architect role is new in 0.5.2 and untested live; watch it, note friction in retro.

## Pointers
- Brief: scope.md. Plan + Team table: iterations/1.md. Risk: open scope squad-close also touches repo (don't read its folder).
- 2026-10-27 15:50Z: whole pod's panes lost (herdr restart); Manager respawned TL/Tech/QAW/QAB via squad-spawn (squad-respawn needs a live pane). Devs 07/04/10 dead; TL to respawn them. Mention in retro: pane loss twice. NEXT: watch TL only.
- 2026-10-28 ASK 11 (AC 24 vs 32 over-cap team sets) moot: Tech withdrew exception; AC 24 stands, Dev trims. If Tech returns with numbers, AC amend goes via PO (REV-7).
- 2026-10-28 Step L Manager side DONE (evidence/L/manager-run.md; scratch /tmp/dsz-live, delete at close). QAB verifying; then TL runs 13. Retro: scratch squad needs process.md + --plugin-root until 13 bumps plugin.json; finding F1 spawn-refusal wording.
- 2026-10-27 PO: 'Merge, close & sleep when done' = standing request to merge the integration branch (checked sha, MRG-2) once 13 + L pass, then close (retro, Token Coach ITER-6b, check-in item), then squad-retire me. Waiting on TL: 13 verdicts, L re-check. iterations/1.md at 80 lines: trim before retro.
- 2026-10-27 all tickets+L passed. Merge BLOCKED: 15 untracked .scratch/drop-scope-size/issues/* in root clash with branch (9 differ); backup in tasks/root-untracked-backup; my rm was denied by auto classifier -> asked PO (inbox). Merge sha e52d366 (evidence-only on cf3b5c0). Retro filled; Token Coach spawned (plugin-coach-drop-scope-size) - wait for its message, accept top 3 (ITER-10), retire it. Then check-in item, squad-close, squad-retire me. Delete /tmp/dsz-live at close.
- 2026-10-27 merge e52d366 after PO committed tickets: still 9 add/add conflicts (02,03,07,08,10,11,12,13,14), aborted (MRG-3). Coach file rewritten skimmable (top 3 = proposals 1-3, 4 to Backlog). Waiting PO: resolve or discard root copies. ITER-10 acceptance into overlay still to do (placeholder rule IDs need mapping).
- 2026-10-27 merged 60ce7a5, check-in sent, coach retired. NEXT: squad-close plugin --scope drop-scope-size, then PO runs squad-retire me.
