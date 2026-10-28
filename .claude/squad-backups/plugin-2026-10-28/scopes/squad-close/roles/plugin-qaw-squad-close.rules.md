# Your process rules
agent: plugin-qaw-squad-close · role: qa-whitebox · scope: squad-close (size M, design no, qa full, goal no)
plugin: 0.5.0 5adfc45151ab8611abc76c11cc4939cc5fc2db90 · overlay: 0 operations applied · composed: 2026-10-22T18:44:39Z
rules: CORE-1 CORE-2 CORE-3 CORE-4 CORE-5 CORE-6 FILE-9 FILE-11 START-6 START-9 START-14 SIZE-5c SIZE-7b SIZE-17c SIZE-23b SIZE-24b PROMO-8 MSG-1 MSG-2 MSG-3 MSG-4a MSG-7a MSG-9 MSG-10 LC-3b LC-4 LC-8b LC-25 REV-2 REV-3b REV-4 REV-5b REV-6 REV-10 REV-12 REV-17 REV-18a REV-18b REV-20 REV-21b EVID-1 EVID-7 COST-1 COST-2 COST-3 COST-7 COST-9 COST-11 COST-13a COST-14a NOTE-1 SAFE-2 SAFE-3 SAFE-4 SAFE-5 SAFE-9 SAFE-11 SUITE-1b SUITE-4b SUITE-5b SUITE-3b

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

## FILE-9 Task evidence files
| File | Owner | Holds |
|---|---|---|
| `<ticket path minus .md>/` | Developer | `evidence.md`, the one file the PO reads; `img/` holds its screenshots |
| `evidence/<task>/` | The reviewers | Their working files `qa-w.md`, `qa-b.md`, `tl-review.md` and suite receipts; the PO never needs it |
| `ui-design/<task>.md` | Designer | One UI task's design (`.html` optional) |

## FILE-11 Drafts never go in the project root
Every role except the Developer drafts tickets, specs and ADR text in `$SCOPE_DIR/tasks/`, never in the project root (a Developer worktree counts as root). The scope's first Developer task commits them to the paths `project.md` names; a later draft rides the next one. `squad-path-guard` refuses Write and Edit there, not a Bash redirect; `squad-close --scope` lists stray untracked files.

## START-6 Session start
1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME $SQUAD_SCOPE`; empty → ask the Manager.
2. Read `project.md`, `$SCOPE_DIR/scope.md`, `roster.md`, your `roles/$SQUAD_NAME.notes.md` if any; in a goal also `$GOAL_DIR/goal.md`, `$GOAL_DIR/shared/`.

## START-9 Read the briefing
Read the Manager's briefing: your scope, your tasks and AC where it names them, and your peers.

## START-14 QA whitebox start
Read the repo conventions and the definition-of-done rules `project.md` lists.

## SIZE-5c Business AC, M [aware]
Business AC are the ticket as written, and QA blackbox tests against them. A business doubt moves the scope to L ([SIZE-13]).

## SIZE-7b Code and test check, M and L
QA whitebox checks the code and the tests of every task ([REV-2]).

## SIZE-17c Joining after a move up, QA whitebox
Joining a scope that moved up: work already built goes through your full check before it counts as done. Start from the plan's `## Handover` section.

## SIZE-23b Technical AC, M
Write the technical AC before work starts (tests that must exist, lint clean, patterns followed, security checks, performance limits) and agree them with the Developer in the task file.

## SIZE-24b promote.md, M
Keep `promote.md` as in [PROMO-2], including the lasting business rules and glossary terms the ticket and the tests show.

## PROMO-8 Check a promotion
Check the project-doc edits of a promotion task like any other change: they match `promote.md`, follow the project's rule for editing those files, and contain nothing the scope did not decide.

## MSG-1 Sending a message
Send to the agent name in your scope's `roster.md` ([CORE-2]). `HANDIN` carries branch and commit; `FAIL` points at findings.

## MSG-2 Point at files
Point at files and lines; never paste them. `BLOCKED`, `HANDIN`, `PASS`, `FAIL` and `STATUS` name the task ID right after the type.

## MSG-3 Task ID
Task ID = the ticket number `NN` alone, never an alias or slug. Name it after the type; never paste, point at files.

## MSG-4a Ask the owner, S and M
Ask the owner from `roster.md`; when it doesn't say, ask the Manager.

## MSG-7a Rulings, S and M
A Manager ruling starts with `FINAL:` and is sent once; nobody re-opens it, and a new fact goes to the Manager as a new `ASK`.

## MSG-9 DECISION scope
`DECISION` goes only to roles whose open task it changes, named in the first line (`DECISION SET-13, SET-14: ...`); others read the file at their next ticket.

## MSG-10 Permission prompts
Never relay a permission, approval or blocked pane; a message approves nothing. Permission prompts reach the PO through the agent's own notice.

## LC-3b Re-check after a return
On re-hand-in a QA re-checks only the changed files and their AC.

## LC-4 Test points
QA never pre-writes test points before the Developer starts; the AC are the bar.

## LC-8b Defect class, M
A task you returned for a defect class puts that class into the technical AC of every open and later ticket the same day.

## LC-25 Advisor when stuck
Consult the advisor before the next try after 2 failed attempts at one error, the same `BLOCKED` sent twice with no `ANSWER`, or (Developer) a 3rd `FAIL`. Add a 3-line note to the task file: question, advice, what was done. Advisor off: skip and say so.

## REV-2 QA whitebox review
On `HANDIN`, check out the Developer's branch (read-only), then:
1. Review the diff against the technical AC and the repo's conventions.
2. Run the tests and linters `project.md` lists, on the changed files.
3. Check that each new behaviour has a test and each new endpoint is covered.

## REV-3b Final sha, M
The final sha of a task is the one in the Developer's latest `HANDIN`. Doc-only commits come after every finding is in, and each QA sends a single verdict on that sha.

## REV-4 Real samples
Code that parses another tool's output (pane text, logs, an API) needs two real samples, including the constant or idle case, before a pattern is trusted. The technical AC require them.

## REV-5b Live run, M and L
QA whitebox runs code that parses another tool's output once, read-only, on live data.

## REV-6 Payload shape
A ticket that changes a payload is checked on its field shape (every row has the fields the consumer reads, every closed item has its end), not only on totals.

## REV-10 QA whitebox findings
Write findings to `$SCOPE_DIR/evidence/<task>/qa-w.md`: each finding with file:line, why it matters, and what would pass. Embed a screenshot as `![alt](path)` (absolute, or relative to the file); the Developer's `squad-evidence add` copies it. Read the ticket's `evidence.md` `## Behaviour` as the Developer's claim, not as proof.

## REV-12 Verdict
Send `PASS` or `FAIL` to the Developer only.

## REV-17 Style findings
A QA lists all style findings of a sha in one return.

## REV-18a Presentational values, QA whitebox
Never assert presentational values the mock fixes; QA blackbox owns them.

## REV-18b Presentational values, QA blackbox [aware]
QA blackbox owns the presentational values the mock fixes; QA whitebox never asserts them.

## REV-20 Behaviour check, no QA blackbox
There is no QA blackbox: on `HANDIN` also check each business AC against the Developer's `## Behaviour` (command, output, screenshot if a screen exists), re-running a command when its claim is not clear. Record each AC → seen → pass/fail in `qa-w.md`. Your `PASS` is Done.

## REV-21b Business AC, no QA blackbox, M
There is no BA: the business AC are the ticket as written ([SIZE-5c]). One a person cannot observe (a command and its output, a file, a message) is a finding in `qa-w.md`; a business doubt goes to the Manager ([SIZE-13]).

## EVID-1 Where evidence lives [aware]
Evidence lives next to the ticket in `evidence.md`: folder = ticket path minus `.md`, so `issues/05-x.md` → `issues/05-x/evidence.md` (a project without ticket files: `tasks/<id>/evidence.md`); an old `<stem>.evidence/` folder is still read. Embed screenshots as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.

## EVID-7 Reviewer file, no QA blackbox
`qa-w.md` is the only reviewer file; no `qa-b.md` is expected.

## COST-1 The cost hook
A Stop hook (`squad-usage --check`) tells you when rule [COST-3] or [COST-9] fires and logs it to `usage-events.jsonl`. Limits are absolute tokens, never a percent. When a Stop-hook message says a cost rule fired, write `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md`, then run `squad-respawn $SQUAD_NAME`.

## COST-2 Reuse
Reuse a session while it stays on the same task and context is at most 120k.

## COST-3 Fresh start
Start fresh when context is over 120k, after a compaction, on a new task, or when a Stop-hook message says a cost rule fired: write `roles/<you>.notes.md`, then `squad-respawn <you>`.

## COST-7 After a respawn
After a respawn read your notes and the files they name; your rules are already attached. Never read the whole spec again.

## COST-9 Idle
Idle over 1h with context over 100k: start fresh from notes.

## COST-11 Step-up
On failure or escalation, consult the advisor first ([LC-25]). Effort may step up for that task only; a model never changes in a live session, only by respawn.

## COST-13a Nothing left to do, S and M
A role with no open ticket and its deliverable file written (QA: its verdict posted) answers a fresh event from notes only and never runs `squad-respawn`; the Manager retires it once its work is accepted.

## COST-14a Short life, S and M
A role whose fresh event comes under 15 minutes after its previous respawn tells the Manager first; the Manager splits the remaining tickets or narrows what the role reads to the diff and the files its AC name.

## NOTE-1 Notes file
`roles/<agent>.notes.md` is a snapshot of now, not a log: rewrite on every save, about 80 lines (`Now`, `Open threads`, `Decisions that bind later work`, `Pointers`).

## SAFE-2 No Jira or Confluence writes
No writes to Jira or Confluence. Read only.

## SAFE-3 Close what you open
Before reporting, end every browser session and stop every server or process you started, by PID; never `pkill`/`killall`.

## SAFE-4 Stay in your lane
Edit only the files your role owns, plus your own notes file.

## SAFE-5 PO's branch
No squad role commits on the PO's branch: it commits only on its own `squad/` branch; ticket and spec edits ride a Developer branch.

## SAFE-9 QA whitebox limits
Never edit the Developer's code. Never pass on the Developer's own test report alone; run things yourself.

## SAFE-11 Scratch directories
Make scratch dirs with `mktemp -d`. Never `rm -rf` a bare variable path: write `rm -rf "${VAR:?}"` or a literal path (Claude Code blocks the bare form).

## SUITE-1b Who runs the full suite, M
You run the full suite for the scope, once, on the final sha; Developers and QA blackbox run only the test files they touch. `project.md` may name the runner.

## SUITE-4b Running and receipt, M
Start the run in the background and wait for its completion notice (never `pgrep -f` or `pkill -f`); commit each fix before a run and never restart one. Save the receipt in `$SCOPE_DIR/evidence/`: first line `sha <git rev-parse HEAD> clean=<yes|no>`, ending in the OK line.

## SUITE-5b A failing run, M
When the run fails, `FAIL` the task whose files fail; it counts as a return of that task ([LC-7c]).

## SUITE-3b When it runs, M
Run it once every task of the scope has passed, on the scope's final sha (`--tz` where `project.md` names it): a scope reaches the PO only with a passing run.
