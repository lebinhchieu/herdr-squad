Status: ready-for-agent
Type: task
Task ID: 10
Touches: `templates/squad/process/files.md` (FILE-* rules), `bin/squad-path-guard` (new), `hooks/hooks.json` (PreToolUse entry), `bin/squad-close` (untracked-root report), `tests/test_squad_path_guard.py` (new), `tests/test_hooks_json.py`, `tests/test_squad_close.py`
Does not touch: `agents/*`, `bin/squad-spawn`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_path_guard test_hooks_json test_squad_close test_windows_safe`
Blocked by: 03

# 10: Drafts never land untracked in the project root

**Done when a non-Developer role cannot write a file in the project root outside the squad folder, the rules say where drafts go, and `squad-close` reports untracked root files.**

## Why
Review finding 3: untracked tickets or specs in the project root appeared in 10 of 20 iterations. They came back 4 times after the 2026-10-17 rule. The one clean iteration (win-compat it.4) drafted in `tasks/`.

## What
- **Rules:**
  - Tech Lead, BA and Team Lead draft tickets, specs and ADR text in `$SCOPE_DIR/tasks/`.
  - The first Developer task of the scope commits them to the paths `project.md` names.
  - A later draft rides the next Developer task.
- **`squad-path-guard`** (PreToolUse on `Write|Edit|MultiEdit|NotebookEdit`):
  - when `SQUAD_ROLE` is set and is not `dev`, and the target is inside the project root but outside `.claude/squads/`, it blocks with: "draft it in $SCOPE_DIR/tasks/; a Developer task commits it [FILE-n]";
  - Developers are not limited by it;
  - with no `SQUAD_ROLE` (the PO's own session) it does nothing.
- **`squad-close --scope`:** prints untracked files in the project root outside `.claude/squads/` (`git status --porcelain --untracked-files=all`). It warns, never refuses. The Manager's pre-merge check rule cites the same command.

## Technical AC
1. The guard decision table is tested: each role × path inside the squad folder / project root / outside the project / a worktree path; with no `SQUAD_ROLE`; symlinked and `..` paths are resolved before the check.
2. The guard exits fast: no git call, no network, at most one `realpath`.
3. `hooks.json` stays valid, and its test covers the new entry.
4. `squad-close` on a fixture repo with an untracked `.scratch/x/issues/01.md` lists it, and the close proceeds.
