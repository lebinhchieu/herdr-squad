# 07 Token Coach role

Status: resolved
Blocked by: 01, 06

Add `agents/token-coach.md` (sonnet/medium) and a retro step in `process.md` and `manager.md`: spawn the Coach, which reads the squad-usage table and `usage-events.jsonl` and writes a ranked `iterations/<n>.coach.md`. The Manager decides the top 3, the rest go to backlog, and accepted changes are logged in `process-log.md`.

## AC
- The Coach never edits files other than `coach.md`.
- Each proposal cites an evidence row.

## Comments

- Added `agents/token-coach.md` (sonnet/medium): reads `squad-usage` + `usage-events.jsonl` + earlier coach files, never raw transcripts; writes `iterations/<n>.coach.md` with proposals ranked by saving, each with evidence row, exact `process.md` change and saving; may only propose `process.md` changes.
- `templates/squad/process.md` Retro step now spawns the Coach and describes the accept-top-3 / backlog / `process-log.md` flow. `agents/manager.md` gets the matching Retro bullet and `token-coach` in its roles list. `bin/squad-spawn` accepts the `token-coach` role.
- "Never edits files other than coach.md" is enforced in two layers: the role text, and `templates/squad/settings/token-coach.json` (allow write only on `iterations/*.coach.md`; deny writes to other squad `*.md` and `settings/**`; deny reading `~/.claude*/projects/**`). Not enforced: arbitrary Bash writes or paths outside the squad folder (path rules are project-relative; auto mode still classifies them).
- Also: `Bash(squad-respawn:*)` added to the six role settings templates, `Bash(squad-usage:*)` to the Manager's, so the new commands do not prompt.
- Test: docs and settings only; `tests/test_squad_spawn.py` now covers the `token-coach` defaults and that every role's settings JSON parses. Full suite: `python3 -B -m unittest discover -s tests` → 39 tests OK.
- Unverified: the `Write(/.claude/squads/*/iterations/*.coach.md)` pattern syntax against a live Claude Code permission check.
