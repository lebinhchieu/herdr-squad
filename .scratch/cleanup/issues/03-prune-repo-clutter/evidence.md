# Evidence 03: prune repo clutter

## Candidate list (committed before the delete commit)

Base: 60ce7a5. Reader greps exclude .git, .worktrees, .scratch/_done.

| Path | Reader grep (files outside the candidate) | Decision |
|---|---|---|
| `.claude/squad-backups/plugin-process-2026-10-16-2.md` | none | git rm |
| `.claude/squad-backups/plugin-process-2026-10-16.md` | none | git rm |
| `.claude/squad-backups/plugin-process-2026-10-17.md` | none | git rm |
| `.claude/squad-backups/plugin-process-2026-10-19-2.md` | none | git rm |
| `.claude/squad-backups/plugin-process-2026-10-19.md` | none | git rm |
| `.claude/squad-backups/plugin-process.local-2026-10-27.md` | none | git rm |
| `.claude/squad-backups/accounts-2026-10-28/`, `plugin-2026-10-28/` (untracked, PO's) | n/a | leave |
| `handover/2026-10-13-retire-kill.md` | none | git rm |
| `SETTINGS-NOTES.md` | tests/test_squadsettings.py .scratch/drop-scope-size/issues/14-settings-qab-read-deny-rm-tmp.md  (comment only in test; ticket 14 text) | git rm + reword comment |
| `TODO.md` | none | KEEP (open item, PO decides) |
| `.scratch/_done/composed-process/issues/03-convert-process-to-rules/mapping.md` | tests/test_process_conversion.py  | KEEP (task 01 removes) |
| `.scratch/_done/**` (385 other files) | tests: only tmp-tree `_done` dirs (test_squad_close, test_squad_start) and comments (test_squadcompose, test_team_duties); no path read | git rm -r |
| `tests/fixtures/*` | each subdir has a live reader | keep all |
| redundant tests | none identified | keep |

Dead pointers left: docs/adr/0011 -> .scratch/squad-plugin-windows/design.md; bin/squadupgrade.py:8, squadrules.py:3, squadruntime.py:11 -> .scratch/composed-process/...

## _done file count: 386
