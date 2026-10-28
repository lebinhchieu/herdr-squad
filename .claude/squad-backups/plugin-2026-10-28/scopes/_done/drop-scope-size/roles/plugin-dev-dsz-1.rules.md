# Your process rules
agent: plugin-dev-dsz-1 · role: dev · scope: drop-scope-size (size L, design no, architecture yes, qa full, goal no)
plugin: 0.5.2 294957333ee4b2953e1db26e96e297637ed2343c · overlay: 0 operations applied · composed: 2026-10-27T13:33:10Z
rules: CORE-1 CORE-2 CORE-3 CORE-4 CORE-5 CORE-6 START-6 START-10 MSG-3 MSG-4b MSG-11b LC-3a LC-18 LC-19c LC-20b LC-25 REV-13b REV-14b EVID-2a EVID-2b COST-5 SAFE-1a SAFE-3 SAFE-4 SAFE-11 SUITE-2a

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

## MSG-4b Ask the owner, L
Ask the owner from `roster.md`; when it doesn't say, ask the Team Lead.

## MSG-11b Gaps, L
No guessing at a gap. `ASK` the Tech Lead (technical), the BA (business or scope), the Team Lead (plan or order). `BLOCKED <task>` and `STATUS?` answers go to the Team Lead. Work on the unblocked meanwhile.

## LC-3a Returned task
On `FAIL`: fix every finding, re-verify, hand in again; same task, same branch.

## LC-18 Developer work
- `squad-label "<ticket id> <few words>"` on taking a ticket, `squad-label ""` to wait.
- Implement as designed; reuse code.
- Before hand-in run `project.md`'s "done" tests, linters and checks on changed files; test new behaviour.

## LC-19c Architecture
Build inside `$SCOPE_DIR/architecture.md`; a difference is an `ASK` to the Architect, and after 2 rounds the Manager decides.

## LC-20b Done, L
Done when both QAs sent `PASS`. Tell the Team Lead and wait; it retires you.

## LC-25 Advisor when stuck
Consult the advisor before the next try after 2 failed attempts at one error, the same `BLOCKED` sent twice with no `ANSWER`, or (Developer) a 3rd `FAIL`. Add a 3-line note to the task file: question, advice, what was done. Advisor off: skip and say so.

## REV-13b Hand in, M and L
`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA whitebox and QA blackbox.

## REV-14b Diff check after PASS, L
After a PASS, a later commit goes to both QAs as `HANDIN <task>: diff check <passed sha>..<new sha>`; tell the Team Lead after both pass it.

## EVID-2a Behaviour
You write `## Behaviour` in the ticket's `evidence.md`, commit it with your code, and embed screenshots as `![alt](img/<file>)`.

## EVID-2b Assemble evidence
After every checker passed: `squad-evidence add <ticket> --heading "<H>" --from <review file>` per review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Tech Lead.

## COST-5 Developer retires
Retire (no `squad-respawn`) at 120k with the ticket merged-ready, or when no open ticket touches your files. Mid-ticket respawn once, then the Team Lead splits the rest. Never reuse a retired name.

## SAFE-1a No push, Developer
Commit only to your own `squad/<squad>/<scope>/<agent>` branch; `git merge` only inside it. Never push, rebase or touch another worktree.

## SAFE-3 Close what you open
Before reporting, end every browser session and stop every server or process you started, by PID; never `pkill`/`killall`.

## SAFE-4 Stay in your lane
Edit only the files your role owns, plus your own notes file.

## SAFE-11 Scratch directories
Make scratch dirs with `mktemp -d`; `cd` out before `rm` (Claude blocks the cwd or a parent). No bare `rm -rf $VAR`: use `"${VAR:?}"` or a literal.

## SUITE-2a Suites, Developer
Run only the test files you touched; the full suite is the Tech Lead's; two suite runs never overlap.
