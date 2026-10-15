# Squad

A self-managing dev team made of Claude Code sessions. For each request from a human, the PO, a fresh Manager runs the work as one scope or one goal. Sources: `README.md`, `agents/*.md`, `templates/squad/process.md`.

## People

**PO**:
The human who makes the requests, confirms scope sizes, and alone decides a merge (the Manager runs it on request), a push or a deploy.
_Avoid_: user, owner, client

**Manager**:
The role that runs one scope (a lone task) or one goal (several scopes): sizes the work, starts and retires the other roles, and keeps them unblocked. It starts fresh for each request and never does another role's work. The one running a goal is the **goal Manager**.
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

**UI/UX Designer**:
The role that delivers a design (screens, states, flows, optional HTML prototype) for a scope's UI tasks before they are built. It joins only when the PO sets `design: yes`, delivers a design only, and does not check the built UI.
_Avoid_: UX, designer (alone), design reviewer

**Developer**:
The role that builds one task in its own worktree until the checkers pass it.
_Avoid_: engineer, coder

**Token Coach**:
The role started when an M or L scope or a goal closes, that finds wasted tokens and proposes `process.md` changes. It never changes anything itself.
_Avoid_: cost bot, optimizer

**Role**:
A job definition, for example BA or Developer.
_Avoid_: persona, type

**Agent**:
One live, named copy of a role. Each agent is a row in the roster.
_Avoid_: session (that is the process behind the agent), bot

## Structure

**Squad**:
The standing setup of one project or module: how the team works (`process.md`, settings) and where the project's truth lives (`project.md`). It holds many scopes and goals over time, and several squads can run side by side.
_Avoid_: team, project

**Scope**:
The unit of work and of freshness: one task or one part of a goal. It has its own folder, a fresh pod, and closes with one move. A lone scope shares nothing with other scopes.
_Avoid_: module, workstream

**Pod**:
The group of agents that delivers one scope.
_Avoid_: team, squad (a squad is the whole)

**Size**:
How many roles a scope gets: S (Tech Lead + Developers), M (+ BA and both QAs), L (+ Team Lead). The Manager proposes it, the PO confirms it. Bigger work is a goal.
_Avoid_: tier, T-shirt size

**Risk flag**:
A sign that forces a scope to at least size M: data migration, breaking API change, security, or anything another team sees.
_Avoid_: red flag

**Contract**:
An agreement between two scopes of one goal, such as an API, an event or a status model, kept in the goal's `shared/contracts/`.
_Avoid_: interface, spec

**Process version**:
The integer on the line `process-version: <N>` in a squad's `process.md`. A squad without the line is version 1. The plugin's template carries the current version; a squad is *behind* when its number is lower.
_Avoid_: schema version, template version

**Section view**:
What `squad-process show <role>` prints for a role: its sections of `process.md` plus the title section, from the same one file. Manager and Tech Lead read the whole file.
_Avoid_: split file, role copy

**Process changelog**:
The plugin's list of changes to the `process.md` template, one `##` per version and one `###` item per change (sections, kind, why, old and new wording), next to a pristine copy of every released version. The update reads it.
_Avoid_: release notes

**Process update**:
The skill `/squad:squad-process-update`. It shows the PO what a squad's `process.md` would become (the plugin's changes combined with the squad's own edits), and writes it only after the PO confirms the whole result.
_Avoid_: migration (that word is `squad-migrate`, for folder layouts)

## Goals and knowledge

**Request**:
What the PO asks for with `squad-start`: a lone task (one scope) or a goal.
_Avoid_: ticket, order

**Goal**:
A request with several scopes, run by one goal Manager. Its folder holds `goal.md` and `shared/`. Only the scopes of one goal share anything.
_Avoid_: epic, project

**Shared folder**:
A goal's `shared/`: `decisions.md` (goal-wide decisions and domain facts), a summary per closed scope, and contracts. Every role of every scope in the goal reads it.
_Avoid_: goal memory, knowledge base

**Promotion**:
Writing what must outlive a scope or goal into the project's own docs, through a reviewed task. A lone scope promotes at its close; a goal once, at its close. The squad keeps no domain knowledge.
_Avoid_: export, archiving

**Stacked branch**:
A branch that builds on a passed but unmerged branch, so a later scope of a goal need not wait for the PO's merge.
_Avoid_: dependent branch

**Integration task**:
The last task of a scope with several tasks: a Developer merges the scope's passed branches into its own branch and runs the full suite.
_Avoid_: merge task

## Work

**Iteration**:
One work cycle inside a scope: goal check, plan, build and verify, retro, check-in. A scope can have several.
_Avoid_: sprint

**Goal check**:
The start of an iteration, where the Manager and PO agree the iteration's goal and the PO confirms the scope's size.
_Avoid_: kickoff

**design flag**:
The `design: yes|no` line in `scope.md`, default `no`. Only the PO's request turns it on, and the Manager never proposes it. It adds the UI/UX Designer to a scope of any size.

**Check-in**:
The end of an iteration, where the Manager shows the PO what is done, open escalations and proposed role changes.
_Avoid_: demo, review

**Retro**:
The step after build and verify where the Manager collects friction. The Token Coach proposes savings when an M or L scope or a goal closes.
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

## Squad board

The local page that shows a squad live (`bin/squad-board`, `bin/squad-board.html`, guide `docs/squad-board-guide.html`). Sources: `docs/adr/`, `.scratch/squad-board/`.

**Home**:
A folder with its own roster, escalations, logs, `iterations/` and `roles/`: `goals/<g>/` or `scopes/<s>/` in a per-scope squad, the squad folder itself in a flat one. The board reads every home and merges them.
_Avoid_: folder, workspace

**Bar**:
One working stretch of one agent, drawn on the sequence. `working_s` is the bar minus its waiting parts (blocked time stays in it).
_Avoid_: session, span

**Status**:
An agent's state, one of `working`, `idle`, `blocked`, `waiting`. `waiting` is an idle agent whose last pane line shows a background shell or monitor.
_Avoid_: state (that is the task's word)

**Needs-you**:
The list of what waits on the PO: a blocked agent, an unanswered escalation, an idle Manager with an empty check-in.

**Recorder**:
The thread that polls idle and done panes on the herdr socket and writes `activity.jsonl`. It runs only while the board runs.

**Replay**:
Serving a copy of a squad folder at a fixed `--now` instead of live data. Tests and QA use it.

**Receipt**:
The proof of one full test run on the final sha: `suite-default.txt` and `suite-tz.txt` in the ticket's evidence folder, made by `tests/run_suite.py --receipt`.

## Relationships

- A **Squad** holds many **Scopes** and **Goals** over time, each with its own folder and fresh **Manager** (a **Goal** has one **goal Manager** for all its **Scopes**).
- A **Pod** delivers exactly one **Scope**; the **Scope**'s **Size** decides which **Roles** the **Pod** has.
- A **Scope** is split into **Tasks**; one **Developer** builds one **Task**.
- A **Task** is **Done** only when the checkers its **Size** names pass it.
- A **Home** belongs to one **Goal** or **Scope**; a **Bar** is drawn in the **Home** its start row came from.
