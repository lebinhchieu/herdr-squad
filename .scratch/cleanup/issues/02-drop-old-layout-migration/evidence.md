# Evidence 02: drop old-layout migration

## Behaviour

Base: 60ce7a5. Scratch dirs only; commands run from the worktree.

**Removed** (all `git rm`): `bin/squad-migrate`, `bin/squadadopt.py`, `tests/test_squad_migrate.py`, `tests/test_squadadopt.py`. `squad-process adopt` removed from usage and dispatch; `skills/squad-process-update/SKILL.md` section "Adopting an old squad" removed.

**Zero-reference proof** (`grep -rn 'squadadopt\|squad-migrate\|squad-process adopt\|AdoptError'` over bin/ hooks/ skills/ agents/ templates/ tests/ docs/*.md README.md CONTEXT.md CLAUDE.md, minus `docs/adr/`, `.scratch/`, `skills/*/changelog.md`, `skills/*/history/`): 2 hits, both kept on purpose for task 01:
- `bin/squadprocess.py:269` message "run `squad-migrate` first" (dies with the legacy code in 01; Tech Lead design note).
- `tests/test_squadprocess_apply.py:149` asserts that message.
Also `skills/squad-process-update/history/process-v6.map.md:3` ("Shipped data for `squad-process adopt`"): deleted by 01.

**T2 scaffold identical.** `squad-process scaffold --squad-dir <scratch> --plugin-root <root> --new-pin "0.7.0 abcdef123456"`, base (git archive of 60ce7a5) vs this branch: stdout identical after path substitution, trees identical (`diff -r`). Second run: "nothing to create". Scaffold on a legacy squad (process.md only) still exits 2; only the text changed (no longer names `adopt`).
Scaffold test coverage moved to `tests/test_squadscaffold.py` (6 tests, assertions unchanged): scaffold layout + lint, qa-blackbox settings without code paths, never overwrites/refuses legacy; plus `show` retired + `apply` needs `--legacy`, no prompt calls `show`, live-squad overlay fixture lints (all three were in test_squadadopt but are not adopt tests; the `squadadopt.py` skip in the show scan dropped). Dropped (adopt-only, no scaffold coverage): MapData (3), TwoOpsOneItem, the adopt dry-run/resolve/backup/pin/settings cases, `test_adopt_with_nothing_to_adopt_exits_1`. From test_team_cli: ConverterTest (all), MigrateTest (3), LiveCopyTest. test_squad_migrate.py whole file. test_utf8_helpers MigrateTest; test_windows_safe squad-migrate entries; test_squad_spawn adopt-run in the pinned byte-identical test (test renamed, spawn half kept).

**T3** `squad-process adopt --squad-dir X` → `usage: squad-process [-h] {version,check,plan,compose,apply} ...` / `squad-process: error: argument cmd: invalid choice: 'adopt' (choose from version, check, plan, compose, apply)`, exit 2, no traceback. `squad-process --help | grep -c adopt` = 0.

**T4** old-format scope.md (`size: M`, `qa-b: yes`), `squad-process compose dev --home <h>`: exit 2, stdout empty, stderr:
```
scope.md:3: old format `size:`; replace the old scope lines by one `team:` line (ADR 0018)
scope.md:4: old format `qa-b:`; replace the old scope lines by one `team:` line (ADR 0018)
```
Legacy squad spawn still works; hint now: `legacy squad: plugin rules attached, local process.md edits not applied; new squads: squad-process scaffold (or /squad:squad-init)` (test_squad_spawn, test_utf8_helpers). Flat squad: `squad-start` message "uses the flat layout ...; squad-start refuses it" (test_squad_start).

**T5** `squad-process upgrade --check --squad-dir <process.md only>`: exit 2, `not composed: <dir> has no process.local.md; a v6 squad moves with `squad-process plan` / `apply``.

**T6** allow-lists: removed `bin/squad-migrate`, `bin/squadadopt.py` entries (test_old_language_inventory, test_promotion_0_6_0); no other count moved (reworded messages carry no `size` word).

**Messages reworded** (same exit codes): squadcompose old_format_error + docstrings, squadteam:88, squadupgrade:476,539 ("not composed"), squad-spawn:210,237, squad-start:327, squad-log-message:2, squad-process usage/apply text. Docs: README (0.6.0 paragraph, squad-migrate row, squad-process row, flat squads), CONTEXT 125/137/138, skills squad-init, squad-start, squad-process-update.

**Feature loss for the PO:** `squad-migrate --scope-to-goal` goes with the script (no caller).

**C2 tests run** (touched + `grep -rl` hits), all OK: test_old_language_inventory, test_promotion_0_6_0, test_squadcompose, test_squad_team, test_team_cli, test_squad_spawn, test_squad_respawn, test_squad_start, test_squadupgrade, test_squadscaffold, test_utf8_helpers, test_windows_safe, test_instructions, test_squadprocess_apply. Full suite: Tech Lead on the final sha (T8).

## Additions (Tech Lead FAIL 3d5bc64)

**T1b fixture:** `tests/fixtures/upgrade/live-squad.local.md` kept: `tests/test_squadscaffold.py` (live-squad overlay test) and `tests/test_squadupgrade.py` (glob) read it. The glob comment "built by `adopt`" removed.

**T2 message changes** (AdoptError renamed ScaffoldError; only text changed, exit codes same):
- `scaffold` on a legacy squad (exit 2): was "has a process.md: run `squad-process adopt` instead", now "has a process.md (a legacy squad): scaffold only makes a new composed squad".
- `squad-process apply` without `--legacy` (exit 2): "...for a squad that has not adopted (`squad-process adopt` moves it...)" → "...for a squad with only a process.md".
- squadcompose old-format (exit 2): "run `squad-process adopt` (dry run first) to convert the scope to a `team:` line" → "replace the old scope lines by one `team:` line (ADR 0018)".
- squadteam:88: "run `squad-process adopt --squad-dir <squad>` first" → "replace the old lines by one `team:` line by hand first".
- squadupgrade:476,539: "not adopted: ... run `squad-process adopt` first" → "not composed: ...".
- squad-spawn:210 hint, :237 warning; squad-start:327 ("would convert it, so it refuses" → "refuses it").
Byte diff of scaffold vs base: `diff` of stdout (paths substituted) and `diff -r` of the two scratch trees both empty.

**T3-T5 exit codes:** `squad-process adopt --squad-dir X` 2; old-format `compose dev --home <h>` 2, stdout empty; `upgrade --check` on process.md-only squad 2; flat `squad-start` refusal covered by test_squad_start (green); legacy spawn by test_squad_spawn (green).

**T6 counts** (bin/, `size` word): squad-log-message 1, squad-manager-guard 1, squad-respawn 2, squad-spawn 2, squadcompose 4, squadreport 3, squadreport_rollup 3, squadrules 10, squadruntime 4, squadteam 2, squadupgrade 4. Inventory (`size:` etc.): squad-log-message 1, squad-respawn 2, squad-spawn 2, squadcompose 4, squadinbox 1, squadreport 3, squadreport_rollup 3, squadrules 10, squadruntime 1, squadteam 2, squadupgrade 4. Only change: the two removed files' entries.
