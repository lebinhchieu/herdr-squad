# Task 03: Fix 3: plugin watchdog nudges the Manager when nobody works

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes in its last scope); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED 03`.

Status: ready
Source: `git show squad/plugin/process-audit/plugin-dev-process-audit-6:.scratch/process-audit/report.md` (6f500f8, unmerged), section 4 finding 3. Read only that finding.
Files: new bin/squad-watchdog, bin/squad-start, tests for them
Ticket: commit this file's content as `.scratch/process-fixes/issues/03-watchdog.md` in your first commit.
Base: main.

## AC
- AC1 The plugin ships a watchdog started with every scope/goal; it logs each idle start with every agent's state.
- AC2 It nudges the Manager after 5 and again after 15 minutes of nobody working while work is ready.
- AC3 Sleep-when-done is OPT-IN: it turns on for an agent only when the PO requests it; without that request the watchdog never sleeps. Chieu's words: 'Watchdog should support for sleep when done as well', 'it just enable sleep when done on I request agent'.
- AC4 The nudge text and log are what a person reads: QA blackbox checks them. Touched test files pass.

## Rules to follow
- [REV-15] report deliverable: copy any report into `$SCOPE_DIR/evidence/{n}/` at the handed-in sha.
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": run only touched test files plus `grep -rl` hits for touched `templates/` paths or printed strings.
- Do not bump the plugin version; the last scope does it once.

## Design notes
- **Program:** new `bin/squad-watchdog` (Python). `run --home H --manager M` loops every 60 s (env `SQUAD_WATCHDOG_INTERVAL`), one `tick` per pass; exits when `H` is gone (squad-close moves it). `tick` runs one pass. `sleep AGENT [--off]` and `status` for the Manager.
- **Start:** `squad-start` starts `run` detached after the Manager spawn, for a lone scope, a goal and `--resume`; not for `--dry-run`, not for `--in-goal` (no Manager; the goal's watchdog scans its scopes each pass). `SQUAD_WATCHDOG=off` skips it. One watchdog per home: a heartbeat in `watchdog.state.json` (no pid probe, portable).
- **Reuse:** `squadboard_agents.fetch` (herdr status), `squadboard_active.roster_rows` (roster), `squadtickets.scope_tasks` (tickets).
- **Idle:** no live agent of the home (and, for a goal, its scopes) is `working` in herdr AND a ticket is open (ready, building, returned, handed in, checking). A blocked ticket does not count. herdr not answering = no decision.
- **Log:** `<home>/watchdog.log`, one line per event, UTC: `idle start` (lists every agent and its state, and the waiting tickets), `nudge 5 min` / `nudge 15 min` (what was sent and to whom), `idle end after N min`, `sleep ...`.
- **Nudge:** `herdr agent prompt <manager> "<text>"` at 5 and at 15 min, once each per idle spell. Text: plain sentences: since when, which tickets wait, every agent's state, what to do, and that the PO's answer being awaited is a reason to ignore it.
- **Sleep (opt-in, AC3):** reading of "sleep when done" = close the agent's pane and keep worktree and branch, i.e. `squad-retire` (it saves notes first). Off for everyone. `squad-watchdog sleep AGENT` (the Manager runs it only when the PO asks) writes the name in `<home>/watchdog.sleep`; `--off` removes it. A listed agent sleeps when its herdr state is idle for 2 min and its roster `ticket NN` is done. Never the Manager; an agent with no ticket number never sleeps. No file / empty file = never sleeps.
- **Assumption to confirm:** "sleep" = retire (pane closed). If the PO means something else, only `do_sleep` changes.
- **Tests:** `tests/test_squad_watchdog.py` (pure decision + tick + CLI with a fake herdr) and 1-2 cases in `tests/test_squad_start.py`.
