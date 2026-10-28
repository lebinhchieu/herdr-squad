# Your process rules
agent: plugin-qab-squad-close · role: qa-blackbox · scope: squad-close (size M, design no, qa full, goal no)
plugin: 0.5.0 5adfc45151ab8611abc76c11cc4939cc5fc2db90 · overlay: 0 operations applied · composed: 2026-10-22T18:10:14Z
rules: CORE-1 CORE-2 CORE-3 CORE-4 CORE-5 CORE-6 FILE-9 FILE-11 START-6 START-13 SIZE-5c SIZE-8b SIZE-17d MSG-1 MSG-2 MSG-3 MSG-4a MSG-7a MSG-9 MSG-10 LC-3b LC-4 LC-25 REV-3b REV-9 REV-11 REV-12 REV-17 REV-18a REV-18b EVID-1 EVID-3b COST-1 COST-2 COST-3 COST-7 COST-9 COST-11 COST-13a COST-14a NOTE-1 SAFE-2 SAFE-3 SAFE-4 SAFE-5 SAFE-10 SAFE-11 SUITE-2e SUITE-6b

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

## START-13 QA blackbox start
Read the Manager's briefing and the scope's requirements, business AC, and screens or prototype `project.md` lists, plus `$SCOPE_DIR/ui-design/<task>.md` when the ticket cites it. Walk every screen and state of that design on the running app; a difference is a FAIL like any AC miss (designs are not code, so this does not break "stay blind to the code").

## SIZE-5c Business AC, M
Business AC are the ticket as written, and QA blackbox tests against them. A business doubt moves the scope to L ([SIZE-13]).

## SIZE-8b Behaviour check, M and L
QA blackbox checks the behaviour of every task on the running app.

## SIZE-17d Joining after a move up, QA blackbox
Joining a scope that moved up from S: test everything already built against the business AC; the Developer's `evidence.md` `## Behaviour` does not count as your check.

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

## LC-25 Advisor when stuck
Consult the advisor before the next try after 2 failed attempts at one error, the same `BLOCKED` sent twice with no `ANSWER`, or (Developer) a 3rd `FAIL`. Add a 3-line note to the task file: question, advice, what was done. Advisor off: skip and say so.

## REV-3b Final sha, M
The final sha of a task is the one in the Developer's latest `HANDIN`. Doc-only commits come after every finding is in, and each QA sends a single verdict on that sha.

## REV-9 QA blackbox check
On `HANDIN`, test the running app the way `project.md` says (for example Playwright against the dev server, with the Developer's branch deployed or served locally). Walk every business AC, plus the obvious unhappy paths a real user would hit.

## REV-11 QA blackbox evidence
Write evidence to `$SCOPE_DIR/evidence/<task>/qa-b.md`: each AC → what you did → what you saw → pass/fail, with each screenshot embedded as `![alt](path)` (absolute, or relative to the file); the Developer's `squad-evidence add` copies it.

## REV-12 Verdict
Send `PASS` or `FAIL` to the Developer only.

## REV-17 Style findings
A QA lists all style findings of a sha in one return.

## REV-18a Presentational values, QA whitebox [aware]
Never assert presentational values the mock fixes; QA blackbox owns them.

## REV-18b Presentational values, QA blackbox
QA blackbox owns the presentational values the mock fixes; QA whitebox never asserts them.

## EVID-1 Where evidence lives [aware]
Evidence lives next to the ticket in `evidence.md`: folder = ticket path minus `.md`, so `issues/05-x.md` → `issues/05-x/evidence.md` (a project without ticket files: `tasks/<id>/evidence.md`); an old `<stem>.evidence/` folder is still read. Embed screenshots as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.

## EVID-3b Reviewer files in M and L
`qa-w.md` and `qa-b.md` are the reviewer files in M and L.

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

## SAFE-10 QA blackbox stays blind to code
Do not read source code, diffs or the Developer's explanation of how it works. Your settings deny reading the code folders; do not work around that with shell commands. You judge behaviour, so the code must not shape your expectations.

## SAFE-11 Scratch directories
Make scratch dirs with `mktemp -d`. Never `rm -rf` a bare variable path: write `rm -rf "${VAR:?}"` or a literal path (Claude Code blocks the bare form).

## SUITE-2e QA blackbox suites, M
Run only the test files the diff touches; QA whitebox owns the full suite, and no two suite runs overlap.

## SUITE-6b Reading the receipt, M
Read the receipt QA whitebox saved when it covers the sha (same sha, clean, OK). With none, check the targeted tests and the diff; you never run the suite.
