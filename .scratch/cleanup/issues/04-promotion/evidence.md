# Evidence 04: promotion, ADR 0019
## Behaviour

Branch already holds 01-03 (01 stacked on 02; 05 on top): no merge needed. `git merge-base --is-ancestor` of each passed sha vs HEAD: 5274494 (02) yes, 6ab2bf7 (03) yes, 7c41807 (01) yes. Base fd4cd9a (05 passed).

**Change:** one new file `docs/adr/0019-drop-process-history-and-old-layout-migration.md`, copied from promote.md section 1 (PROMO-5). Only change: `<merge sha>` -> "the squad/plugin/cleanup branch" (promote.md's own instruction). CONTEXT.md and README.md: no edit (promote.md sections 2, 3; checked: line 125 says composed/legacy only, README "Flat squads" says `squad-start` refuses; no `adopt`/`squad-migrate`/`history/` left).

**D1** ADR text == promote.md block (script extract). **D2** sweep (`git grep` of the D2 pattern over README CONTEXT docs skills agents bin hooks templates tests CLAUDE.md, minus ADRs 0001-0018 and changelog.md): hits only `tests/test_squad_spawn.py:656`, `test_squad_start.py:355,512,514` (tests asserting `process_update` is absent) and ADR 0019 (history). No hit in README/CONTEXT/bin/skills. **D3** previous ADR 0018; heading and `Status:` / `**Overrides:**` shape match 0018. **D4** ADR 0019 paths: `bin/squadscaffold.py` exists; `bin/squadprocess.py` is gone (listed as removed); `squad-process mode` prints composed | legacy | none (bin/squad-process); `squad-process version` -> argparse usage error, rc 2 (live). **D5** `git diff fd4cd9a --stat`: the ADR only.

**Tests run:** test_promotion_0_6_0 (8) OK, test_team_cli (12) OK (the two files that mention `docs/adr`). Full suite `--tz`: Tech Lead.

## QA blackbox

### 04 QA blackbox (final sha fa6dd95; evidence-only c66bf6f on top; a865a77 superseded, same content)

Docs-only task. Checked the ADR/CONTEXT/README text against the running tool.

| AC | Did | Saw | Result |
|---|---|---|---|
| ADR 0019 exists, numbering | `ls docs/adr` | 0018 then 0019-drop-process-history-and-old-layout-migration.md; overrides/unchanged lines name 0018, 0005, 0016, 0004 | PASS |
| Records loss of `squad-migrate --scope-to-goal` | read ADR | Consequences: "`squad-migrate --scope-to-goal` is gone"; converters section names both tools | PASS |
| Removed `squad-process` commands exit 2 | `version`, `check`, `plan`, `apply --legacy`, `adopt`, `compose --out x` | each rc 2 argparse usage error, no traceback | PASS |
| `squad-process mode` composed/legacy/none | scratch squads: process.local.md / process.md only / empty | composed / legacy / none | PASS |
| Old `scope.md` refuses and says so | `compose dev --home <scope with size:/design:>` | rc 2, "old format `size:`; replace ... by one `team:` line (ADR 0018)" | PASS |
| Legacy squad keeps spawning, flat squad refused | not re-run here: same behaviour as tested in 01/02 evidence (H4, T4), docs-only change since | n/a | PASS (by 01/02 evidence) |
| No stale mentions | `git grep` for squad-migrate, adopt, apply --legacy, process-v, process_update, templates/squad/process.md, history/ over README, CONTEXT, docs, skills, agents, bin, hooks, templates, tests, CLAUDE.md | hits only in ADR 0019, ADRs 0000-0018 (immutable), changelog v9 prose, and 3 tests that assert `process_update` is absent | PASS |
| README/CONTEXT edits | read diff vs main | 0.6.0 paragraph says replace lines by hand; migrate/adopt rows gone; Flat squads bullet says refused; CONTEXT legacy/Changelog/Process update entries lose adopt/history/squad-migrate | PASS |
| Links | path check of backticked paths | all resolve except runtime-only paths (`squad/...`, `shared/decisions.md`, `process/_removed.md`) and files the ADR says were removed | PASS |
| Removed files gone | ls bin, handover, SETTINGS-NOTES.md, .scratch/_done, .claude/squad-backups, skills/squad-process-update | absent; changelog.md + SKILL.md remain | PASS |

Non-blocking: ADR says "Removed commands fail as argparse usage errors, exit 2". True for `squad-process` subcommands; `squad-migrate` is gone as a file, so the shell says "No such file" (rc 127), not argparse.
Also (pre-existing, same on main): `squad-process --help` lists only lint, compose, team, rule, who.

## QA whitebox

### QA whitebox 04 on fa6dd95 (PROMO-8, D1-D6)
- D1: ADR 0019 == promote.md §1 (scripted compare; only `<merge sha>` -> "the squad/plugin/cleanup branch", as promote.md instructs). CONTEXT/README: promote.md says no edit; I read CONTEXT:124-140 and README:75: nothing stale (no adopt/squad-migrate/history/; "squad-start refuses" present).
- D2: sweep clean outside ADRs 0001-0018, 0019, changelog; only hits are 4 tests asserting `process_update` is absent.
- D3: 0019 follows 0018; Status/Overrides shape matches; Overrides named.
- D4: ADR claims verified at the branch: removed files gone (squadprocess.py, squad-migrate, process.md, history/, backups, _done, handover, SETTINGS-NOTES), TODO.md kept, version/check/plan/adopt/compose --out/apply --legacy exit 2, `mode` prints composed|legacy|none, flat squad refused (test_squad_start 45 OK).
- D5: 5274494, 6ab2bf7, 7c41807, a56d225 ancestors of branch; diff fd4cd9a..fa6dd95 = ADR only; c66bf6f evidence only. test_promotion_0_6_0 (8), test_team_cli (12) OK.
Not findings (wording in TL's promote.md, accepted text): "Dead pointers to `.scratch/_done/`" — the pointers actually read `.scratch/composed-process/...` and `.scratch/squad-plugin-windows/...` (they moved into `_done`, now pruned); "580 KB" history: I measured 476 KB in 75 tracked files at base (process-v*, history/, process.md), figure not reproduced.
Live flat-layout run skipped (scratch rm blocked by safety check); covered by the test.
Verdict: PASS.
