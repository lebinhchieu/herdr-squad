# 16 Integration: merge the passed branches of 09-15

Status: ready-for-agent

Spec: none
Blocked by: 09, 10, 11, 12, 13, 14, 15
Aim: Merge all passed branches and prove every sha is in
Estimate: 1h
Depends on: 09, 10, 11, 12, 13, 14, 15

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/16.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Merge order from the "Integration relations" table: 13 on 12; 15 merges 13 and 14; then merge 09's branch (10, 11 chain) into 15's. Run the shared test files that table names, then the three whole-repo files. Keep version 0.11.1 and changelog `## v32`; a `## Changelog line` missing from 15's bullets is added here.
Files: merges only (plus a missing changelog bullet); tests `test_squad_usage`, `test_squad_respawn`, `test_session_lookup`, `test_squad_spawn`, `test_squad_manager_guard` and the union of the ticket test files

## Problem
09-14 are built on separate branches; 12, 13, 15 share `squadtask.py` and `squad-log-message`, 14 and 15 share `squadmergecheck.py`, and 09, 10, 11 share `squad-usage`. The two groups share test hits (listed in the plan), so they are related siblings and must be merged and tested together.

## AC
- AC1: every passed sha is an ancestor of HEAD: the HANDIN quotes `git merge-base --is-ancestor <sha> HEAD` and its exit code per sha, including each Developer tip and every evidence-only commit.
- AC2: targeted tests of every ticket plus the shared files above and the three whole-repo files pass on the integration sha; `python3 bin/squad-process lint` exits 0.
- AC3: `plugin.json` says 0.11.1 and the changelog top heading is `## v32`.
- AC4: no merge conflict is resolved by dropping a ticket's change; `git diff --stat` against base shows only files named in tickets 09-15.

## Comments
