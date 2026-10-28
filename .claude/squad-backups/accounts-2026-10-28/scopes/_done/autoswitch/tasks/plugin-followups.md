# Plugin follow-ups from autoswitch it.1 (drafts, not filed)

Source: iterations/1.coach.md (full evidence). Squad is composed (rules from plugin pin), so rule proposals are plugin-level; none applied here.

## Rule proposals (Coach 1-3)
1. DEV-SHAPE: stub/fixture of another tool's output carries one real sample in the ticket before HANDIN (3 of 3 tasks returned once on shapes/wording).
2. QA-DOC: doc-only ticket = QA whitebox alone (lowers QA bar: PO decides).
3. QAB-READY: Manager has QA blackbox live and exports the base sha to /tmp/qab-<task> before the Dev's HANDIN.

## Plugin proposals (Coach)
1. usage-events.jsonl lacks ctx, limit, cost_rule fields.
2. squad-usage shows only the current session per agent (undercounts respawned roles).
3. Stop-hook text names a Team Lead in a size M scope that has none.
4. QA blackbox settings deny .worktrees reads and allow no run of a build: allow the task's /tmp/qab-* export or document the export step.

## Retro extras
- cautoswitch finds panes from live /proc environ, so it cannot be isolated by PATH/HOME: a stub-herdr seam would let QA-b run it.
- squad-evidence check on a scope-folder evidence path fails outside the repo (rev unknown).
