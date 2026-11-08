# Task 01: sleep on idle for any reason

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (the goal promotes in its last scope, goals/watchdog2/promote.md); full suite: QA whitebox, once on the final sha, only after Chieu says yes through the Manager. A risk flag, user-visible change or business doubt: `BLOCKED <task>`.

Status: handed in
Source: `goals/watchdog2/goal.md` (Request 1 and Chieu's clarification) and `shared/decisions.md`. Read only those and `bin/squad-watchdog`.
Files: `bin/squad-watchdog`, `tests/test_squad_watchdog.py`. No other file (README is edited by the promotion task).
Ticket: commit this file's content as `.scratch/watchdog2/issues/01-sleep-on-idle.md` in your first commit.
Base: main. Repo: /home/chieule/workspace/squad.

## AC
- AC1 With `sleep on`, `decide()` returns the `sleep` event when no agent anywhere on the machine has been `working` for `sleep_after` seconds, whatever the tickets are (all done, passed, open, none).
- AC2 `passed` joins DONE for `all_done`. `all_done` is used only for the reason in the log line.
- AC3 The `sleep pc` log line names the reason: `sleep pc: all tickets passed ...` when `all_done`, else `sleep pc: team idle with open tickets ...`. It still says the PO asked, still logs before the switch goes off, and the switch still goes off after (one shot).
- AC4 A working agent anywhere resets the quiet timer. `sleep off` (or no switch) never fires. herdr not answering is still no decision and restarts the timer.
- AC5 `squad-watchdog sleep on` prints text that matches the new rule (idle for any reason), and the module docstring is rewritten to the same rule.
- AC6 Tests: one per trigger (all passed, open tickets), one that a working agent resets the timer, one that `sleep off` never fires. Rewrite the existing sleep tests that assumed "every ticket done" instead of adding copies. Touched test files pass.

## Design notes (Developer fills in)
- `decide`: the sleep gate is now `if not snap["machine_working"]:`. The `sleep` event carries the reason: `("sleep", minutes, all_done(snap))`, so `tick` needs no second look at the snapshot.
- `DONE` gains `passed`. `all_done` is used only for the log reason. No tickets at all counts as "team idle with open tickets" (AC3 else-branch).
- Log line: `sleep pc: all tickets passed; nobody on this machine has worked for N min (...)` or `sleep pc: team idle with open tickets; ...`. Order unchanged: log, switch off, suspend.
- `sleep on` text and docstring say "idle for any reason". The `sleep-when-done:` status prefix stays (tests and callers read it).
- Tests: rewrote the two sleep tests (passed, open tickets) and the goal test (open scope ticket no longer holds the sleep); added working-agent reset and switch-off tests.

## Rules to follow
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": touched test files plus `grep -rl` hits; no full suite.
- Do not bump the plugin version; the last scope does it once.

## Technical AC (QA whitebox, 2026-11-08; Developer: reply in this file or by ANSWER if you disagree)
- TA1 `decide()` stays pure. The sleep branch is `if not snap["machine_working"]:` and nothing else gates it. The reason (`all_done(snap)`) is computed outside the timer logic: carried in the `sleep` event, or computed in `tick` from the same `snap`. No second herdr call, no new state key.
- TA2 `DONE` gains `passed` (`{"done","resolved","merged","passed"}`). `OPEN` is unchanged. Nothing else reads `DONE` in a way the change alters (grep `DONE` and `all_done` in the file, list the hits in `## Review`).
- TA3 Log line order unchanged: `log` → `set_sleep(False)` → `write_state` → suspend. Both reasons keep the stem `sleep pc:`; the two exact openers are `sleep pc: all tickets passed` and `sleep pc: team idle with open tickets`. The line keeps the minutes and says the PO asked. Quote the final text of each in `## Review`.
- TA4 `quiet_since` is cleared on a herdr gap (`not snap["ok"]`), on a working agent, and after a sleep event. Unchanged lines stay unchanged.
- TA5 `sleep on` output and the docstring (lines 2-24): no remaining text that says "every ticket is done" as a condition. `grep -n "every ticket\|all done\|every ticket of the home" bin/squad-watchdog` shows only text that matches the new rule. The other docstring lines (idle nudges) stay as they are.
- TA6 Tests, each tied to one AC, no copies:
  - all-passed trigger: tickets all `passed` (not only `done`), log line has `all tickets passed`;
  - open-tickets trigger: a `building` ticket, quiet 5 min → suspended once, log line has `team idle with open tickets`;
  - a working agent (also one not in the roster) resets the timer;
  - `sleep off` / no switch never suspends, even with tickets all done;
  - existing tests that assumed "every ticket done" are rewritten (the sleep-once test at line 126 asserted "nothing sleeps while a ticket is open"; the goal test at line 159 asserted the same for scopes). No old assertion is just deleted: each is replaced by the new truth.
  - the one-shot check (`sleep_on` false after, no second suspend after a wake-up) stays.
- TA7 Touched files only: `bin/squad-watchdog`, `tests/test_squad_watchdog.py`. No plugin version bump (`git diff` shows no `plugin.json` or version change).
- TA8 Run `python3 -m unittest` (or the repo runner on) `tests/test_squad_watchdog.py` plus the `grep -rl` hits of `squad-watchdog` in `tests/`, all green, nothing newly skipped. No full suite.
- TA9 Real-sample rule ([REV-4]) does not apply: no new parsing of another tool's output.
- Not a FAIL, but I will list under Follow-ups: the README row for `squad-watchdog` (README.md:46) still describes the old rule; the promotion task owns it.
