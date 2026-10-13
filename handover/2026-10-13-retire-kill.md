# Bug: squad-retire killed (exit 137) and took other panes with it

**From:** ecapture-mgr-engine-icons (squad Manager, project ~/workspace/wpw, squad `ecapture`, scope `engine-icons`), 2026-10-13.

## What happened
- Manager ran, in one Bash call: `squad-retire ecapture-dev-engine-icons-1 2>&1 | tail -3; <sed/python edits of roster.md and iterations/1.md>`.
- The Bash call ended with **exit 137** (SIGKILL); none of the following edits ran.
- Afterwards `herdr agent list` showed **no ecapture agents at all**: the dev (expected), but also the Manager (caller) and the Tech Lead `ecapture-tech-engine-icons` disappeared from the list. The Manager session lost `SCOPE_DIR`/`SQUAD_*` env vars (empty on the next call).
- `ListAgents` (Claude Code peer list) still shows the Tech Lead as a live `bg` session, and the Manager is reachable by name — so the herdr panes/names were dropped while the processes (or replacements) kept running.
- All panes were in herdr workspace `wG`: Manager `wG:p2` (tab t2), TL `wG:p3` (t3), dev `wG:p4` (t4).

## Expected
squad-retire closes only the dev's tab `wG:t4`; caller and other agents untouched.

## Suspects to check
- Tab/pane close by index or workspace instead of by id; or killing a process group that includes the caller.
- The caller's own process getting signalled (137 on the caller's Bash).
- Env loss in the caller after the kill.

## Evidence
- ~/workspace/wpw/.claude/squads/ecapture/scopes/engine-icons/messages.jsonl, roster.md, iterations/1.md (log line "squad-retire of the dev was killed").
- Worktree still present: ~/workspace/wpw/.worktrees/ecapture/engine-icons/ecapture-dev-engine-icons-1.

Investigate, write a failing test/repro, fix. Don't touch the wpw project files.
