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

## Manager ruling (2026-11-06)
- AC3 = reading A: per agent. Chieu names an agent (`squad-watchdog sleep AGENT`); once its ticket is done and it is idle 2 min, the watchdog retires it. Nobody named = nothing sleeps. Chieu's words: "it just enable sleep when done on I request agent".
- No process-rule line (templates stay outside touches); the README documents the command. Confirm with Chieu at check-in.

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
- **Assumption to confirm:** "sleep" = retire (pane closed). If the PO means something else, only `retire()` in `bin/squad-watchdog` changes.
- **Tests:** `tests/test_squad_watchdog.py` (pure decision + tick + CLI with a fake herdr) and 1-2 cases in `tests/test_squad_start.py`.

## Review

AC trace (run from `tests/`: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q <module>`):

AC1 | test_squad_watchdog.test_an_idle_start_is_logged_with_every_agents_state_and_the_waiting_tickets; test_scopes_of_a_goal_that_share_a_ticket_folder_list_each_ticket_once; test_squad_start.test_a_scope_and_a_goal_start_a_watchdog_and_a_dry_run_or_an_in_goal_scope_does_not | `python3 -m unittest -q test_squad_watchdog test_squad_start`
AC2 | test_squad_watchdog.test_the_manager_is_nudged_once_at_5_and_once_at_15_minutes; test_work_ends_the_spell_and_the_next_spell_nudges_again; test_tick_in_a_process_sends_the_nudge_to_the_manager_through_herdr (real `herdr agent prompt` call) | `python3 -m unittest -q test_squad_watchdog`
AC3 | test_nothing_sleeps_unless_the_po_named_the_agent; test_a_named_agent_sleeps_only_with_a_done_ticket_and_after_2_idle_minutes; test_cli_sleep_turns_an_agent_on_and_off | `python3 -m unittest -q test_squad_watchdog`
AC4 | `.scratch/process-fixes/issues/03-watchdog/evidence.md` (log and both nudges as a person reads them); the CLI recipe below shows the same without Python | the recipe below; tests above

Touched test files: test_squad_watchdog, test_squad_start, squadtest (clean_env sets `SQUAD_WATCHDOG=off`). Hits of `grep -rl squad-start tests/` and README, all pass: test_instructions, test_old_language_inventory, test_squad_respawn, test_squadboard_server, test_squadruntime, test_team_models, test_templates, test_windows_safe, test_promotion_0_6_0, test_squad_close, test_squad_path_guard, test_no_bare_bash, test_sizes. `project.md` names no linter.

CLI-only recipe for QA blackbox (no Python to write; the scope folder must sit under a `.claude/squads/<squad>/scopes/` path):

```
W=<worktree>/bin/squad-watchdog; D=$(mktemp -d); H=$D/.claude/squads/t/scopes/s1; mkdir -p $H/tasks $D/fakebin
printf '#!/usr/bin/env bash\necho "$@" >> "$HERDR_LOG"\n' > $D/fakebin/herdr; chmod +x $D/fakebin/herdr
printf '# s1\n' > $H/scope.md; printf '# T\n\nStatus: ready\n' > $H/tasks/03.md
printf '| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n| t-mgr-s1 | manager | s1 | plan | live | a |\n| t-dev-s1 | dev | s1 | ticket 03 | building | b |\n' > $H/roster.md
echo '{"result":{"agents":[{"name":"t-mgr-s1","agent_status":"idle"},{"name":"t-dev-s1","agent_status":"idle"}]}}' > $D/h.json
export HERDR_LOG=$D/herdr.log PATH=$D/fakebin:$PATH PYTHONDONTWRITEBYTECODE=1
for t in 08:00 08:05 08:15; do python3 $W tick --home $H --manager t-mgr-s1 --herdr-json $D/h.json --now 2027-01-15T$t:00Z; done
cat $H/watchdog.log; cat $HERDR_LOG      # idle start line, nudge 5, nudge 15; two `agent prompt t-mgr-s1 WATCHDOG: ...` calls
python3 $W sleep t-dev-s1 --home $H      # opt in; `--off` turns it off. Without it nothing is ever retired
```
Then set the Manager to `working` in h.json and tick once more: the log gets `idle end after 20 min`. Clean up: `cd /; rm -rf $D`.

Points for the checkers:
- "Sleep" = `squad-retire` (pane closed, worktree and branch kept), per agent, on the PO's request: the Manager's ruling FINAL 03.
- README only tells the Manager about `squad-watchdog sleep AGENT`; no template touched (Manager ruling).
- Idle uses herdr's `working`; a blocked agent counts as not working. A scope folder not under `.claude/` gives no tickets, so no nudge.
