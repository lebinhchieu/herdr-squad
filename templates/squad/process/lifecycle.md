# Task lifecycle

## LC-1 Own checks are not passed
roles: manager
aware: tech-lead
topic: lifecycle

A Developer's own checks are required but never enough to pass ([SIZE-2]).

## LC-2 UI ticket waits for its design
roles: team-lead
aware: tech-lead
when: design = yes
topic: lifecycle

A UI ticket with a `Design:` line stays `ready` until its design is `Status: final`. The Developer does not start the UI part before that.

## LC-3a Returned task
roles: dev
topic: lifecycle

On `FAIL`: fix every finding, re-verify, hand in again, same branch.

## LC-3b Re-check after a return
roles: qa-whitebox, qa-blackbox
when: handin-target = qas
topic: lifecycle

On re-hand-in a QA re-checks only the changed files and their AC.

## LC-4 Test points
roles: qa-whitebox, qa-blackbox
when: handin-target = qas
topic: lifecycle

QA never pre-writes test points before the Developer starts; the AC are the bar.

## LC-5 Next ticket
roles: team-lead
when: qa-black = yes
topic: lifecycle

The next ticket starts on the last sha that passed the code check, without waiting for QA blackbox, when it touches different files; a blackbox return is merged in afterwards.

## LC-6 Queued tickets
roles: team-lead
topic: lifecycle

A Developer with queued tickets in its area takes the next, and retires per [COST-5].

## LC-6c Bundle small tickets
roles: manager, team-lead
topic: lifecycle

The Team Lead may give one Developer 2-3 tickets of at most 2 files each, all different files. One `HANDIN` lists each ticket and sha; both QAs check every ticket in one pass and send one verdict line per ticket. A `FAIL` returns only the failed ticket.

## LC-7b Three returns, Team Lead
roles: team-lead
aware: manager
topic: lifecycle

After 3 returns on one task (a return is a handed-in sha with a `FAIL`; `squad-ledger` counts them) the Team Lead steps in and decides whether the task, the AC or the Developer is the problem, then sends the Manager one line ([MSG-6]).

## LC-7c Three returns, QA
roles: qa-whitebox, qa-blackbox
when: handin-target = qas
topic: lifecycle

After 3 returns on one task (a return is a handed-in sha with a `FAIL`; `squad-ledger` counts them) the 3rd failing QA sends the Team Lead `BLOCKED NN: 3 returns`.

## LC-8 Defect class
roles: tech-lead
when: tech-ac = tech-lead
topic: lifecycle

When a task returns for a defect class, the Tech Lead adds that class to the AC of every open and later ticket the same day.

## LC-8b Defect class, QA whitebox
roles: qa-whitebox
when: tech-ac = qa-white
topic: lifecycle

A task you returned for a defect class puts that class into the technical AC of every open and later ticket the same day.

## LC-8c Defect class, Developer
roles: manager
when: tech-ac = dev
topic: lifecycle

A task returned for a defect class: add that class to the `Duties:` line of every later task file the same day.

## LC-9 Touched files before AC
roles: tech-lead
when: design-notes = tech-lead
topic: lifecycle

The Tech Lead names a ticket's touched files and its test harness or fixtures before AC is drafted; a ticket whose touches change is re-issued, not patched by messages.

## LC-9b Touched files before AC, Manager
roles: manager
when: design-notes = dev
topic: lifecycle

Name each task's touched files and test harness or fixtures in its task file before its technical AC is written; if the touches change, re-issue the task file instead of correcting it by message.

## LC-9c Ticket opens with a picture
roles: manager, tech-lead, ba, architect
topic: lifecycle

A ticket opens with a picture when its change has a shape (wireframe, `diagram` fence of at most 44 columns, item-by-place table, before / after block); a rule or test fix needs none. Problem: at most 3 sentences plus the picture; details go in Change or AC. Start from `templates/squad/ticket.md`.

## LC-10 Design each task
roles: tech-lead
when: design-notes = tech-lead
topic: lifecycle

Design each task before it is built: which files, which patterns, which existing code to reuse. Follow the repo's own CLAUDE.md, conventions and ADRs.

## LC-11 Design with a UI
roles: tech-lead
when: tech-lead = yes and design = yes
topic: lifecycle

Plan the UI tasks to start after their design is final. Put `Design: ui-design/<task>.md` and the AC "built UI matches the design: every screen and state" in each UI ticket, and answer the Designer's feasibility `ASK`s.

## LC-11d Tickets after the architecture, Team Lead
roles: team-lead
when: architecture = yes
topic: lifecycle

Assign tickets only after `architecture.md` reads `Status: final`; check that each ticket's AC says "conforms to `architecture.md`".

## LC-11e Design inside the architecture
roles: tech-lead
when: tech-lead = yes and architecture = yes
topic: lifecycle

Design each task inside `architecture.md` and answer the Architect's feasibility `ASK`s.

## LC-12 Migrations and compatibility
roles: tech-lead
when: risk-owner = tech-lead
topic: lifecycle

For any change to a DB schema, stored data, API, event or config contract, decide in the design: additive first and remove later, the migration and its rollback, what old clients and other teams still rely on, and the deploy order across repos. Put it in the task's technical notes and make it part of the technical AC.

## LC-13 Deploy plan
roles: tech-lead
when: risk-owner = tech-lead
topic: lifecycle

Write the deploy plan, never run it. Order, migration steps, rollback and the checks to run after deploy go in the task or decisions file. The PO deploys.

## LC-14 Help the plan
roles: tech-lead
aware: manager
when: tech-lead = yes
topic: lifecycle

Help the Manager plan: write each task's dependencies, touched files, parallel-safe groups and technical risks in a file under `tasks/`, with the `## Handover` section ([SIZE-16]). For each ticket that deletes or moves files, list the tickets that read them; a reader goes before its deleter. Send the Manager one line pointing at the file, Team Lead on copy.

## LC-15 Shape the plan
roles: team-lead
topic: lifecycle

Check that each task in the Manager's plan fits one Developer session, has clear AC links, and names the files it will touch, with no two parallel tasks on the same files; an `ASK` to the Manager fixes a gap.

## LC-16 Write the plan
roles: team-lead
topic: lifecycle

Write each `tasks/<id>.md` from the Manager's plan, in the plan's order and with its dependencies, owner and state. Mark which tasks are ready in parallel; migration and cross-repo tasks follow the deploy order in their task or decisions file ([LC-13]).

## LC-17 Track delivery
roles: team-lead
topic: lifecycle

Move task state as `HANDIN`, `PASS` and `FAIL` messages arrive (read `squad-ledger`; you are not copied). You never reorder the plan: when a gap needs a new order, send the Manager an `ASK`. State lives in the plan file, the roster and your notes, not in memory.

## LC-18 Dev work
roles: dev
topic: lifecycle

- `squad-label "<ticket id> <few words>"` on taking a ticket, `squad-label ""` to wait.
- Implement as designed; reuse code; test new behaviour.
- Before hand-in run `project.md`'s "done" tests, linters and checks on changed files.

## LC-19 Design
roles: dev
when: design-notes = tech-lead and design = yes
topic: lifecycle

A `Design:` ticket waits for `Status: final`; build each screen and state of `$SCOPE_DIR/ui-design/<task>.md`; differences: `ASK` the Tech Lead. Shots: [EVID-5].

## LC-19b Design, Manager answers
roles: dev
when: design-notes = dev and design = yes
topic: lifecycle

A `Design:` ticket waits for `Status: final`; build every screen and state of `$SCOPE_DIR/ui-design/<task>.md`; `ASK` the Manager on a difference. Shots: [EVID-5].

## LC-19c Architecture
roles: dev
when: architecture = yes
topic: lifecycle

Build inside `$SCOPE_DIR/architecture.md`; a difference: `ASK` the Architect; unsettled after 2 rounds: the Manager.

## LC-20b Passed, QAs
roles: dev
when: handin-target = qas
topic: lifecycle

On every `PASS` send the Team Lead `STATUS NN: passed <sha>`; stay until the Team Lead retires you ([LC-20f]).

## LC-20f Retire after the evidence check, Team Lead
roles: team-lead
when: handin-target = qas
topic: lifecycle

Keep the Developer until both checkers sent `PASS` and its evidence commit is in. Run `squad-evidence check <folder>` on the final sha; only on exit 0 retire it and record `STATUS <task>: passed`, quoting the exit code and sha.

## LC-20e Passed, Team Lead alone
roles: dev
when: handin-target = team-lead
topic: lifecycle

At `HANDIN` send `STATUS NN: passed <sha>`; it retires you.

## LC-21 QA light mode
roles: qa-whitebox, qa-blackbox
when: qa = light and handin-target = qas
topic: lifecycle

With `qa: light` in `scope.md`, QA runs the targeted tests, skims the diff and PASSes; a task returns only for wrong behaviour, a spec-rule defect, a failing test or a security finding.

## LC-22a Light mode follow-ups, QA
roles: qa-whitebox
when: qa-white = yes and qa = light
topic: lifecycle

Test-strength gaps go in `qa-w.md` as "follow-up".

## LC-22b Light mode follow-ups, Team Lead
roles: team-lead
when: qa = light
topic: lifecycle

Batch the follow-ups of `qa-w.md` into one last, droppable ticket.

## LC-23 Design files
roles: designer
when: design = yes
topic: lifecycle

- Write `$SCOPE_DIR/ui-design/<task>.md` for each UI task, with a `Status: draft|final` line, then: the screens, every state (empty, loading, error, edge, long or missing data), the flows between screens, the copy, and what to reuse from the existing UI.
- Optionally add `ui-design/<task>.html`: one self-contained file, no network, opens from disk.

## LC-25 Advisor
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, dev
topic: lifecycle

Consult the advisor before the next try after 2 failed tries at one error, 2 unanswered `BLOCKED`, or (Developer) a 3rd `FAIL`. Note it in the task file, 3 lines: question, advice, what was done. Advisor off: say so.

## LC-26 Advisor before an irreversible choice
roles: manager, tech-lead
topic: lifecycle

Before an irreversible design choice, consult the advisor and leave the [LC-25] note. Otherwise you decide when to consult it.

## LC-27 Task record and gates
roles: manager, team-lead, tech-lead, qa-whitebox, qa-blackbox
topic: lifecycle

- A hook records each ticket's state; only `merged` is done, `passed` is not. Gates warn, never block: fix the cause of a warning. One exception: the HANDIN gate ([EVID-0]) refuses a hand-in whose evidence check fails.
- `passed` = every QA on the roster sent `PASS` for the current sha. A `PASS` from anyone else warns and is not counted.
- No QA on the team: the `HANDIN` hook runs `squad-evidence check`. Exit 0 is `passed`; else a warning, and the ticket stays `in progress`.
- A step the hook missed: `squad-task claim|handin|pass|fail|blocked|merged NN`; `squad-task passed NN` overrides and warns.

## LC-28 Hold a task for an open PO question
roles: manager, team-lead
topic: lifecycle

A task waits while an open `ASK` to the PO changes it, or its open part becomes a later ticket. When a `PASS` lists choices for the PO, ask the PO before you retire the Developer, 45 minutes at most; the PO's fix on that unmerged branch is a return ([CORE-1]).
