# 04 Closing task: commit Phase A files and follow-ups

Status: done
Blocked by: none (01 ad3b4c7, 02 ff67d2d, 05 d6bdeb9, 06 8f1f2d1 passed both QAs; 03 is wontfix)

Output: one branch that merges the passed task branches (01, 02, 05, 06) and commits the untracked `.scratch/audit-token/` files, including `trial-protocol.md`. This is the scope's integration task: `--tz`, nothing skipped, and the scope's last task is the promotion commit of `promote.md` after the PO's pick.

## Technical AC
- The "Closing task AC" in `spec.md` (commit spec and issues, clean `git status --short .scratch/audit-token`, promote rows the PO's pick confirmed, AT-01 follow-ups, each ticket's `Status:` and `## Comments` current).
- Merge of the passed task branches runs `python3 tests/run_suite.py --receipt <dir> --tz`; nothing skipped.
- AT-02 QAW nit (droppable): `haiku.md` says Haiku runs cost $0.0011-0.0023, but the `runs/*.json` minimum is $0.000995 (evidence/AT-02/qa-w.md, last section); fix the range. The AT-02 passed sha is ff67d2d.
- AT-05 QAW follow-up (droppable): two squads in one repo that share a bare agent name are not separated by the cwd rule (evidence/AT-05/qa-w.md, Round 2). Agent names carry the squad prefix, so only a hand-made clash hits it; leave it unless cheap.
- AT-05 follow-up (droppable): the table's `subagents` cell shows `0k` below 0.5k output tokens; show the exact number under 1k (evidence/AT-05/qa-b.md).
- AT-06 QAW nit (droppable): its R7 changed-files list omits `tests/test_squad_start.py`; no code change.
- Merge order: 01, 02 (docs/scripts), then 05 (`bin/squad-usage`), 06 (`bin/squad-spawn`, `squad-respawn`, tests); disjoint files, so no conflict is expected.
- The Manager's ruling (resume caveat) is in `trial-protocol.md` (Overrides); it is committed with the rest of `.scratch/audit-token/`.
- `scripts/audit.py` from AT-01 is on the branch and runs read-only, because the trial reads its per-scope and per-role tables.
- remove-board also edits `agents/`, `bin/`, `skills/`, `templates/`: if it merged first, rebase on it and resolve conflicts; a conflict in `bin/squad-usage`, `squad-spawn` or `squad-respawn` goes to the Tech Lead.

## Comments
