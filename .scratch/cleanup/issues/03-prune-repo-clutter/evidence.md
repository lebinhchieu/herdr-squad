# Evidence 03: prune repo clutter
sha: 09ab86f
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

## Behaviour
- Deleted: 6 backups, `handover/2026-10-13-retire-kill.md`, `SETTINGS-NOTES.md`, 385 `.scratch/_done` files (393 total; `git diff --stat --diff-filter=D`: nothing outside the four allowed paths). Kept: `mapping.md`, `TODO.md`, `tests/fixtures/*`.
- Only edit outside deletes: comment at `tests/test_squadsettings.py:79` (file name dropped).
- PO untracked dirs `accounts-2026-10-28/`, `plugin-2026-10-28/` are not in this worktree (untracked, live in the main checkout): untouched by construction.
- Live `.scratch/` dirs: file counts per dir identical before/after (only this evidence dir is new, `.scratch/cleanup/`).
- No README/CONTEXT/ADR link points at a deleted path (grep of md/py outside `.scratch`: only code/tests that build tmp `squad-backups` dirs).
- Tests green: test_process_conversion, test_squadsettings, test_squad_close, test_squad_start, test_squadupgrade, test_squadprocess_apply, test_squad_migrate.

## QA whitebox review

### QA whitebox 03, sha 09ab86f: PASS
- P1 candidate list commit 6a8aeae precedes delete commit 475d55e.
- P2 `git diff --diff-filter=D main 09ab86f`: 6 backups, handover/, SETTINGS-NOTES.md, 385 `.scratch/_done` files; `_done` keeps only `composed-process/issues/03-convert-process-to-rules/mapping.md`. PO's untracked dirs not in diff.
- P3 test_process_conversion green (run in scratch export of the sha).
- P4 `_done` hits in tests/ are tmp-tree builds; only `test_process_conversion:16` reads the repo `.scratch/_done` (kept file). `test_team_cli` LiveCopyTest reads a live squad dir, skipped if absent.
- P5/P6 non-delete changes: new evidence.md and the `tests/test_squadsettings.py:79` comment. TODO.md and tests/fixtures kept.
- No reference to deleted paths in bin/ hooks/ skills/ agents/ templates/ tests/ README.md CONTEXT.md CLAUDE.md docs (outside `.scratch`, ADRs).
- Note: the suite tests that use `git grep` fail in a `git archive` copy (no .git); same failures on main: environment, not the branch.

## QA blackbox review

### QA blackbox 03 (sha 09ab86f, base 60ce7a5)

Method: same CLI commands run from main (60ce7a5) and from the 03 worktree, scratch HOME + scratch squad dir, SQUAD_* env unset, paths and sha normalised. Outputs and exit codes compared.

| AC | Did | Saw | Result |
|---|---|---|---|
| No CLI change | `squad-process` --help, bogus (exit 2), adopt (exit 2), scaffold --help, scaffold on scratch dir (13 files created, file list + contents compared), mode/lint/team/upgrade --help, `upgrade --check`, `squad-start/spawn/close --help`, `squad-migrate --help` | identical output + exit codes both trees; only difference is the pin sha in the "pinned runtime is missing" message (`0.6.0-60ce7a59644e` vs `0.6.0-09ab86fca548`), expected: it names the plugin build | PASS |
| Only the listed paths removed | name-status main..09ab86f: 393 D (385 `.scratch/_done`, 6 `.claude/squad-backups/*.md`, `handover/2026-10-13-retire-kill.md`, `SETTINGS-NOTES.md`), 1 A (this task's evidence.md), 1 M (`tests/test_squadsettings.py`) | matches design notes | PASS |
| `_done` mapping.md kept | `find .scratch/_done -type f` | only `composed-process/issues/03-convert-process-to-rules/mapping.md` | PASS |
| TODO.md kept | ls | present | PASS |
| PO's two untracked backup dirs untouched | `git status` in main | both still `??`, branch worktree status clean | PASS |
| Live `.scratch` dirs untouched | ls | same 5 live feature dirs + `cleanup` + `_done` | PASS |

Verdict: PASS. Not checked (whitebox/TL): test suite, link check, comment-only edit.
