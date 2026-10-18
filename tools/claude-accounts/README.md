# claude-accounts

**Source of the two-account Claude launchers (`c`, `c1`, `c2`, `c3`, `cdefault`, `cswitch`, `cautoswitch`). `install.sh` links them into `~/.claude-accounts` and the skill into `~/.claude/skills/`.** Run it from the main checkout, never from a task worktree.

## Install

1. From the **main checkout**: `bash tools/claude-accounts/install.sh --dry-run`. It writes nothing and prints the full plan and the resolved source dir.
2. Read the diffs and every `refuse` or `unexpected:` line.
3. Run `bash tools/claude-accounts/install.sh --force`. The first install needs `--force` on a home whose `HANDOFF.md` or `SKILL.md` differs from the repo copy (they do after this iteration's doc edits); without it the item is refused and nothing changes. `--force` moves each replaced original to `~/.claude-accounts/.install-backup/` first.

The install deletes leftovers (`<managed name>.bak-*`, `.new`, `.orig` in `~/.claude-accounts` and `bin/`, and a `__pycache__` holding only `*.pyc`) and does not back them up, with or without `--force`; `--dry-run --force` lists each as `delete:`. (A differing skill folder moved by `--force` goes to `.install-backup/` whole, leftovers inside it included.)

**Deploy plan (the PO runs it; the squad never does):**

1. The PO asks the Manager to merge the integration branch into `main`.
2. In the main checkout: `bash tools/claude-accounts/install.sh --dry-run`. Read the plan: nothing marked `refuse` and no `unexpected:` line you care about.
3. `bash tools/claude-accounts/install.sh --force` (needed once: `HANDOFF.md` and `SKILL.md` differ from the repo copy). Safe while the statusline, popup or a running `cautoswitch` use the files (atomic swaps).
4. Check: see "Post-install check" below, and open a new shell for `command -v c1`.
5. Later, the PO's choice: retire `~/.claude-accounts/.git`.
6. **Rollback:** `bash tools/claude-accounts/install.sh --unlink` (real copies again), or restore from `~/.claude-accounts.rar` / the live `.git`. Never `git checkout` another branch in the main checkout while linked (see Hazards).

The install never edits `.bashrc`, the herdr config or the statusline. It swaps links atomically, so the statusline, the popup and a running `cautoswitch` keep working while it runs.

| Flag | Does |
|---|---|
| `--dry-run` | Print the plan, change nothing. Exit 1 when a real run would refuse |
| `--force` | Replace a differing live file or skill folder, after moving it to `.install-backup/` |
| `--allow-worktree` | Run from a linked worktree (tests only; the worktree is deleted at squad close) |
| `--unlink` | Rollback: turn every link made here back into a regular copy; state untouched |

## Post-install check (PO)

- `ls -l ~/.claude-accounts ~/.claude-accounts/bin ~/.claude/skills/claude-accounts`: links point into this checkout.
- `cdefault` prints the default; `ACCT_NO_WS_DEFAULT=1 c1 --version` runs.
- `echo x | ~/.claude-accounts/usage-popup.sh` prints usage; in herdr, `prefix+u` opens the popup.
- A new shell: `command -v c1` finds `~/.claude-accounts/bin/c1`.
- After the next status-line refresh, `usage-1` or `usage-2` in `~/.claude-accounts` has a new mtime.

## What stays in `~/.claude-accounts`

State, never in the repo (`.gitignore` lists it): `default`, `workspace-default/`, `usage-*`, `cswitch.log`, `.install-backup/`, and the old `.git` (the install never touches it; retiring it is the PO's step).

Three hooks keep working because the paths do not change:

- **`.bashrc`**: PATH holds `~/.claude-accounts/bin`.
- **herdr popup**: runs `~/.claude-accounts/usage-popup.sh`.
- **statusline**: calls `~/.claude-accounts/record-usage.sh` (must be executable: `[ -x ~/.claude-accounts/record-usage.sh ]`).

## Layout

| Path | What |
|---|---|
| `bin/` | `c`, `c1`, `c2`, `c3`, `cdefault`, `cswitch`, `cautoswitch` |
| `lib.sh` | shared functions |
| `usage-popup.sh`, `record-usage.sh` | herdr usage popup and the statusline cache writer |
| `HANDOFF.md` | setup notes, linked to `~/.claude-accounts/HANDOFF.md` |
| `skill/` | the `claude-accounts` skill, linked as a directory |
| `install.sh` | the installer |

Windows is `windows/`: the PowerShell 7 port of the per-workspace default (`claude-accounts.ps1`) and `CHECKLIST.md`, the PO's Windows check; it is not installed by `install.sh`.

## Tests

`python3 tests/run_suite.py` (see the repo `CLAUDE.md`), or only the files `tests/test_ca_*.py`. Every test uses a temp HOME and stub `herdr`, `claude` and `pgrep`; the real home and the network are never touched.

## Hazards

- **The link target is a working tree.** Checking out a branch without `tools/claude-accounts/` in the main checkout breaks `c1`, `cdefault` and the statusline cache. Rollback: `install.sh --unlink`.
- **`link_shared` (`lib.sh`) runs `rm -rf`** on a real file or directory in `~/.claude-2|3` that is in `SHARED`; only an existing symlink is skipped.
- **`usage-popup.sh` shows the global default**, not the workspace default.
