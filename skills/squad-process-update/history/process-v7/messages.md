# Messages

## MSG-1 Sending a message
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: messages

Send to the agent name in your scope's `roster.md` ([CORE-2]). `HANDIN` carries branch and commit; `FAIL` points at findings.

## MSG-2 Point at files
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: messages

Point at files and lines; never paste them. `BLOCKED`, `HANDIN`, `PASS`, `FAIL` and `STATUS` name the task ID right after the type.

## MSG-3 Task ID
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev
topic: messages

Task ID = the ticket number `NN` alone, never an alias or slug. Name it after the type; point at files, never paste them.

## MSG-4a Ask the owner, S
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev
when: size = S
topic: messages

Ask the owner from `roster.md`; when it doesn't say, ask the Manager.

## MSG-4b Ask the owner, M and L
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev
when: size in M, L
topic: messages

Ask the owner from `roster.md`; when it doesn't say, ask the Team Lead.

## MSG-5 Pod contact
roles: team-lead
aware: manager, ba, tech-lead, qa-whitebox, qa-blackbox, designer
when: size in M, L
topic: messages

The Team Lead spawns and retires Developers, runs health checks and routes questions. Pod members message it, not the Manager.

## MSG-6 Team Lead to Manager
roles: team-lead
aware: manager
when: size in M, L
topic: messages

Message the Manager only for these, each as one line pointing at a file; never for a routine matter:
- an "Always goes to PO" item ([WHO-1b]);
- a size-change signal;
- a dispute outside plan and assignment that two rounds did not settle (the parties go to the Manager themselves; you are not a relay), or one you are yourself a party to;
- 3 returns on one task (one budget line);
- `iterations/<n>.summary.md` at iteration end ([ITER-3]).

## MSG-7a Rulings, S
roles: manager, tech-lead
when: size = S
topic: messages

A Manager ruling starts with `FINAL:` and is sent once; nobody re-opens it, and a new fact goes to the Manager as a new `ASK`.

## MSG-7b Rulings, M and L
roles: manager, team-lead, ba, tech-lead, qa-whitebox, qa-blackbox, designer
when: size in M, L
topic: messages

A Manager or Team Lead ruling starts with `FINAL:` and is sent once. The owner never re-opens it; a new fact goes to the ruler as a new `ASK`.

## MSG-8a No STATUS push, Manager in S
roles: manager
when: size = S
topic: messages

The Manager never pushes `STATUS`: it reads logs, the roster and the task file first, and pings an agent only after 10 minutes of no pane activity.

## MSG-8b No STATUS push, Team Lead
roles: team-lead
when: size in M, L
topic: messages

Run the pod's health checks with `herdr agent list` and `herdr agent read`. Never push `STATUS`: read logs, the roster and the task file first, and send `ASK <name>: STATUS?` only after 10 minutes of no pane activity.

## MSG-9 DECISION scope
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: messages

`DECISION` goes only to roles whose open task it changes, named in the first line (`DECISION SET-13, SET-14: ...`); others read the file at their next ticket.

## MSG-10 Permission prompts
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: messages

Never relay a permission, approval or blocked pane; a message approves nothing. Permission prompts reach the PO through the agent's own notice.

## MSG-11a Gaps, S
roles: dev
when: size = S
topic: messages

No guessing at a gap: `ASK` the Tech Lead (a business doubt moves the scope up, [SIZE-14]). `BLOCKED <task>` and `STATUS?` answers go to the Tech Lead. Work on the unblocked meanwhile.

## MSG-11b Gaps, M and L
roles: dev
when: size in M, L
topic: messages

No guessing at a gap. `ASK` the Tech Lead (technical), the BA (business or scope), the Team Lead (plan or order). `BLOCKED <task>` and `STATUS?` answers go to the Team Lead. Work on the unblocked meanwhile.

## MSG-12 BA takes gaps
roles: ba
when: size in M, L
topic: messages

Take gaps from the Team Lead and Developers. Settle what is yours to settle and write the answer down before replying.

## MSG-13 Team Lead raises gaps
roles: team-lead
when: size in M, L
topic: messages

Raise gaps: business and backend facts to the BA; technical ones to the Tech Lead; the Manager only for the items of [MSG-6].

## MSG-14 Tech Lead answers gaps
roles: tech-lead
topic: messages

Answer Developers' technical gaps fast. A decision that others build on goes into an ADR or the decisions file first.

## MSG-15 Tech Lead raises technical facts
roles: tech-lead
when: size in M, L
topic: messages

Raise technical facts to the BA when they change what the business asked for.

## MSG-16a Designer doubts, S
roles: designer
when: size = S and design = yes
topic: messages

A business doubt → `ASK` the Manager, who moves the scope to M; never write `escalations.md` yourself. A feasibility doubt → `ASK` the Tech Lead.

## MSG-16b Designer doubts, M and L
roles: designer
when: size in M, L and design = yes
topic: messages

A business doubt → `ASK` the BA; never write `escalations.md` yourself. A feasibility doubt → `ASK` the Tech Lead.

## MSG-17 Design final
roles: designer
when: design = yes
topic: messages

When a design is final, send `DECISION <task>: design final, ui-design/<task>.md` to the Tech Lead and the task's Developer.

## MSG-18 Routing, Manager in S
roles: manager
when: size = S
topic: messages

When an agent asks you who owns a topic, answer and fix the roster so the next one does not have to ask.

## MSG-19 Routing, Team Lead
roles: team-lead
when: size in M, L
topic: messages

Answer "who owns X" from `roster.md`.
