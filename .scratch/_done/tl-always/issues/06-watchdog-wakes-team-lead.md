# 06 Watchdog wakes the Team Lead
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: bin/squad-watchdog, bin/squad-start (start the watchdog for a scope inside a goal; docstring lines 16-17); tests/test_squad_watchdog.py, tests/test_squad_start.py
Depends: - (group A, parallel with 01, 03, 04, 05; reads no rule file, so no wait on 02). Goal: `../iterations/1.md`; brief `../scope.md`.
Evidence: .scratch/tl-always/issues/06-watchdog-wakes-team-lead/evidence.md

## What and why
Lone scope and goal per Chieu's answer: option (a) (bound decision). Tech Lead writes the exact behaviour in Design notes. Runs parallel with 03, 04.

## Design notes (Tech Lead)
Bound (Chieu E1, option a): each scope's watchdog wakes its own Team Lead; the goal's wakes the goal Manager only on `goals.md` events. Plan decided with ADR 0028 in mind: the nudge and the wake lived on the Manager; this moves the target in a scope home.
Today (read `bin/squad-watchdog`): one watchdog per home, `--manager NAME`; `tick` sends the 5- and 15-minute idle nudge (`nudge_text`) and the 10-minute blocked-pane wake (`wake_events`) with `send(manager, ...)`; `snapshot` covers the home and, for a goal, its scopes (`scope_homes`). `squad-start` starts a watchdog only when it also starts a Manager (`if manager:`); `squad-start --in-goal` starts none, so a scope inside a goal has no watchdog of its own today.

Design:
- Home kinds: a *goal home* has `goal.md` (`home.parent.name == "goals"`); every other home is a *scope home* (lone or in a goal).
- New `--team-lead NAME` on `run`, `tick`, `ensure` (optional). Default: `<squad>-tl-<scope>` = `f"{home.parent.parent.name}-tl-{home.name}"` (the name `squad-spawn` gives it; see `default_manager`). A goal home takes none.
- Scope home: the idle nudges (5 and 15 min) and the blocked-pane wake go to the Team Lead. Fallback, logged as `-> <manager> (team lead absent|blocked)`: to the scope's Manager when the Team Lead is not in `herdr agent list` (not spawned yet, retired, gone) or its own pane is `blocked`; a blocked Team Lead pane is itself woken to the Manager, never held in silence. The Manager of an in-goal scope is the goal Manager: name `<squad>-mgr-<goal>` from `scope.md` `goal:`; of a lone scope `default_manager`. Nothing is sent into a pane that is `blocked` (held, as today).
- Nudge text for the Team Lead: its own wording (ticket wait list and agents; "message the Developer who owns it, spawn one within your cap, or `ASK` the Manager"); a `blocked` goal is the Manager's: it is named in the line, not asked of the Team Lead. The Manager's text is today's.
- Goal home: unchanged idle nudges of open goals to the goal Manager (the `goals.md` events: idle spell with an open goal; all done -> stop). The blocked-pane wake is limited to the goal home's own roster (the goal Manager); scope panes are woken by their own scope watchdogs, so none is woken twice.
- `squad-start`: start the watchdog also for `--in-goal` scopes (target = the scope folder, manager = the goal Manager, team lead derived); `--resume` of a scope inside a goal still refuses (unchanged). Docstring lines 16-17 describe both. `SQUAD_WATCHDOG=off` still starts none; one watchdog per home (heartbeat) holds.
- `ensure --home <folder> --manager <you>` (START-19b text, in 04) keeps its form; the new option is optional, nothing in the rule files changes for it.
- State file keys and `watchdog.log` formats stay; add one log line kind `route:` only when a fallback was used.

Technical AC:
- AC1 A scope home with the Team Lead in the herdr list: the 5-minute nudge goes to `<squad>-tl-<scope>`, not the Manager (test with `--herdr-json` fixture and a recording `send`).
- AC2 Same scope, Team Lead absent from the list, then present but `blocked`: the nudge goes to the Manager with a `route:` log line; Manager `blocked`: nothing is sent and the key stays free.
- AC3 Blocked-pane wake (10 min) in a scope home: a blocked Developer -> Team Lead; a blocked Team Lead -> Manager.
- AC4 Goal home: open goal + idle spell -> goal Manager at 5 and 15 minutes; no wake for a blocked scope pane (the scope's own watchdog does it); every goal `done` -> `all goals done; watchdog stops` as today.
- AC5 `squad-start "x" --in-goal G --name N` starts a watchdog for `scopes/N` (stub herdr/process as `tests/test_squad_start.py` does) with the goal Manager and no second one on a repeat; `SQUAD_WATCHDOG=off` starts none.
- AC6 Real samples (REV-4): the Team Lead name and the herdr agent-list shape used in the fixtures come from a real `herdr agent list --json` (one with a retired and one idle agent) and from this squad's roster (`plugin-tl-tl-always`); the Developer pastes the sample's source in `evidence.md`.
- AC7 All existing `tests/test_squad_watchdog.py` rows pass unchanged except the ones that pin the Manager target in a scope home (rewritten); the bg-shell and sleep tests untouched.
- AC8 SQ-10: the diff edits `bin/` and text it prints: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result.
- AC9 Targeted tests: test_squad_watchdog.py, test_squad_start.py, plus `grep -rl "squad-watchdog\|start_watchdog\|nudge" tests/` hits. Live check (QA blackbox): run `squad-watchdog tick` on a scratch scope home with a stub `herdr`, read `watchdog.log` for the target.
Compatibility (LC-12): no stored format changes; an old `watchdog.state.json` is read as before; `--manager` stays required, `--team-lead` optional. A watchdog already running keeps its old code until restarted (its heartbeat holds `ensure`); restart it by closing its `watchdog` tab after the merge. Rollback = revert the merge.

## Evidence
`evidence.md` next to the ticket (path in Evidence: line, Tech Lead).
