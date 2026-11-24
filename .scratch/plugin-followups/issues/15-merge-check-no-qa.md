# 15 Merge check passes a team with no QA; version bump

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/08-merge-check-qa-none.md`)
Blocked by: 13, 14
Aim: Merge check uses the evidence check when a scope has no QA
Estimate: 2h
Depends on: 13, 14

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/15.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Also run `test_squadboard_tasks`, `test_squad_watchdog`, `test_squadplan` (they call `checkers`). Merge 13's and 14's branches first. You alone edit `changelog.md`, `.claude-plugin/plugin.json` and the README row `squad-merge-check`: write `## v32` and version 0.11.1 from the `## Changelog line` of 09-14 (`git show <branch>:<evidence path>`); a missing one goes to 16.
Files: `bin/squadtask.py` (`checkers`), `bin/squadmergecheck.py`, `.claude-plugin/plugin.json`, `skills/squad-process-update/changelog.md`, README row `squad-merge-check`, `tests/test_squadtask.py`, `tests/test_squad_merge_check.py`

## Problem
`squad-merge-check` refused a passed branch (merge 2b535f5): it wanted PASSes from the retired QAs and read the rule id SQ-10 as a ticket. Root cause: `squadtask.checkers` falls back to the retired QA rows, so `slots()` is never `evidence` and the HANDIN hook never records an evidence PASS. Tasks 03, 04 and 05 passed only by a Manager override.

## Change
`squadtask.checkers(home)`: live (non-retired) QA rows win as today; else, when `scope.md` has a decided `team:` (`squadrules.parse_team` not None) with no `qa-white` or `qa-black` token, the answer is `{"qa": []}` and the slot is `evidence`; else the old fallback to retired rows. Basis: of the 34 scope folders under `scopes/_done/`, every one with a QA roster row lists `qa-white` or `qa-black` in `team:`; the 3 without QA have `team: none`. `squadmergecheck.check` skips states whose id is not `is_task_id` (from 12). Version 0.11.1 (tooling fixes, no rule change, nothing breaking), changelog `## v32`.

## AC
- AC1: scope fixture `team: tech-lead, designer` with two retired QA rows: `checkers` = `{"qa": []}` and `slots` = `["evidence"]` (base: the two retired agents). Team with `qa-white` and the same rows: unchanged. Team `none`: `{"qa": []}`.
- AC2: in that fixture the HANDIN hook path records a `pass` in slot `evidence` by `hook` when the evidence check passes (base: not recorded).
- AC3: `squad-merge-check` with an `evidence=PASS` state prints `[evidence=PASS]` and `VERDICT: ok`; a task row `SQ-10` on the same sha is not printed as a ticket (base: refuses "sha not passed by every checker").
- AC4: `test_squadboard_tasks`, `test_squad_watchdog` and `test_squadplan` are green.
- AC5: `grep -c '"version": "0.11.1"' .claude-plugin/plugin.json` is 1; the changelog's top heading is `## v32`; `python3 bin/squad-process lint` exits 0 (base: `0.11.0` once in plugin.json, twice in the changelog; `0.11.1` none).

## Comments
