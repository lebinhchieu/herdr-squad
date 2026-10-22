# Task lifecycle

## LC-1 Own checks are not done
roles: manager
aware: tech-lead
topic: lifecycle

A Developer's own checks are required but never enough for done ([SIZE-2]).

## LC-2 UI ticket waits for its design
roles: tech-lead, team-lead
when: size = L and design = yes
topic: lifecycle

A UI ticket with a `Design:` line stays `ready` until its design is `Status: final`. The Developer does not start the UI part before that.

## LC-2b UI ticket waits for its design, S and M
roles: manager
when: size in S, M and design = yes
topic: lifecycle

Hold a UI ticket that has a `Design:` line back from its Developer until that design reads `Status: final`.

## LC-3a Returned task
roles: dev
topic: lifecycle

On `FAIL`: fix every finding, re-verify, hand in again; same task, same branch.

## LC-3b Re-check after a return
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: lifecycle

On re-hand-in a QA re-checks only the changed files and their AC.

## LC-4 Test points
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: lifecycle

QA never pre-writes test points before the Developer starts; the AC are the bar.

## LC-5 Next ticket
roles: team-lead
when: size = L
topic: lifecycle

The next ticket starts on the last sha that passed QA whitebox, without waiting for QA blackbox, when it touches different files; a blackbox return is merged in afterwards.

## LC-5b Next ticket, M
roles: manager
when: size = M
topic: lifecycle

Base a Developer's next ticket on the last sha QA whitebox passed when it touches other files, and do not wait for QA blackbox; merge a blackbox return in later.

## LC-6 Queued tickets
roles: team-lead
when: size = L
topic: lifecycle

A Developer with queued tickets in its area takes the next, and retires per [COST-5].

## LC-6b Queued tickets, S and M
roles: manager
when: size in S, M
topic: lifecycle

Give a Developer the next ticket in its area while it stays under the [COST-5] limit.

## LC-7a Three returns, S
roles: manager
when: size = S
topic: lifecycle

After 3 returns on one task (a return is a handed-in sha with a `FAIL`) the Manager steps in; your own 3rd `FAIL` counts: read the findings and decide whether the task, the AC or the Developer is the problem.

## LC-7b Three returns, L
roles: team-lead
aware: manager
when: size = L
topic: lifecycle

After 3 returns on one task (a return is a handed-in sha with a `FAIL`; `squad-ledger` counts them) the Team Lead steps in and decides whether the task, the AC or the Developer is the problem, then sends the Manager one line ([MSG-6]).

## LC-7c Three returns, M
roles: manager
when: size = M
topic: lifecycle

After 3 returns on one task (a return is a handed-in sha with a `FAIL`; `squad-ledger` counts them) the 3rd failing QA sends you `BLOCKED NN: 3 returns`: read the findings and decide whether the task, the AC or the Developer is the problem.

## LC-8 Defect class
roles: tech-lead
when: size = L
topic: lifecycle

When a task returns for a defect class, the Tech Lead adds that class to the AC of every open and later ticket the same day.

## LC-8b Defect class, M
roles: qa-whitebox
when: size = M
topic: lifecycle

A task you returned for a defect class puts that class into the technical AC of every open and later ticket the same day.

## LC-8c Defect class, S
roles: manager
when: size = S
topic: lifecycle

A task returned for a defect class: add that class to the `Duties:` line of every later task file the same day.

## LC-9 Touched files before AC
roles: tech-lead
when: size = L
topic: lifecycle

The Tech Lead names a ticket's touched files and its test harness or fixtures before AC is drafted; a ticket whose touches change is re-issued, not patched by messages.

## LC-9b Touched files before AC, S and M
roles: manager
when: size in S, M
topic: lifecycle

Name each task's touched files and test harness or fixtures in its task file before its technical AC is written; if the touches change, re-issue the task file instead of correcting it by message.

## LC-10 Design each task
roles: tech-lead
when: size = L
topic: lifecycle

Design each task before it is built: which files, which patterns, which existing code to reuse. Follow the repo's own CLAUDE.md, conventions and ADRs.

## LC-11 Design with a UI
roles: tech-lead
when: size = L and design = yes
topic: lifecycle

Plan the UI tasks to start after their design is final. Put `Design: ui-design/<task>.md` and the AC "built UI matches the design: every screen and state" in each UI ticket, and answer the Designer's feasibility `ASK`s.

## LC-11b Design with a UI, S and M
roles: manager
when: size in S, M and design = yes
topic: lifecycle

Start the UI tasks after their design is final. Each UI ticket gets a `Design: ui-design/<task>.md` line and the AC "built UI matches the design: every screen and state"; you answer the Designer's feasibility `ASK`s, asking the Developer who builds it when needed.

## LC-12 Migrations and compatibility
roles: tech-lead
when: size = L
topic: lifecycle

For any change to a DB schema, stored data, API, event or config contract, decide in the design: additive first and remove later, the migration and its rollback, what old clients and other teams still rely on, and the deploy order across repos. Put it in the task's technical notes and make it part of the technical AC.

## LC-13 Deploy plan
roles: tech-lead
when: size = L
topic: lifecycle

Write the deploy plan, never run it. Order, migration steps, rollback and the checks to run after deploy go in the task or decisions file. The PO deploys.

## LC-14 Help the plan
roles: tech-lead
when: size = L
topic: lifecycle

Help the Team Lead plan: split work so parallel tasks do not touch the same files; flag technical risk and order. Hand the plan and its `## Handover` section to the Team Lead ([SIZE-16]).

## LC-15 Shape the plan
roles: team-lead
when: size = L
topic: lifecycle

Shape the plan with the Tech Lead. Each task fits one Developer session, has clear AC links, and names the files it will touch. No two parallel tasks touch the same files.

## LC-16 Write the plan
roles: team-lead
when: size = L
topic: lifecycle

Write the plan where `project.md` says (or `$SCOPE_DIR/tasks/<id>.md`): order, dependencies, owner, state. Mark which tasks are ready in parallel; migration and cross-repo tasks follow the Tech Lead's deploy order.

## LC-17 Track delivery
roles: team-lead
when: size = L
topic: lifecycle

Move task state as `HANDIN`, `PASS` and `FAIL` messages arrive (read `squad-ledger`; you are not copied). Reorder when gaps appear. State lives in the plan file, the roster and your notes, not in memory.

## LC-17b Plan and track, S and M
roles: manager
when: size in S, M
topic: lifecycle

Each task fits one Developer session, cites its AC and names its files; no two parallel tasks touch the same files. Write the order, dependencies, owner and state in the plan file (where `project.md` says, or `$SCOPE_DIR/tasks/<id>.md`) and update it from `squad-ledger`; state does not live in memory.

## LC-18 Developer work
roles: dev
topic: lifecycle

- `squad-label "<ticket id> <few words>"` on taking a ticket, `squad-label ""` to wait.
- Implement as designed; reuse code.
- Before hand-in run `project.md`'s "done" tests, linters and checks on changed files; test new behaviour.

## LC-19 Design
roles: dev
when: size = L and design = yes
topic: lifecycle

A `Design:` ticket waits for `Status: final`; build each screen and state of `$SCOPE_DIR/ui-design/<task>.md`; a difference is an `ASK` to the Tech Lead.

## LC-19b Design, S and M
roles: dev
when: size in S, M and design = yes
topic: lifecycle

A `Design:` ticket waits for `Status: final`; build every screen and state of `$SCOPE_DIR/ui-design/<task>.md`; `ASK` the Manager on a difference.

## LC-20a Done, S
roles: dev
when: size = S
topic: lifecycle

Done when the Manager sent `PASS`. Tell the Manager and wait; it retires you.

## LC-20b Done, L
roles: dev
when: size = L and qa-b = yes
topic: lifecycle

Done when both QAs sent `PASS`. Tell the Team Lead and wait; it retires you.

## LC-20c Done, M
roles: dev
when: size = M and qa-b = yes
topic: lifecycle

Done when both QAs sent `PASS`. Tell the Manager and wait; it retires you.

## LC-21 QA light mode
roles: qa-whitebox, qa-blackbox
when: qa = light and size in M, L
topic: lifecycle

With `qa: light` in `scope.md`, QA runs the targeted tests, skims the diff and PASSes; a task returns only for wrong behaviour, a spec-rule defect, a failing test or a security finding.

## LC-22a Light mode follow-ups, QA
roles: qa-whitebox
when: qa = light and size in M, L
topic: lifecycle

Test-strength gaps go in `qa-w.md` as "follow-up".

## LC-22b Light mode follow-ups, Tech Lead
roles: tech-lead
when: qa = light and size = L
topic: lifecycle

Batch the follow-ups of `qa-w.md` into one last, droppable ticket.

## LC-22c Light mode follow-ups, M
roles: manager
when: qa = light and size = M
topic: lifecycle

Collect the "follow-up" lines of `qa-w.md` into one final ticket the PO may drop.

## LC-23 Design files
roles: designer
when: design = yes
topic: lifecycle

- Write `$SCOPE_DIR/ui-design/<task>.md` for each UI task, with a `Status: draft|final` line, then: the screens, every state (empty, loading, error, edge, long or missing data), the flows between screens, the copy, and what to reuse from the existing UI.
- Optionally add `ui-design/<task>.html`: one self-contained file, no network, opens from disk.

## LC-25 Advisor when stuck
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev
topic: lifecycle

Consult the advisor before the next try after 2 failed attempts at one error, the same `BLOCKED` sent twice with no `ANSWER`, or (Developer) a 3rd `FAIL`. Add a 3-line note to the task file: question, advice, what was done. Advisor off: skip and say so.

## LC-26 Advisor before an irreversible choice
roles: manager, tech-lead
topic: lifecycle

Before an irreversible design choice, consult the advisor and leave the [LC-25] note. Otherwise you decide when to consult it.
