# Evidence: 04 Untrack dev state from the plugin repo

## Behaviour

Change (sha 19148df, base d39675b = ticket 01): `git rm -r --cached .claude/squad-backups` (4007 tracked files, all of `.claude/`), `.claude/squad-backups` added to `.gitignore`. No history rewrite; files stay in history.

Fresh-install proxy: `git archive 19148df | tar -x -C <empty mktemp dir>`:
- files: 560 (was 4556 at base caf9f6e per design)
- size: 3,918,784 bytes (< 5,000,000)
- longest relative path: 91 chars (`.scratch/squad-close-keeps-manager/issues/02-closing-rules-and-process-md-match/evidence.md`); 91 + 75 cache prefix = 166 < 200

Existing squads: `git ls-files .claude` is empty after; `.claude/squads` was already ignored and untracked, untouched (`git status --short .claude` empty). `squadupgrade._backup` creates `squad-backups` itself.
Tests: `grep squad-backups` in tests/bin/skills/hooks: only `bin/squadupgrade.py:475` (makedirs) and `tests/test_squadupgrade.py:219` (tmp dir). `cd tests && python -m unittest test_squadupgrade test_squad_close` on Windows: 104 run, 82 errors, all `WinError 193` (script launch, ticket 03), 1 skip (pre-existing); the diff touches no code. Linux run: Tech Lead.
Merge risk (design): merging deletes `.claude/squad-backups/` from the PO's working tree; history keeps it.
