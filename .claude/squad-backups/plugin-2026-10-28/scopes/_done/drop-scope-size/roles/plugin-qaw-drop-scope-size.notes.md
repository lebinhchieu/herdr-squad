# Notes: plugin-qaw-drop-scope-size (QA whitebox), saved 2026-10-28 (6th respawn, cost rule fresh)

## Latest (read first)
- Verdicts sent PASS: 01-10, 11 (final ca53ba7), 12 (final 59e2741, code c768b94; replaced earlier PASS on 309cc49), 14 (b2ee4e5), INT1, INT2, INT3, INT4 (final e265fd7).
- Task 13 (Dev plugin-dev-dsz-13, branch squad/plugin/drop-scope-size/plugin-dev-dsz-13, HANDIN cf3b5c0, code 4dde33e): pre-check CLEAN, notes `$SCOPE_DIR/evidence/13/qa-w.md`. NO verdict sent yet: waiting for Tech Lead (plugin-tech-drop-scope-size) to name the final sha (REV-3) and to confirm the deviation: AC says 0.6.0 in `process-version`, Dev left `process-version: 6` (bin/squadprocess.py accepts integer only; ADR 0016 retired it). On Tech's DECISION 13: if sha code unchanged since 4dde33e (check `git diff --name-only 4dde33e <sha>` is evidence-only) send `PASS 13` to plugin-dev-dsz-13 and `STATUS 13` to Tech. If code changed, re-check only the delta (LC-3b): rerun `cd tests; python3 -m unittest test_promotion_0_6_0 test_squad_spawn test_squad_respawn test_squadcompose test_old_language_inventory test_sizes test_dev_rules_size test_squadupgrade test_squadrules test_process_conversion test_squadprocess` (380 OK, 2 skip) and `python3 bin/squadrules_cli.py lint` (exit 0) on a git-initialised archive.
- After 13: nothing else known; wait for any new HANDIN (INT5? final integration, `--tz` receipts by Tech).

## Decisions that bind later work
- One verdict per task on the final sha the Tech Lead names (REV-3); verdict to Developer only (REV-12), STATUS to Tech Lead. Targeted tests only (SUITE-2b); read receipt if it covers the sha (SUITE-6).
- Never assert presentational values (REV-18a). Findings in `evidence/<task>/qa-w.md`, all style findings of a sha in one return (REV-17).
- Test from `git archive <sha> | tar -x -C $(mktemp -d)`; then `git init -q . && git add -A && git commit -qm x` in it so `git grep` tests work (inventory/promotion tests need it). Skips about "base sha not in this clone" are expected in archives.
- Tool quirks: the peers' hook mangles raw git diff/grep output; use python3 subprocess `git --no-pager diff --no-ext-diff --no-color ...` and print, or write to a file. Heredocs only.
- Lint: `python3 bin/squadrules_cli.py lint` (exit 0 empty). Compose-diff scripts /tmp/qaw11_s.py (hashes + sizes over 9 roles x 128 teams x goal x qa; arg: tree root, out pkl), /tmp/qaw11_v9.py (changed IDs vs v9 changelog rows); recreate if wiped.
- Hook rule: after 3 returns send BLOCKED to Team Lead (LC-7b) and tell Dev to consult advisor (LC-25).
- Spawned role names stay qa-whitebox/qa-blackbox; team keys qa-white/qa-black.

## Pointers
- `$SCOPE_DIR` = /home/chieule/workspace/squad/.claude/squads/plugin/scopes/drop-scope-size
- Tickets: /home/chieule/workspace/squad/.scratch/drop-scope-size/issues/NN-*.md; tasks/tech-design.md, tasks/spec.md, architecture.md in `$SCOPE_DIR`.
- Peers: plugin-tech-drop-scope-size (Tech Lead, rulings), plugin-tl-drop-scope-size, plugin-qab-drop-scope-size, plugin-mgr-drop-scope-size; Devs plugin-dev-dsz-12b, -13, -int4 (worktrees .worktrees/plugin/drop-scope-size/<dev>).
