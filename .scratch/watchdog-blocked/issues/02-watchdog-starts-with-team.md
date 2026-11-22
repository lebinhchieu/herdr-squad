# 02 Watchdog starts when the team is spawned
Status: ready-for-agent
Duties: plan-owner=team-lead, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Files: bin/squad-start (start_watchdog calls ~289, 423, 425), bin/squad-spawn (start the home's watchdog after a non-Manager spawn), bin/squad-watchdog (`sleep on` ensures; docstring), templates/squad/process/starting.md (START-19b line 188: drop the `ensure` step), README.md (watchdog start lines), tests/test_squad_start.py, tests/test_squad_watchdog.py, tests for squad-spawn (grep -rl), plugin version files (bump 0.10.3 -> 0.10.4), skills/squad-process-update/changelog.md
Depends: 01 (same files; build on 01's passed sha). Plan: `$SCOPE_DIR/iterations/1.md`.
Evidence: .scratch/watchdog-blocked/issues/02-watchdog-starts-with-team/evidence.md

## What and why
A scope with only its Manager has nobody to wake: the Manager waits on Chieu, and Chieu sees the toast. Today `squad-start` starts the watchdog at once, so it nudges a lone Manager (seen live in this scope). Chieu chose (E1 (a)): the watchdog of a home starts at the first spawn of a non-Manager agent into it.

## Business AC
- AC1 `squad-start` (new scope, new goal, `--in-goal`, `--resume`) starts no watchdog: no `watchdog` tab, no `watchdog.state.json` heartbeat.
- AC2 The first `squad-spawn` of a non-Manager role into a scope home starts that home's watchdog (as `squad-watchdog ensure` does: own tab, one per home); later spawns are a no-op (fresh heartbeat). A Manager respawn starts none.
- AC3 Goal home: the goal's watchdog starts with the first non-Manager spawn of any of its scopes (the scope's own watchdog starts too, per AC2).
- AC4 `squad-watchdog sleep on --home DIR` starts the home's watchdog when it is not running, so away mode sleeps the PC with no team.
- AC5 Rule START-19b no longer tells the Manager to run `squad-watchdog ensure`; the docstring and README say when the watchdog starts.
- AC6 A failure to start the watchdog warns on stderr and never fails the spawn.

## Technical AC
- AC7 Tests for AC1, AC2, AC4, AC6 in the existing files (extend; no new file); tests that pinned the start in `squad-start` are updated, none skipped.
- AC8 Version bump 0.10.3 -> 0.10.4 in every plugin version file; `grep -rn "0\.10\.3" .claude-plugin/ plugin.json 2>/dev/null` (and wherever 0.10.3 is pinned) shows no stale hit; changelog entry.
- AC9 SQ-10: `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and every hit of `grep -rl "squad-watchdog\|start_watchdog\|START-19b" tests/`; quote results. `squad-process lint` exits 0.
- AC10 Live check (QA blackbox): a scratch squad (stub `claude` and herdr, as `tests/test_squad_start.py`): `squad-start` -> no watchdog; `squad-spawn team-lead ...` -> watchdog heartbeat and tab create call; second spawn -> no second watchdog.

## Evidence
`evidence.md` next to the committed ticket; QA cells assembled (EVID-2d) before the Developer is retired.
