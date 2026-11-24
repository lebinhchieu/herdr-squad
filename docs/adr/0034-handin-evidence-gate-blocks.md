# 0034: The HANDIN evidence gate blocks

Status: accepted. An exception to LC-27 ("gates warn, never block"); the rest of LC-27 is unchanged.

## Context
Of 119 reviewer returns across all squads (to 2026-11-24), 13 failed only because `squad-evidence check` exited non-zero: orphan images, a missing `evidence.md`, a file changed outside the evidence folder. The code was fine. REV-22 already told the Developer to run the check before `HANDIN`, but nothing enforced it when a QA was on the team, so a reviewer found it and the task took a full return trip. Twice two reviewers returned the same evidence finding.

## Decision
- `bin/squad-handin-gate`, a PreToolUse hook on SendMessage, runs `squad-evidence check` on the ticket's folder before any `HANDIN` leaves, on every team. An `evidence sha` hand-in is checked with `--base` set to the task's last code hand-in sha.
- On a failing check it denies the message and its reason tells the Developer to fix, commit and hand in the new sha, or to send `BLOCKED <task>: evidence check` if the check is wrong.
- It never blocks when the check cannot run (no scope, no ticket file, worktree HEAD not the handed-in sha, any tooling error), so a tooling fault never wedges a Developer.
- New rule EVID-0, for reviewers: no `FAIL` for a failing evidence check. It is not in the Developer's start-up rules, because the hook's refusal message carries the instruction.
- Rejected: keep it a warning (that is the status quo that made the returns); make reviewers skip the check by rule only (the Developer would still not run it).

## Consequences
- The PostToolUse W9 path (no QA on the team) is unchanged, but now only sees hand-ins that passed the gate.
- Tickets kept outside `.scratch/<scope>/issues/` (the `tasks/<id>/` layout) are not found, so the gate lets those through.
- The hook runs from the installed plugin, not the scope's pinned runtime, so running scopes get it at their next session start.
- Plugin 0.10.12; changelog v30.
