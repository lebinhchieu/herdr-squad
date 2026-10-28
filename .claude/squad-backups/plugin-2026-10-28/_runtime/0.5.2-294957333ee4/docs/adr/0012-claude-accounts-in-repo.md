# The account launchers live in this repo

Status: accepted (claude-accounts)

**Decision:** the PO's launchers (`c1 c2 c3 c cdefault cswitch cautoswitch`, `lib.sh`, `usage-popup.sh`, `record-usage.sh`, the `claude-accounts` skill) are maintained in `tools/claude-accounts/`. The plugin install copies them but they stay inert: nothing under `bin/`, `skills/`, `hooks/` or `agents/` points at them. `install.sh`, run by the PO after the merge, symlinks each script from `~/.claude-accounts` to the main checkout and the skill folder to `~/.claude/skills/claude-accounts`. State files stay real files in `~/.claude-accounts`. The squad never edits the PO's live home.

**Why:** the launchers were built for working with squads and lived only in an unversioned home folder, with a `.git` of their own, leftovers (`*.bak-*`, `*.new`, `*.orig`, `__pycache__`) and no tests.

**Consequences:**
- The files were imported fresh, without the old `.git`, which is retired at cutover.
- Install: `~/.claude-accounts` and `bin/` stay real directories; swaps are atomic (`ln -s` temp, `mv -T`); a preflight builds the whole plan and one refusal changes nothing. It refuses a linked-worktree source and an empty `HOME` (`--allow-worktree` for tests). Flags: `--dry-run` (rc 1 when a real run would refuse), `--force`, `--unlink` (rollback to real copies). The first install needs `--force`: the live `HANDOFF.md` and skill folder differ from the repo; `--force` moves them to `~/.claude-accounts/.install-backup/`. Leftovers are deleted, not backed up; any other unknown file is printed as `unexpected:` and kept.
- Hazard: the links point into the main checkout's working tree. Checking out a branch without `tools/claude-accounts/` there breaks `c1`, `cdefault` and the statusline cache; rollback is `install.sh --unlink`.
- Tests (`tests/test_ca_*.py`, harness `tests/ca_stubs.py`) use a temp HOME with stub `herdr`, `claude`, `pgrep`, and must pass in a plain `git clone`, not only a linked worktree; suite receipts for a merge are taken from a clone of that sha. `install.sh` needs git 2.31 or later.
- Known gaps: the `FAILED: claude did not exit` line, the live branch of `cautoswitch.usage()`, token refresh success and the popup `resets -` 5h branch are untested; the popup shows the Global default, not the Workspace default; `link_shared` runs `rm -rf` on a real file in `~/.claude-2|3`.

**Alternative rejected:** keep `~/.claude-accounts` as its own git repo (outside the project's review, tests and the squad's branches).
