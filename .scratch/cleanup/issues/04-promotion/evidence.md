# Evidence 04: promotion, ADR 0019
## Behaviour

Branch already holds 01-03 (01 stacked on 02; 05 on top): no merge needed. `git merge-base --is-ancestor` of each passed sha vs HEAD: 5274494 (02) yes, 6ab2bf7 (03) yes, 7c41807 (01) yes. Base fd4cd9a (05 passed).

**Change:** one new file `docs/adr/0019-drop-process-history-and-old-layout-migration.md`, copied from promote.md section 1 (PROMO-5). Only change: `<merge sha>` -> "the squad/plugin/cleanup branch" (promote.md's own instruction). CONTEXT.md and README.md: no edit (promote.md sections 2, 3; checked: line 125 says composed/legacy only, README "Flat squads" says `squad-start` refuses; no `adopt`/`squad-migrate`/`history/` left).

**D1** ADR text == promote.md block (script extract). **D2** sweep (`git grep` of the D2 pattern over README CONTEXT docs skills agents bin hooks templates tests CLAUDE.md, minus ADRs 0001-0018 and changelog.md): hits only `tests/test_squad_spawn.py:656`, `test_squad_start.py:355,512,514` (tests asserting `process_update` is absent) and ADR 0019 (history). No hit in README/CONTEXT/bin/skills. **D3** previous ADR 0018; heading and `Status:` / `**Overrides:**` shape match 0018. **D4** ADR 0019 paths: `bin/squadscaffold.py` exists; `bin/squadprocess.py` is gone (listed as removed); `squad-process mode` prints composed | legacy | none (bin/squad-process); `squad-process version` -> argparse usage error, rc 2 (live). **D5** `git diff fd4cd9a --stat`: the ADR only.

**Tests run:** test_promotion_0_6_0 (8) OK, test_team_cli (12) OK (the two files that mention `docs/adr`). Full suite `--tz`: Tech Lead.
