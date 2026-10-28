# Your process rules
agent: plugin-dev-cwcl-4 · role: dev · scope: coachwait-closelocal (size M, design no, qa full, goal no)
plugin: 0.5.0 5adfc45151ab8611abc76c11cc4939cc5fc2db90 · overlay: 0 operations applied · composed: 2026-10-22T19:31:23Z
rules: CORE-1 CORE-2 CORE-3 CORE-4 CORE-5 CORE-6 START-6 START-10 MSG-3 MSG-4a MSG-11a LC-3a LC-18 LC-20c LC-25 REV-13b REV-14c EVID-2a EVID-2d COST-5a SAFE-1a SAFE-3 SAFE-4 SAFE-11 SUITE-2c

## CORE-1 Task states
`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`.

## CORE-2 Message types
Send with `SendMessage` to the agent name in `roster.md`, as `<TYPE> <TASK-ID>: <text>`. Types: `ASK`, `ANSWER`, `DECISION`, `BLOCKED`, `HANDIN`, `PASS`, `FAIL`, `STATUS`.

## CORE-3 Owners
Owners: Manager process, roster, scope size; Designer UI; the rest by size: [WHO-1a], [WHO-1b], [WHO-2].

## CORE-4 Two rounds
No agreement after 2 exchanges: send it to its owner, or to the Manager when the owner is one of you.

## CORE-5 Files first
Write a durable thing to a file first, then message a pointer to it.

## CORE-6 Rules not attached
A rule cited as `[ID]` that is not in this file: run `squad-process rule <ID>`. `squad-process who <ID>` shows which roles it binds.

## START-6 Session start
1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME $SQUAD_SCOPE`; empty → ask the Manager.
2. Read `project.md`, `$SCOPE_DIR/scope.md`, `roster.md`, your `roles/$SQUAD_NAME.notes.md` if any; in a goal also `$GOAL_DIR/goal.md`, `$GOAL_DIR/shared/`.

## START-10 Developer start
1. Read your briefing (task, AC, design, peers).
2. `git status`, `git branch --show-current`: expect `squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME`, work only there.
3. Read CLAUDE.md and the `project.md` conventions.

## MSG-3 Task ID
Task ID = the ticket number `NN` alone, never an alias or slug. Name it after the type; never paste, point at files.

## MSG-4a Ask the owner, S and M
Ask the owner from `roster.md`; when it doesn't say, ask the Manager.

## MSG-11a Gaps, S and M
No guessing at a gap: `ASK` the Manager (a business doubt moves the scope up, [SIZE-14]); `BLOCKED <task>` and `STATUS?` answers go to the Manager. Work on the unblocked.

## LC-3a Returned task
On `FAIL`: fix every finding, re-verify, hand in again; same task, same branch.

## LC-18 Developer work
- `squad-label "<ticket id> <few words>"` on taking a ticket, `squad-label ""` to wait.
- Implement as designed; reuse code.
- Before hand-in run `project.md`'s "done" tests, linters and checks on changed files; test new behaviour.

## LC-20c Done, M
Done when both QAs sent `PASS`. Tell the Manager and wait; it retires you.

## LC-25 Advisor when stuck
Consult the advisor before the next try after 2 failed attempts at one error, the same `BLOCKED` sent twice with no `ANSWER`, or (Developer) a 3rd `FAIL`. Add a 3-line note to the task file: question, advice, what was done. Advisor off: skip and say so.

## REV-13b Hand in, M and L
`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA whitebox and QA blackbox.

## REV-14c Diff check after PASS, M
After a PASS, a later commit goes to both QAs as `HANDIN <task>: diff check <passed sha>..<new sha>`; tell the Manager after both pass it.

## EVID-2a Behaviour
You write `## Behaviour` in the ticket's `evidence.md`, commit it with your code, and embed screenshots as `![alt](img/<file>)`.

## EVID-2d Assemble evidence, M
Once every checker has passed: `squad-evidence add <ticket> --heading "<H>" --from <review file>` per review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Manager.

## COST-5a Developer retires, S and M
At 120k with the ticket merged-ready, or when no open ticket touches your files, retire (no `squad-respawn`). Mid-ticket, respawn once, then the Manager splits the rest. A retired name is never reused.

## SAFE-1a No push, Developer
Commit only to your own `squad/<squad>/<scope>/<agent>` branch; `git merge` only inside it. Never push, rebase or touch another worktree.

## SAFE-3 Close what you open
Before reporting, end every browser session and stop every server or process you started, by PID; never `pkill`/`killall`.

## SAFE-4 Stay in your lane
Edit only the files your role owns, plus your own notes file.

## SAFE-11 Scratch directories
Make scratch dirs with `mktemp -d`. Never `rm -rf` a bare variable path: write `rm -rf "${VAR:?}"` or a literal path (Claude Code blocks the bare form).

## SUITE-2c Suites, Developer, M
Run only the test files you touched; the full suite is QA whitebox's; two suite runs never overlap.
