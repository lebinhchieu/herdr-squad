# 03: the watchdog follows the goals file: idle + open goal wakes the Manager; all goals done stops it

Duties: design notes dev; technical AC qa-white (with dev); business AC ticket; code check qa-white; behaviour check qa-black; promote.md qa-white; full suite qa-white (targeted tests by default).
Files: bin/squad-watchdog, bin/squad-start (only if `ensure` needs its start code), tests/test_squad_watchdog.py, README.md

Owner: Developer (design notes in this file). Depends on: 01 (passed e5589e2; start from its branch, reuse its worktree). Chieu's design, chat 2026-11-20, replaces E2.
Ticket file the Developer commits: `.scratch/watchdog-should/issues/03-watchdog-follows-goals.md` (copy this into it).

## Chieu's model
1. When Chieu asks the team for something, the Manager writes it down as a goal, status `in progress`.
2. When the work is done: `done`.
3. Completely stuck, needs Chieu: `blocked` + reason, plus an inbox item with what Chieu must know.
4. The watchdog watches whether the team is idle. When everyone is idle it reads the goals: any not `done` (in progress or blocked) -> it tells the Manager to check and solve. All `done` -> the watchdog stops. It runs again when Chieu starts the team again.

## The goals file
`<home>/goals.md` (home = scope folder, or goal folder for a goal Manager). One table, one row per request:

| # | Goal | Status | Reason / what Chieu must do | Updated |
|---|---|---|---|---|
| G1 | what Chieu asked, one line | in progress / done / blocked | blocked only: why, and the inbox item id | UTC date |

Only the Manager writes it ([FILE-6]); a missing file or an empty table means "no goals recorded". Status words: `in progress`, `done`, `blocked`; any other word counts as `in progress` (never silent).

## Technical AC
1. A pure reader `read_goals(home)` -> list of (id, goal, status, reason); tolerant of extra spaces and case; no file -> `None`.
2. Idle spell starts when nobody in the roster is `working` in herdr AND at least one goal is not `done`. The nudge to the Manager at 5 and again at 15 minutes of the same spell stays (existing timing); the text lists each open goal with its status and, for `blocked`, the reason, and asks the Manager to check and solve. The old line "ignore this if you only wait for the PO" is removed.
3. Nobody `working` and every goal `done` (at least one row): the watchdog logs `all goals done; watchdog stops` and `run` returns, so its herdr tab closes. While anyone works it never stops. It never stops with no goals file or an empty table.
4. No goals file (a scope from before this change): the watchdog behaves as after ticket 01 (ticket-based idle check, nudges, no stop). Existing tests of that behaviour keep passing.
5. `squad-watchdog ensure --home DIR --manager NAME`: starts the watchdog if its heartbeat is not fresh, else does nothing (the same guard as `squad-start`'s `watchdog_alive`; reuse its tab/detached start, no second copy). `squad-start` of a new or resumed scope still starts it (unchanged).
6. The `blocked`-pane wake (10 minutes) and sleep-when-idle are unchanged.
7. Docstring, `README.md` (also drop the sentence "says nothing when a ticket passes or comes back" or restate it as the goals model) and `squad-watchdog status` (shows open goal count) describe the new behaviour.
8. Tests: extend `tests/test_squad_watchdog.py`, no new file: (a) open goal + idle -> nudge at 5/15 with the reason text; (b) all done + idle -> stop line and `run` returns; (c) all done but an agent working -> no stop; (d) no goals file -> as before; (e) `ensure` starts once, a second call does nothing.
9. `## Behaviour` replays `python3 -I <scope folder>/evidence/idle-demo.py <fresh dir>` extended with the goal cases (open, blocked with reason, all done -> stops, no file). The Manager shows Chieu that output.

10. (QA whitebox, LC-8b; defect class from 01's first return) `evidence.md` `## Checks` cells contain no `\|`; `squad-evidence checks <evidence.md>` exits 0 before HANDIN. `## Review` starts with the AC trace ([SQ-2]), one line per AC1-10.

## Tests to run (targeted)
`cd tests && python3 -m unittest test_squad_watchdog test_squad_start`, plus every hit of `grep -rl 'squad-watchdog\|watchdog_alive' tests/`. SQ-10 applies (`bin/` text): also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`.

## Manager notes
- Related: 02 (process) writes the Manager's rule for the goals file and the `ensure` call; 02 starts after 03 passes.
- SQ-15 dry run: base is 01's branch tip e5589e2.
