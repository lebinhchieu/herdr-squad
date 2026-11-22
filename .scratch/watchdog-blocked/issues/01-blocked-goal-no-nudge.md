# 01 Blocked goals get no idle nudge
Status: ready-for-agent
Duties: plan-owner=team-lead, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Files: bin/squad-watchdog (goal idle nudge, docstring "Goals:"), tests/test_squad_watchdog.py, docs/adr/0028-watchdog-follows-goals-file.md (Decision line 2); this ticket and tasks/02.md committed to .scratch/watchdog-blocked/issues/01-blocked-goal-no-nudge.md and 02-watchdog-starts-with-team.md
Depends: none. Base: main at 8d74fcb. Plan: `$SCOPE_DIR/iterations/1.md`.
Evidence: .scratch/watchdog-blocked/issues/01-blocked-goal-no-nudge/evidence.md

## What and why
Chieu saw the watchdog nudge the Manager at 5 min, the Manager set the goal `blocked` (waiting on Chieu's inbox item), and at 15 min it nudged again. A goal that waits on Chieu has nothing the squad can do; the nudge is noise. This reverses ADR 0028 "a goal not `done`" and `.scratch/watchdog-should/issues/03-watchdog-follows-goals.md` AC4: the idle test now counts only `in progress` goals (any unknown status word still counts as `in progress`).

## Business AC
- AC1 Home with goals.md, every not-`done` goal `blocked`, nobody working: no 5 min and no 15 min nudge to the Manager or Team Lead. `watchdog.log` has one line saying the open goals are all blocked (once per spell, not every pass). The watchdog keeps running (no `all goals done; watchdog stops`).
- AC2 Mixed `in progress` and `blocked` goals, nobody working: the 5 and 15 min nudges fire and name only the `in progress` goals; no blocked goal is listed in the nudge.
- AC3 A goal goes `in progress` -> `blocked` mid-spell (after the 5 min nudge): no 15 min nudge while all open goals stay blocked. A goal goes `blocked` -> `in progress`: a fresh idle spell starts then, so the next nudge comes 5 min later (not at once, not never).
- AC4 Unchanged: the 10 min blocked-pane wake, sleep-when-idle (a team idle with only blocked goals still lets the PC sleep when sleep is on), all-done stop, the no-goals-file ticket check, the Team Lead routing.

## Technical AC
- AC5 Tests in `tests/test_squad_watchdog.py` (extend, no new file) for AC1, AC2, AC3 via `tick --now`; existing tests that pin a blocked goal in the nudge are updated, none skipped; the file passes.
- AC6 Docstring "Goals:" paragraph and ADR 0028 Decision updated to say blocked goals get no nudge (one line each; the ADR keeps its number, add "amended by watchdog-blocked 01").
- AC7 SQ-10: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and every hit of `grep -rl "squad-watchdog" tests/`; quote results in `## Behaviour`.
- AC8 Live check (QA blackbox): `squad-watchdog tick --now` on a scratch scope home with goals.md (all blocked, then mixed, then back to in progress); `watchdog.log` and the stub herdr prompt log show AC1-AC3.

## Evidence
`evidence.md` next to the committed ticket; QA cells assembled (EVID-2d) before the Developer is retired.
