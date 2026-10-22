# 27 Integration evidence

## Behaviour

**Merges** (`--no-ff`, on pf-3 @858f670 chain, base 4901cab): pf-3 (21), pf-1 (10), pf-2 (12), pf-4 (14), pf-8 (26, brings 11+10), pf-7 (25, brings 13+10). pf-1 was not contained in pf-3: merged. Only conflict: `templates/squad/process/iterations.md`.

**Ancestor checks** (`git merge-base --is-ancestor <sha> HEAD`, all exit 0): 10 0f1a68c, 11 3be9c32, 12 054bf37, 13 a6e06f0, 14 99796ce, 21 27df79d, 25 9905c0c, 26 57335d5 — all `ancestor-ok`.

**ITER-12 resolution:** kept 11's text (Manager notice; "The cost hook never nudges you…" dropped), kept ITER-13..ITER-16 exactly as 13 wrote them. Result paragraph:
`Reset after each check-in when the scope goes on. Once the PO's decisions are in the iteration file, update your notes and run squad-respawn $SQUAD_NAME. The new session opens in a new tab; tell the PO to continue there.`

**Extra fix (cross-ticket defect):** 26's COST-13/COST-14 carry `(S: …)` clauses; `test_process_conversion.test_no_size_clauses_in_rule_text` (from 22/23) failed on the merge. Split each into `COST-13a/13b`, `COST-14a/14b` with `when: size = S` / `size in M, L`, same roles/aware, wording identical apart from the Team Lead/Manager swap. Commit "split COST-13/14 by size".

**Folder moves** (`git mv`, pure rename): 10-drafts-never-in-project-root, 11-manager-usage-notice, 12-ledger-replaces-copies, 13-retro-loop, 14-qa-blackbox-optional-no-ui, 25-runtime-cleanup-at-close, 26-coach-cost-lessons: each `.evidence` → no suffix. `find .scratch -name '*.evidence'` → 0; `git ls-files | grep '\.evidence/'` → 0.

**Tests** (cwd tests/, `env -u SCOPE_DIR -u SQUAD_DIR -u GOAL_DIR`, `PYTHONDONTWRITEBYTECODE=1`, TMPDIR temp; the 17 named modules all exist): 447 tests, 1 skipped, OK after the COST fix (first run: 1 failure, the one above). Re-run of dev_rules_size, process_conversion, processlint, templates, squadcompose, instructions: 136 OK. `squad-process lint`: exit 0, no output.

**Dev rules size:** composed for all 12 size×design×goal combos: max 5112 B (limit 5120); delta vs 4901cab between −14 B and +6 B per combo.

**Composed diff vs 4901cab** (fixture scope without qa-b, union over size/design/goal combos; rule IDs added/changed):
- dev: COST-3, COST-5, REV-13b
- manager: CLOSE-2, CLOSE-5, COST-8, COST-13a/b, COST-14a/b, FILE-11, ITER-12, ITER-15, ITER-16, LC-7a/b, MRG-2, MRG-5, SIZE-19, Index
- ba: COST-13a/b, COST-14a/b, FILE-11
- team-lead: COST-13b, COST-14b, FILE-11, ITER-3, LC-17, LC-7b, MSG-19, NOTE-3
- tech-lead: COST-13/14 a/b, EVID-1, FILE-11, FILE-9, Index
- qa-whitebox, qa-blackbox: COST-13/14 a/b, EVID-1, FILE-11, FILE-9, REV-12
- designer: COST-13/14 a/b, FILE-11, FILE-9
All other rules byte-identical. Probes ran in temp dirs, SCOPE_DIR/SQUAD_DIR unset; no writes to real scope logs.

Not run (Tech Lead owns): `--tz` suite.

## Suite fixes (after Tech Lead `--tz` FAIL on 199a01a)
- `test_team_lead_role`: pin updated to ticket 12's ITER-3 wording (test only).
- `test_qab_optional`: golden regenerated from the merged tree (it legitimately adds rules from 10-13, 25, 26); 14's byte-identity to 4901cab was proven at 99796ce. New check at the merged sha: compose with no `qa-b` line equals `qa-b: yes` for every role and size.
- `test_squadinbox.test_no_pyc`: stale `__pycache__` deleted; runs use `PYTHONDONTWRITEBYTECODE=1`.
- The 3 files: 77 tests OK.
