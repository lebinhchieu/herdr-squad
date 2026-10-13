# 05 squad-respawn

Status: resolved
Blocked by: 03

`bin/squad-respawn <agent>` closes the old herdr pane and starts the same role again, with the same name, scope and worktree, on the role's default model. The first prompt points at `roles/<agent>.notes.md`. It updates the session id in `roster.md`.

## AC
- A Dev keeps its worktree and branch.
- The new session id is in `roster.md`.

## Comments

- Added `bin/squad-respawn <agent> [--dry-run]` and `squad-usage --get NAME` (role, scope, session from `roster.md`).
- Flow: look up role/scope in the roster → rename the old herdr agent to `<name>-prev` (so the name is free) → `squad-spawn` with the same name/role/scope, no `--model` (so the role's default applies) and a first prompt pointing at `roles/<agent>.notes.md` → close the old tab **last** (safe when an agent respawns itself). `squad-spawn` writes the new session id to the roster row. If the spawn fails, the rename is undone.
- Worktree: if `.worktrees/<squad>/<name>` exists, its repo is found with `git rev-parse --git-common-dir` and passed as `--repo`; `squad-spawn` then reuses the worktree (no `worktree add`), so branch and uncommitted files stay.
- Files: `bin/squad-respawn`, `bin/squad-usage`, `tests/test_squad_respawn.py` (stub `herdr`, real temp git repo + worktree).
- Test: `python3 -B -m unittest tests.test_squad_respawn` → 3 tests OK; full suite `python3 -B -m unittest discover -s tests` → OK.
- Not verified: real `herdr agent rename` + `agent start` with a reused name; the stub only checks the call order. Notes for the old session are written by the agent before it calls respawn (the hook message says so), unlike `squad-retire` which prompts for them.
