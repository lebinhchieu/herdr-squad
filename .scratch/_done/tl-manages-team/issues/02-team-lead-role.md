# T2 · agents/team-lead.md for M and L
Status: ready-for-agent
Type: task
Blocked by: none
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches (and no others)
`agents/team-lead.md`, `tests/test_team_lead_role.py` (new).

## Do
Rewrite the role file; keep `model: sonnet`, `effort: medium`, the Start-of-session block and Notes block.
- Exists in **M and L**; **if you join because a scope moved up from S, take the plan file over from the Tech Lead's `## Handover`** (same format). Moving M to L changes nothing for you.
- **Owns:** plan, order, assignment; spawn and retire **Developers only** (`squad-spawn dev <squad>-dev-<scope>-<n> --scope <scope> --repo <repo> [--base <ref>] --title "<id> words" --prompt "<briefing>"`, name at most 32 characters; the briefing names scope, folder, files to read, peers by name; `--base` only the ref the Manager checked and named in the iteration file); `squad-retire` a Developer after its task is done; health checks (`herdr agent list`, `read`, `ASK <name>: STATUS?` only after 10 idle minutes); routing (who owns X); 3-returns triage; roster rows of the Developers it spawned (small script that re-reads the file just before writing; never the other rows); the pod's single contact (process.md → Messages).
- **Developer cap:** its share from the Manager's briefing (a lone scope: the whole cap, `process.md` → Defaults); queue the rest. **Quote the share rule in the role file** (B15): when your share is used up, the next task waits as `ready`; a finished scope's share goes to the scopes still running at the next briefing or respawn. Say the cap is a rule, not a lock.
- **You never** spawn or retire any role but `dev` (a sentence the test greps), relay a blocked pane or a permission, or message the Manager for a routine matter.
- **Sends the Manager, each as one line pointing at a file:** an "Always goes to PO" item; a size-change signal; a dispute outside plan and assignment that two rounds did not settle (the parties go to the Manager themselves; you are not a relay); 3 returns on one task (one budget line); and `iterations/<n>.summary.md` at iteration end (tasks done with evidence links, returns per task, friction, open items, at most 40 lines; from the first goal that runs this, one line naming the residual risk "the cap is a rule, not a lock").
- **Disputes:** settle plan, order and assignment ones; write the ruling where the plan lives; start it with `FINAL:`.
- **State lives in files** (plan file, roster, notes), not memory: you carry every HANDIN/PASS/FAIL copy and will cross 120k. On respawn read notes, plan, roster and `herdr agent list`.
- Remove the old "ASK manager: spawn dev" and "The Manager spawns one Developer per ready task" text.

## Technical AC
AC-3.1, AC-3.5, AC-2 (Team Lead side of every moved duty). `tests/test_team_lead_role.py` greps the sentences above (dev-only, `FINAL:`, summary path, no relay, respawn reads) and runs under `test_instructions.py` unchanged.

## Business AC
B5, B7, B10, B17, B18, B19, B21.
