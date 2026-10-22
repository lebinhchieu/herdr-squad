# 01 Designer role file, settings, squad-spawn

Status: ready-for-agent
Blocked by: none
Task ID: UXD-01

**`squad-spawn designer` starts a sonnet/high UI/UX Designer with its own settings, and only in a scope whose `scope.md` says `design: yes`.** Spec: `.scratch/ui-ux-design-role/spec.md` (decisions 1, 2, 5, 6, 7). Precedent: `.scratch/token-coach/issues/07-token-coach-role.md`.

## Files (only these)

- `agents/designer.md` (new)
- `templates/squad/settings/designer.json` (new)
- `bin/squad-spawn`
- `tests/test_squad_spawn.py`
- `tests/test_templates.py`

## What to build

- **`agents/designer.md`**, frontmatter `model: sonnet`, `effort: high`, a `description:` in the same shape as the other roles ("... Not for use as a subagent."). Follow `agents/tech-lead.md` for the start-of-session block: `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`; read `process.md`, `project.md`, `$SCOPE_DIR/scope.md`, `roster.md`, own notes; in a goal also `$GOAL_DIR/goal.md` and `shared/`; cost-rule respawn line. Then:
  - Reads the Manager's briefing, the UI tasks and their AC, and the existing UI conventions `project.md` lists; reuses existing components, palette and patterns before inventing.
  - Writes `$SCOPE_DIR/ui-design/<task>.md` per UI task: `Status: draft|final`, screens, **every state** (empty, loading, error, edge, long or missing data), flows between screens, copy, and what to reuse. Optional `ui-design/<task>.html`: one self-contained file, no network, opens from disk.
  - When final, sends `DECISION <task>: design final, ui-design/<task>.md` to the Tech Lead and the task's Developer.
  - Business doubt: `ASK` the BA (M, L) or the Tech Lead (S); never writes `escalations.md` itself. Feasibility doubt: `ASK` the Tech Lead.
  - **Never:** edits project code, `scope.md`, `process.md`, tickets, or another role's files; reviews the built UI (no post-build check is part of this role).
- **`designer.json`:** copy `templates/squad/settings/token-coach.json` and adapt: allow `Write`/`Edit` on `/.claude/squads/*/scopes/*/ui-design/**`; keep the three `*.md` level denies and `settings/**` denies; keep the git and Jira denies of the other roles; add `Bash(squad-respawn:*)`; no `Read` denies (it must read the existing UI).
- **`bin/squad-spawn`:** add `designer` to the role list (usage line and `case`). After the scope folder is resolved, for `designer` in a per-scope squad: read `$scope_dir/scope.md`; if no line matches `^design:[[:space:]]*yes[[:space:]]*$` (case-insensitive on `yes`), print `scope <s> has no 'design: yes' in scope.md; only the PO turns the designer on` to stderr and exit 1. Applies with `--dry-run` too. Flat squads (no `scopes/` folder) and other roles: unchanged.

## AC

1. `squad-spawn designer x --scope s --dry-run` in a per-scope squad whose `scope.md` has `design: yes` exits 0 and the printed command has `--agent squad:designer`, `--model sonnet`, `--effort high`, `--settings` pointing at `designer.json`.
2. The same with `design: no`, no `design:` line, and no `scope.md` exits 1 with the message above and starts nothing (no herdr call in a non-dry run either).
3. All other roles spawn exactly as before; `TABLE` in `tests/test_squad_spawn.py` has `"designer": ("sonnet", "high")`; `ROLES` in `tests/test_templates.py` has `designer`.
4. A test in `tests/test_templates.py` shows `designer.json` parses, allows `Write` only on `ui-design/**` (plus its notes if you add them), and denies `Write` at the three squad `*.md` levels and on `settings/**`, like the Token Coach test.
5. `designer.md` passes the checks in `tests/test_instructions.py` unchanged (reads `$SCOPE_DIR/scope.md`, `$GOAL_DIR/goal.md`, `shared/`, its notes path; no stale tokens such as `XL`).
6. Full suite green: `python3 tests/run_suite.py --receipt <evidence dir> --tz`. Save the receipt in `$SCOPE_DIR/evidence/UXD-01/`.

## Technical notes

- Do not touch `templates/squad/process.md`, `agents/manager.md`, scope template or role files other than `designer.md`: tickets 02 and 03 own them.
- Known gap to state in `dev-evidence.md`: the `Write(...)` pattern syntax is not checked against a live Claude Code permission prompt (same as the Token Coach); project code is not covered by settings.
- Hand in: `HANDIN UXD-01: branch ..., commit ...` to the Tech Lead with `dev-evidence.md` (commands run, output of AC 1 and 2).
