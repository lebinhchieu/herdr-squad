# 01 Team Lead nudge asks it to send the Manager the goal status
Status: building (plugin-dev-tl-wake-status-1)
Duties: plan-owner=team-lead, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Files: bin/squad-watchdog (team_lead_nudge_text, module docstring "Who is told"), tests/test_squad_watchdog.py, docs/adr/0028-watchdog-follows-goals-file.md (one Consequences line), .claude-plugin/plugin.json (version bump); this ticket file committed to .scratch/tl-wake-status/issues/01-team-lead-sends-goal-status.md
Depends: -. Plan: `$SCOPE_DIR/iterations/1.md`; brief `$SCOPE_DIR/scope.md`.
Evidence: .scratch/tl-wake-status/issues/01-team-lead-sends-goal-status/evidence.md

## What and why
After ce3ff02 a scope watchdog sends its idle nudges (5 and 15 min) to the Team Lead. With rows in `goals.md`, an idle spell lasts while a goal is not `done`. `team_lead_nudge_text` names only open tickets and `blocked` goals; an `in progress` goal is not named, and nothing asks the Team Lead to report it. `goals.md` is Manager-only (START-19b), and the Manager is no longer nudged while the Team Lead lives. So once every ticket has passed, the goal stays `in progress`, the Team Lead reads "Waiting: none open", the Manager is never told, and the watchdog never stops.

Chieu's decision (E1): the Team Lead messages the Manager, and the Manager writes `goals.md`. Routing stays as ce3ff02 built it (Team Lead first, Manager as fallback); the Team Lead never writes `goals.md`.

## Business AC
- AC1 Scope home, live Team Lead, `goals.md` with an `in progress` goal, no open ticket: the 5- and 15-minute nudges go to the Team Lead and name each open goal (id, title, status), and tell it to send the Manager one line (MSG-6): the goal is done when all its tickets passed, else blocked with the reason, so the Manager updates `goals.md`. The Team Lead is never told to edit `goals.md`.
- AC2 Same, with open tickets too: the nudge still lists the waiting tickets as today and names the open goals; the goal-status line is asked only when no ticket is open.
- AC3 A `blocked` goal is still named as the Manager's, as today.
- AC4 Unchanged: Manager wording and fallback (Team Lead absent or blocked), goal home nudges, blocked-pane wake, bg-shell and sleep behaviour, `goals.md` all `done` -> `all goals done; watchdog stops`.

## Technical AC
- AC5 One test per AC1 and AC2 in `tests/test_squad_watchdog.py` (recording `send`, `--herdr-json` style fixture as the ce3ff02 tests do); existing rows pass unchanged.
- AC6 The module docstring "Who is told" paragraph says what the Team Lead nudge asks; ADR 0028 gets one Consequences line: the Team Lead reports goal status to the Manager, who alone writes `goals.md`.
- AC7 SQ-10: the diff edits `bin/` printed text: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result in `## Behaviour`; plus `grep -rl "squad-watchdog\|team_lead_nudge\|nudge" tests/` hits.
- AC8 SQ-5: plugin version bump in `.claude-plugin/plugin.json` from 0.10.2 (`grep -rn '0\.10\.2' .claude-plugin/` shows no hit after), with a `skills/squad-process-update/changelog.md` row if that file lists versions.
- AC9 Live check (QA blackbox): `squad-watchdog tick --home <scratch scope> --herdr-json <fixture> --now ...` on a scratch scope home with a Team Lead in the fixture, a `goals.md` row `in progress` and all tickets passed; `watchdog.log` shows the nudge to the Team Lead with the goal-status line.

## Promotion
`promote.md`: ADR 0028 line rides this ticket (AC6); nothing else to promote.

## Evidence
`evidence.md` next to the committed ticket (Evidence: line).
