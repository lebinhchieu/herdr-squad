# Task 03: Fix 3: plugin watchdog nudges the Manager when nobody works

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes in its last scope); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED 03`.

Status: handed in (rework FINAL 03)
Source: `git show squad/plugin/process-audit/plugin-dev-process-audit-6:.scratch/process-audit/report.md` (6f500f8, unmerged), section 4 finding 3. Read only that finding.
Files: new bin/squad-watchdog, bin/squad-start, tests for them
Ticket: commit this file's content as `.scratch/process-fixes/issues/03-watchdog.md` in your first commit.
Base: main.

## AC
- AC1 The plugin ships a watchdog started with every scope/goal; it logs each idle start with every agent's state.
- AC2 It nudges the Manager after 5 and again after 15 minutes of nobody working while work is ready.
- AC3 Sleep-when-done is OPT-IN: it turns on for an agent only when the PO requests it; without that request the watchdog never sleeps. Chieu's words: 'Watchdog should support for sleep when done as well', 'it just enable sleep when done on I request agent'.
- AC4 The nudge text and log are what a person reads: QA blackbox checks them. Touched test files pass.

## Manager ruling (2026-11-06)
- AC3 = reading A: per agent. Chieu names an agent (`squad-watchdog sleep AGENT`); once its ticket is done and it is idle 2 min, the watchdog retires it. Nobody named = nothing sleeps. Chieu's words: "it just enable sleep when done on I request agent".
- No process-rule line (templates stay outside touches); the README documents the command. Confirm with Chieu at check-in.

## Rework: AC3 changed by Chieu (2026-11-07, answer to E3: "Sleep = sleep PC, don't retire")
**FINAL 03.** This replaces AC3 and the Manager ruling above. "Sleep when done" = the watchdog puts the computer to sleep (suspend). Nothing is retired. Remove `retire()` and the per-agent `watchdog.sleep` list.
- AC3 Opt-in switch for the squad: `squad-watchdog sleep on|off --home H`; `status` shows it. Off by default; the Manager turns it on only when Chieu asks.
- AC3b When the switch is on, the watchdog suspends the PC once, when all hold for 5 minutes (env `SQUAD_WATCHDOG_SLEEP_AFTER`, minutes): every ticket of the home is done (for a goal, of its scopes), and no agent anywhere on the machine is `working` in herdr (the whole `herdr agent list`, not only this squad: other squads run here). herdr not answering = no decision. Logs `sleep pc` first; then sets the switch back to off (one shot, so a wake-up does not sleep again).
- AC3c Suspend command by host, env `SQUAD_WATCHDOG_SLEEP_CMD` overrides it (tests use it): WSL `powershell.exe -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend',\$false,\$false)"`; Linux `systemctl suspend`; macOS `pmset sleepnow`; Windows `rundll32.exe powrprof.dll,SetSuspendState 0,1,0`. Tests never suspend a real machine.
- Follow-ups from the QAs to fold in (cheap): one entry per agent name in log and nudge text; `tick` prints no raw event lines on stdout.
- Retest: AC3, AC3b, AC3c and the README line (rewrite it for `sleep on|off`). QAB re-checks the new text and `status` output.
- Base: your branch continues from dcae61b. HANDIN to QA whitebox and QA blackbox (live: plugin-qaw-watchdog, plugin-qab-watchdog).

## Rules to follow
- [REV-15] report deliverable: copy any report into `$SCOPE_DIR/evidence/{n}/` at the handed-in sha.
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": run only touched test files plus `grep -rl` hits for touched `templates/` paths or printed strings.
- Do not bump the plugin version; the last scope does it once.

## Design notes
- **Program:** new `bin/squad-watchdog` (Python). `run --home H --manager M` loops every 60 s (env `SQUAD_WATCHDOG_INTERVAL`), one `tick` per pass; exits when `H` is gone (squad-close moves it). `tick` runs one pass. `sleep on|off` and `status` for the Manager.
- **Start:** `squad-start` starts `run` detached after the Manager spawn, for a lone scope, a goal and `--resume`; not for `--dry-run`, not for `--in-goal` (no Manager; the goal's watchdog scans its scopes each pass). `SQUAD_WATCHDOG=off` skips it. One watchdog per home: a heartbeat in `watchdog.state.json` (no pid probe, portable).
- **Reuse:** `squadboard_agents.fetch` (herdr status), `squadboard_active.roster_rows` (roster), `squadtickets.scope_tasks` (tickets).
- **Idle:** no live agent of the home (and, for a goal, its scopes) is `working` in herdr AND a ticket is open (ready, building, returned, handed in, checking). A blocked ticket does not count. herdr not answering = no decision.
- **Log:** `<home>/watchdog.log`, one line per event, UTC: `idle start` (lists every agent and its state, and the waiting tickets), `nudge 5 min` / `nudge 15 min` (what was sent and to whom), `idle end after N min`, `sleep ...`.
- **Nudge:** `herdr agent prompt <manager> "<text>"` at 5 and at 15 min, once each per idle spell. Text: plain sentences: since when, which tickets wait, every agent's state, what to do, and that the PO's answer being awaited is a reason to ignore it.
- **Sleep (opt-in, AC3, FINAL 03):** "sleep when done" = suspend the PC, nothing retired. Switch in `<home>/watchdog.sleep` (`on` line; no file = off), set by `squad-watchdog sleep on|off`. `decide` keeps `quiet_since`: set while every ticket of the home (goal: its scopes) is done and no agent in the whole `herdr agent list` is `working`; cleared otherwise; herdr down = no decision. When the switch is on and `quiet_since` is `SQUAD_WATCHDOG_SLEEP_AFTER` minutes old (default 5): log `sleep pc`, switch off (one shot), suspend. Command: `SQUAD_WATCHDOG_SLEEP_CMD` (shell) or by host (WSL powershell, `systemctl suspend`, `pmset sleepnow`, `rundll32`).
- **Tests:** `tests/test_squad_watchdog.py` (pure decision + tick + CLI with a fake herdr) and 1-2 cases in `tests/test_squad_start.py`.

## Review

AC trace (run from `tests/`: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q <module>`):

AC1 | test_squad_watchdog.test_an_idle_start_is_logged_with_every_agents_state_and_the_waiting_tickets; test_scopes_of_a_goal_that_share_a_ticket_folder_list_each_ticket_once; test_a_name_listed_twice_in_the_roster_shows_once_in_the_log_and_the_nudge; test_squad_start.test_a_scope_and_a_goal_start_a_watchdog_and_a_dry_run_or_an_in_goal_scope_does_not | `python3 -m unittest -q test_squad_watchdog test_squad_start`
AC2 | test_squad_watchdog.test_the_manager_is_nudged_once_at_5_and_once_at_15_minutes; test_work_ends_the_spell_and_the_next_spell_nudges_again; test_tick_in_a_process_sends_the_nudge_to_the_manager_through_herdr (real `herdr agent prompt` call; stdout empty) | `python3 -m unittest -q test_squad_watchdog`
AC3 | test_the_pc_never_sleeps_unless_the_switch_is_on; test_cli_sleep_on_and_off_and_status_shows_the_switch | `python3 -m unittest -q test_squad_watchdog`
AC3b | test_the_pc_sleeps_once_after_5_quiet_minutes_when_every_ticket_is_done; test_an_agent_of_another_squad_working_holds_the_sleep_and_restarts_the_clock; test_a_goal_sleeps_only_when_the_tickets_of_all_its_scopes_are_done; test_herdr_not_answering_is_no_decision_for_the_sleep | same
AC3c | test_the_suspend_command_comes_from_the_env_or_the_host_and_runs_after_the_log_and_the_switch (env command in a real process; host table; tests never suspend) | same
Follow-ups | one entry per name: test_a_name_listed_twice...; `tick` stdout empty: asserted in test_tick_in_a_process... and the AC3c test | same
README | row for `bin/squad-watchdog` in README.md, rewritten for `sleep on|off` | read it
AC4 | `.scratch/process-fixes/issues/03-watchdog/evidence.md` (log, nudges, `sleep pc` as a person reads them) and the CLI recipe below | the recipe below

Touched test files: test_squad_watchdog (AC3 tests replaced), test_squad_start and squadtest unchanged since dcae61b. Hits of `grep -rl squad-watchdog tests/`: only test_squad_watchdog. `project.md` names no linter.

CLI-only recipe for QA blackbox (no Python to write; the scope folder must sit under a `.claude/squads/<squad>/scopes/` path). The suspend command is replaced, so nothing sleeps:

```
W=<worktree>/bin/squad-watchdog; D=$(mktemp -d); H=$D/.claude/squads/t/scopes/s1; mkdir -p $H/tasks $D/fakebin
printf '#!/usr/bin/env bash\necho "$@" >> "$HERDR_LOG"\n' > $D/fakebin/herdr; chmod +x $D/fakebin/herdr
printf '# s1\n' > $H/scope.md; printf '# T\n\nStatus: ready\n' > $H/tasks/03.md
printf '| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n| t-mgr-s1 | manager | s1 | plan | live | a |\n| t-dev-s1 | dev | s1 | ticket 03 | building | b |\n' > $H/roster.md
echo '{"result":{"agents":[{"name":"t-mgr-s1","agent_status":"idle"},{"name":"t-dev-s1","agent_status":"idle"},{"name":"other-dev-x","agent_status":"working"}]}}' > $D/h.json
sed 's/working/idle/' $D/h.json > $D/h2.json      # the other squad's agent stops working
export HERDR_LOG=$D/herdr.log PATH=$D/fakebin:$PATH PYTHONDONTWRITEBYTECODE=1 SQUAD_WATCHDOG_SLEEP_CMD="echo SUSPEND-CALLED >> $D/suspend.log"
python3 $W status --home $H                       # sleep-when-done: off
python3 $W sleep on --home $H                     # opt in; `off` turns it off
for t in 08:00 08:05 08:15; do python3 $W tick --home $H --manager t-mgr-s1 --herdr-json $D/h.json --now 2027-01-15T$t:00Z; done
sed -i 's/ready/done/' $H/tasks/03.md             # every ticket done; the other squad still works, so no sleep
for t in 08:20 08:50; do python3 $W tick --home $H --manager t-mgr-s1 --herdr-json $D/h.json --now 2027-01-15T$t:00Z; done
for t in 08:51 08:55 08:56 09:30; do python3 $W tick --home $H --manager t-mgr-s1 --herdr-json $D/h2.json --now 2027-01-15T$t:00Z; done
cat $H/watchdog.log; cat $HERDR_LOG; cat $D/suspend.log; python3 $W status --home $H   # `sleep pc` at 08:56, SUSPEND-CALLED once, switch off
```
Clean up: `cd /; rm -rf $D`. Expected log: `idle start`, `nudge 5 min`, `nudge 15 min`, `idle end after 20 min`, `sleep pc` at 08:56 (5 quiet minutes after 08:51), nothing after it.

Points for the checkers:
- "Sleep" = the PC suspends (FINAL 03). Nothing is retired; `retire()` and the per-agent list are gone.
- The quiet clock runs while the switch is off too: turning the switch on when everything is already done and quiet sleeps the PC at the next pass (every minute).
- Idle (nudges) uses herdr's `working` of this home's agents; the sleep check uses the whole machine. A blocked agent counts as not working. A scope folder not under `.claude/` gives no tickets, so no nudge and no sleep.
