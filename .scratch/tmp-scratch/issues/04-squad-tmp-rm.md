# 04 squad-tmp rm frees space mid-task

Status: done
Spec: `.scratch/tmp-scratch/spec.md`
Blocked by: 01
Aim: An agent can delete its own big scratch without a prompt
Estimate: 30m
Depends on: 01

## Problem
A clone or worktree in scratch sometimes has to go before retire; `rm` on it prompts Chieu.

## Change
- `squad-tmp rm <path>...`: deletes each path only if it sits strictly inside the caller's `$SQUAD_TMP` (resolved, symlinks not followed out); the scratch dir itself, a path outside it or no `$SQUAD_TMP` is refused with exit 2.
- All role settings templates allow `Bash(squad-tmp:*)`.

## AC
- AC1: `squad-tmp rm "$SQUAD_TMP/x"` deletes `x` without a permission prompt.
- AC2: `squad-tmp rm /tmp/other`, `rm "$SQUAD_TMP"` and a symlink in scratch pointing out of it delete nothing outside scratch.

## Comments
- Decided by Chieu 2026-11-25 ("write all 5 tickets & implement"): this tool passes the built-in rm check on purpose; it is safe because it checks the path itself.
