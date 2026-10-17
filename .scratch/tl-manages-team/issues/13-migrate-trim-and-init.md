# T13 · `squad-migrate --to layered-settings` and squad-init writes layered files
Status: ready-for-agent
Type: task
Blocked by: T10 passed (QA whitebox). Branch from T10's passed sha.
Repo: /home/chieule/workspace/squad
Spec: PO E3/E4 rule 2 · Design: ../design.md decisions 17, 19, 21 · Technical AC: AC-14 below (QA-W to confirm)

## Files this task touches (and no others)
`bin/squad-migrate`, `skills/squad-init/SKILL.md` (section 3, and the one line in section 5 only if it names settings), `tests/test_squad_migrate.py`.

## Do
1. **`squad-migrate <squad> --to layered-settings [--adopt-template-rules] [--dry-run] [--no-backup]`**: add `layered-settings` to `--to` choices; it takes neither `--scope` nor `--goal` (adjust the argument checks; the two existing forms behave as before). Uses `squadsettings.trim` and `equivalent` from T10 for every `settings/<role>.json` of the squad that has a template and no stamp, as design decision 19. Backup is a copy of `settings/` only, to `<project>/.claude/squad-backups/<squad>-settings-<date>[-n]` (`--no-backup` skips it). Write each file atomically (`write_atomic`), then re-read and check equivalence again; on any failure restore the backup, print how, exit 1. A stamped file: "already layered". A file with no template, or not `<role>.json`: untouched, one note line. `--dry-run` prints per file what is kept, dropped, removed, adopted, and the summary; changes nothing (not even the backup).
2. **Summary output** ends with: files trimmed, template rules kept off by `remove` (list), rules adopted, the minimum plugin version (`MIN_PLUGIN`), and the line "a teammate on an older plugin keeps every deny and is asked for more permissions". The `process-log.md` row is written by the Manager (say so in the output); the script does not edit it.
3. **`skills/squad-init/SKILL.md` section 3** rewritten for layered files: no copy of the templates; write `settings/<role>.json` only for a role that needs an addition, with the stamp (`"squadSettings": {"layer": 1, "minPlugin": "<MIN_PLUGIN>"}`, value from `squad-settings`/the module, never typed from memory); QA blackbox: `deny` entries `Read(//<absolute code path>/**)` per code folder plus `Read(//<root>/.worktrees/**)`, and `"remove": {"deny": ["Read(//CODE_PATHS_SET_BY_SQUAD_INIT/**)"]}`; every role: `allow` for the project's exact test and lint commands; "Keep every deny rule" replaced by "the template's deny rules apply by themselves"; validate with `squad-settings show <role>` instead of `jq empty`. Do not change other sections.
4. **Tests** (`tests/test_squad_migrate.py`, temp squads, the plugin root's real templates): a full-copy squad becomes layered and `combine` of each result equals the original (default) or original plus adopted (`--adopt-template-rules`); `deny` entries kept; missing template allow goes to `remove` by default and the output lists it; backup holds the originals and `--no-backup` makes none; `--dry-run` changes and creates nothing; a second run says "already layered" and changes nothing; a file with no template and a stray `.swp` are untouched; a forced failure (make `equivalent` fail, by monkeypatching) restores the files and exits 1; the existing `--to per-scope` and `--scope-to-goal` tests pass unchanged. A test that reads SKILL.md section 3 and checks it names `squad-settings show`, the stamp, and the `remove.deny` placeholder entry.
5. **Run only the test files you touched**; never the full suite. `PYTHONDONTWRITEBYTECODE=1`.

## Technical AC (AC-14)
- AC-14.1 Dry-run then real run on a **copy** of the live `.claude/squads/plugin/` squad (copy the folder to a temp project, run there): output saved in `dev-evidence.md`; each file's effective permissions before and after are equal (default) and the three rules the live `team-lead.json` lacks appear in the "kept off" list. The live squad is not touched.
- AC-14.2 `squad-spawn <role> --show-settings` on that migrated copy prints the same permissions as before the migration (needs T12; QA-W checks it on the integration branch instead if T12 has not passed).
- AC-14.3 Restore path works: after a forced failure the squad's `settings/` is byte-identical to the backup.
- AC-14.4 No file outside `settings/` and `squad-backups/` is written.

## Business AC
PO E4 rule 2: the trim runs only through `squad-migrate`; full-copy files keep working unchanged until then; the trimmed squad records the minimum plugin version.

## Amendments (Tech Lead, 2026-10-17, from QA-W v6)
- **A16 denies (decided):** a template **deny** the copy lacks is **adopted by default** (it is not written into `remove.deny`): adopting a deny is the fail-safe direction. `--keep-template-denies-off` writes it into `remove.deny` instead. `--adopt-template-rules` still applies to allows only. Dry-run and summary list the missing denies in their own block, "template DENY not in your copy, adopted" (or "kept off" with the flag), separate from the allows. A test pins each default. AC-14.1 lists the denies each live file lacks.
- **A17 restore:** read every file into memory before writing, so `--no-backup` still restores (from memory) and never leaves a half-trimmed squad. A test forces a failure while writing file k of n: files 1..k-1 are restored, the rest untouched, and `settings/` is byte-identical to the original (hash per file), with and without `--no-backup`.
- **A10** `bin/squad-migrate` sets `sys.dont_write_bytecode = True` before importing `squadsettings` if it does not already.
