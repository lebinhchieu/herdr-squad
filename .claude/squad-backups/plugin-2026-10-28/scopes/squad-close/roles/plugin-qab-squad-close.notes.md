# Notes plugin-qab-squad-close (QA blackbox, scope squad-close)

## Now
- 01 PASS (commit 3ffabe7) and 02 PASS (commit 6ebcfbd) sent to plugin-dev-squad-close-1. Nothing open.
- Evidence: evidence/01/qa-b.md, evidence/02/qa-b.md (in $SCOPE_DIR).

## Open threads
- None. Non-blocking notes already sent: scope/goal close lists the kept pin twice ("still runs from it" + "(running)"); AC4 said CLOSE-5 unchanged but text got "retires every agent, the Managers last".
- Not tested: goal holding scopes with live agents (goal fixture layout unknown); AC6 header comment and AC7 tests (whitebox).

## Decisions that bind later work
- None.

## Pointers
- Scratch squad recipe for squad-close: temp git repo; copy a squad into `.claude/squads/<name>/`; it needs `process.md` (empty file ok) or "no squad folder"; fill the last iteration's Retro (Went well/Friction/Process changes) or use --force; stub `herdr` on PATH (`agent get <n>` prints JSON with pane_id to look live; log calls); scope pin = `plugin: <ver> <sha>` line in scope.md/goal.md, runtime dir `_runtime/<ver>-<sha12>`; set SQUAD_PLUGIN_DIR to the Dev worktree. Compare against main `bin/squad-close`.
- Scratch dirs already deleted; no processes left.
