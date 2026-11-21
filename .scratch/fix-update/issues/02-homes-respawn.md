# 02 `squad-process homes --apply --yes` respawns the moved homes' live agents at once
Duties: Developer builds and writes design notes (this file is the design) and the evidence; technical AC are in this file (Tech Lead, agreed with QA whitebox); business AC = this ticket as written; QA whitebox code check; QA blackbox behaviour check; hand in to both QAs
Files: bin/squadhomes.py, tests/test_squad_respawn.py, tests/test_squadupgrade.py, README.md
Evidence: .scratch/fix-update/issues/02-respawn-moved-homes/evidence.md
Status: ready
After: 01 (build on 01's branch; the passed sha of 01 is `--base`)

Ticket path: `.scratch/fix-update/issues/02-homes-respawn.md`. Touched files are an estimate (LC-9b); a change re-issues this file.
Harness: `tests/squadtest.py` `fake_herdr(dir, "live")` with `HERDR_LOG` (as `tests/test_squad_respawn.py` setUp) and `PluginCopy`. The stub cannot show a real tab or a real mid-turn agent: say so in `## Behaviour` and list the live check as not done (Chieu's merge check).

## Problem
Chieu's Q3 (b): when a home moves to the new pin, its live agents are respawned at once, not only listed. Respawn is built for an agent's own pane (`bin/squad-respawn`: notes first, old pane closed last); here the Manager's tool drives it for other agents, including one mid-ticket, and never for the Manager itself.

## Design (extends `squadhomes.py` of 01; runs only after the pins and log rows are written)
`--respawn` is the default of `--apply --yes`; `--no-respawn` skips the stage (the rollback and test path). Without `--yes` the NOT APPLIED output includes the plan below as `would respawn:` lines, in order.
1. **Who.** For each moved home: the rows of `<home>/roster.md` whose Status is `live` (table columns Agent, Role, Scope, Owns, Status, Session), minus the caller (`$SQUAD_NAME`). A goal home's roster is the goal's; each scope's is its own. An agent whose `herdr agent get <name>` fails is `not running` (reported, not an error). Order: dev, qa-white, qa-black, tech-lead, ba, designer, architect, then team-lead, so the coordinator restarts after the pod it routes to.
2. **Per agent.** (a) `herdr agent prompt <name> "PIN-MOVE: your home moved to plugin <new>. Finish the step you are on, commit nothing you did not intend to, write roles/<name>.notes.md (NOTE-1), then reply DONE." --wait --timeout <ms>`, the same call `bin/squad-retire` makes for RETIRE. `<ms>` is 300000, or the value of env `SQUAD_HOMES_PROMPT_TIMEOUT_MS` when set to a positive integer (a test and QA override; documented in the `homes` help text). (b) On DONE: run `<target runtime>/bin/squad-respawn <name>` (never the one on PATH, never `--force`) with env `SQUAD_DIR=<squad>` and exactly one of `SCOPE_DIR=<scope home>` / `GOAL_DIR=<goal home>` (the others removed), so it reads that home's roster, notes and new pin. (c) A prompt that does not settle in the timeout, or a respawn that exits non-zero: the agent is `pending`, not killed, not retried; its worktree, branch and open work stay untouched.
3. **The caller.** The tool runs in the Manager's pane, so it never respawns the caller. It prints `caller <name>: last step: report to Chieu, write your notes, then run squad-respawn <name>`; the skill (03) does that.
4. **Output and exit.** One line per agent: `respawned <name>`, `pending <name>: <reason>; run squad-respawn <name> after it saved its notes`, `not running <name>`. Exit 0 when every live agent was respawned or not running; exit 4 when the pins are moved but an agent is `pending` (the pins are never rolled back).
5. Notes: the new session opens in a new herdr tab per `squad-respawn`; the output says so in one line.

## AC
- AC1 Fixture: a goal with two open scopes, each with a roster of live agents, `fake_herdr` live. After `homes --apply --yes` with all three homes chosen, `HERDR_LOG` shows, per agent, a `prompt` call before the respawn call, the order of Design 1, no call for the caller, and each respawn run with `SQUAD_DIR` and exactly one of `SCOPE_DIR`/`GOAL_DIR` set to that agent's own home (assert on the stub's recorded env or argv).
- AC2 The respawn path used is `<target runtime>/bin/squad-respawn` (assert the path in the log); no call passes `--force`.
- AC3 A prompt that returns without DONE (stub timeout) leaves that agent `pending`, exit 4, the other agents still respawned, the moved pins still written, and the output names the agent and the command to run later.
- AC4 `--apply` without `--yes` and `--no-respawn` call herdr zero times (empty `HERDR_LOG`).
- AC5 Roster rows with Status other than `live`, and an agent `herdr agent get` cannot find, are never prompted or respawned; the latter prints `not running`.
- AC6 [SQ-10] `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` run, result quoted; `tests/test_squad_respawn.py` still passes. Subprocess calls use `sys.executable`/list argv, no shell.
- AC8 When the caller (`$SQUAD_NAME`) is a live roster row of a moved home, the last line `--apply --yes` prints is `caller <name>: last step: report to Chieu, write your notes, then run squad-respawn <name>`, after every agent line; with no caller in a moved roster, no such line. (Business AC: the Manager is told, last, what only it can do.)
- AC9 `SQUAD_HOMES_PROMPT_TIMEOUT_MS=<small>` shortens the wait in AC3 (QA blackbox's stub herdr returns no DONE; the run ends in about that time, not five minutes); an invalid value falls back to 300000.
- AC10 (follow-up from 01's PASSes, `bin/squadhomes.py`) A home refused at read time (a malformed `plugin:` line) is named on `--apply` too: its note is printed and `--apply` exits 2, never `nothing to move` exit 0 (a test: one refused-at-read offered home, `--apply --yes`, nothing changed).
- AC11 (same) After `--apply --yes` the table shows the pins as moved (pin now = target, state `at-target`), or the table is printed before the move and each `moved ...` line is the result; say which in the evidence.
- AC7 Evidence says the live behaviour (a real agent mid-turn, the new tab) was not verified, and what Chieu checks at merge.

## SQ-1 (deletes and moves)
Deletes or moves no file; `bin/squad-respawn` and `bin/squad-retire` are called, not edited.

## Comments
