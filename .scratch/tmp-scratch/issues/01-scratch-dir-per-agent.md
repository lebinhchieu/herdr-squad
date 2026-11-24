# 01 Each agent gets its own scratch dir

Status: done
Spec: `.scratch/tmp-scratch/spec.md`
Blocked by: none
Aim: mktemp in an agent lands in its own scratch dir
Estimate: 1h
Depends on: none

## Problem
Agents make scratch anywhere under `/tmp` and must clean it themselves with `rm`, which trips Claude Code's dangerous-rm check.

## Change
- New `bin/squad-tmp` (Python): `root`, `path <agent>`, `make <agent>` (0700, prints the path). Root `/tmp/squad-<uid>`, `SQUAD_TMP_ROOT` overrides it.
- `squad-spawn` runs `squad-tmp make <name>` and puts `TMPDIR`, `SQUAD_TMP` (the dir) and `CLAUDE_CODE_TMPDIR` (the caller's, else its `TMPDIR`, else `/tmp`) into the pane env. A failure only warns; the agent then runs on plain `/tmp`.

## AC
- AC1: a spawned agent's pane env has `TMPDIR` and `SQUAD_TMP` set to `/tmp/squad-<uid>/<name>`, which exists with mode 0700.
- AC2: `CLAUDE_CODE_TMPDIR` is set, so Claude Code's task dir stays at `/tmp/claude-<uid>` (herdr-bg unchanged).

## Comments
- 2026-11-25, Claude: not covered: the `/squads` resume command for a Manager (`bin/squadcommands.py` `_resume_text`) sets no `TMPDIR`, so a hand-resumed Manager uses plain `/tmp` until its next respawn.
