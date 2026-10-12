# Squad

A self-managing dev team made of Claude Code sessions. One Manager runs the team toward one goal for a human, the PO. Sources: `README.md`, `agents/*.md`, `templates/squad/process.md`.

## People

**PO**:
The human who sets the goal, confirms scope sizes, and alone may merge, push or deploy.
_Avoid_: user, owner, client

**Manager**:
The role that runs the squad: splits the goal into scopes, starts and retires the other roles, and keeps them unblocked. It never does another role's work.
_Avoid_: orchestrator, lead

**BA**:
The role that owns the business need and the business AC of one scope. Present in M and L scopes.
_Avoid_: analyst, product owner

**Team Lead**:
The role that owns the plan (which tasks, in which order, who does each). Present only in L scopes; in S and M the Tech Lead holds this duty.
_Avoid_: project manager, scrum master

**Tech Lead**:
The role that owns technical design, quality and security of one scope. Also owns the plan in S and M.
_Avoid_: architect

**QA whitebox**:
The role that checks a task is built right: reads the diff, runs tests and lint. Agrees the technical AC with the Tech Lead.
_Avoid_: code reviewer, tester

**QA blackbox**:
The role that checks the running app does what the business asked, without reading code. Agrees the business AC with the BA.
_Avoid_: tester, acceptance tester

**Developer**:
The role that builds one task in its own worktree until the checkers pass it.
_Avoid_: engineer, coder

**Token Coach**:
The role started at each retro that finds wasted tokens and proposes `process.md` changes. It never changes anything itself.
_Avoid_: cost bot, optimizer

**Role**:
A job definition, for example BA or Developer.
_Avoid_: persona, type

**Agent**:
One live, named copy of a role. Each agent is a row in the roster.
_Avoid_: session (that is the process behind the agent), bot

## Structure

**Squad**:
One team working on one goal. Several squads can run side by side.
_Avoid_: team, project

**Scope**:
One part of the goal: a feature area, an epic or a group of tickets.
_Avoid_: module, workstream

**Pod**:
The group of agents that delivers one scope. A squad can hold several pods.
_Avoid_: team, squad (a squad is the whole)

**Size**:
How many roles a scope gets: S (Tech Lead + Developers), M (+ BA and both QAs), L (+ Team Lead), XL (several pods). The Manager proposes it, the PO confirms it.
_Avoid_: tier, T-shirt size

**Risk flag**:
A sign that forces a scope to at least size M: data migration, breaking API change, security, or anything another team sees.
_Avoid_: red flag

**Contract**:
An agreement between two scopes in an XL squad, such as an API, an event or a status model.
_Avoid_: interface, spec

## Work

**Iteration**:
One work cycle: goal check, plan, build and verify, retro, check-in.
_Avoid_: sprint

**Goal check**:
The start of an iteration, where the Manager and PO agree the goal and the PO confirms each scope's size.
_Avoid_: kickoff

**Check-in**:
The end of an iteration, where the Manager shows the PO what is done, open escalations and proposed role changes.
_Avoid_: demo, review

**Retro**:
The step after build and verify where the Manager collects friction and the Token Coach proposes savings.
_Avoid_: retrospective meeting

**Task**:
One piece of work for one Developer. It moves ready → building → handed in → checking → done or returned.
_Avoid_: ticket (a ticket lives in the project's own tracker), story

**AC**:
Acceptance criteria a task must pass. **Business AC** is agreed by the BA and QA blackbox; **technical AC** by the Tech Lead and QA whitebox.
_Avoid_: requirements, definition of done

**Done**:
A task is done when its size's checkers pass it: the Tech Lead review in S, both QAs in M and L.
_Avoid_: finished, complete

**Evidence**:
A file that proves a task works, such as a QA report or a Developer's run output.
_Avoid_: proof, report

**Handover**:
A plan section the Tech Lead writes when a scope moves up in size: what was decided, built and left open. Not the same as a HANDIN.
_Avoid_: handoff

**HANDIN**:
The message a Developer sends to QA to give a finished task for checking. Not the same as a Handover.
_Avoid_: submit, handoff

**Escalation**:
A question that waits for the PO, written down by the Manager with options and a recommendation.
_Avoid_: blocker (a blocked agent waits on anything; an escalation waits on the PO)

## Relationships

- A **Squad** has one goal and holds one or more **Pods**.
- A **Pod** delivers exactly one **Scope**; the **Scope**'s **Size** decides which **Roles** the **Pod** has.
- A **Scope** is split into **Tasks**; one **Developer** builds one **Task**.
- A **Task** is **Done** only when the checkers its **Size** names pass it.
