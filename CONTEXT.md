# Squad

A self-managing dev team made of Claude Code sessions. For each request from a human, the PO, a fresh Manager runs the work as one scope or one goal. Sources: `README.md`, `agents/*.md`, `templates/squad/process.md`.

## People

**PO**:
The human who makes the requests, confirms scope sizes, and alone decides a merge (the Manager runs it on request), a push or a deploy.
_Avoid_: user, owner, client

**Manager**:
The role that runs one scope (a lone task) or one goal (several scopes): sizes the work, starts and retires the other roles (in M and L the Team Lead starts and retires the Developers) and keeps them unblocked (in M and L the Team Lead keeps the pod unblocked). It starts fresh for each request and never does another role's work. The one running a goal is the **goal Manager**.
_Avoid_: orchestrator, lead

**BA**:
The role that owns the business need and the business AC of one scope. Present in M and L scopes.
_Avoid_: analyst, product owner

**Team Lead**:
The role that owns the plan (which tasks, in which order, who does each) and runs the pod in M and L scopes: spawns and retires the Developers, checks on the pod, routes its questions, and is the pod's **single point of contact**. Takes the plan from the Tech Lead. Present in M and L scopes.
_Avoid_: project manager, scrum master

**Single point of contact**:
In an M or L scope, the role every pod member messages for routine matters: the Team Lead. The Manager hears from it only an escalation to the PO, a size-change signal, a dispute the pod could not settle, 3 returns on one task and one summary per iteration (`iterations/<n>.summary.md`).
_Avoid_: relay, gateway

**Manager traffic**:
The four things the Manager hears from an M or L pod: an escalation to the PO, a size-change signal, a dispute the pod could not settle, and the iteration summary; plus one line when a task has had 3 returns.
_Avoid_: status, relay

**Tech Lead**:
The role that owns technical design, quality and security of one scope. Owns the plan in S; in M and L the Team Lead takes it.
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
How many roles a scope gets: S (Tech Lead + Developers), M (+ BA, both QAs and Team Lead), L (the same roles as M; it differs only in the signals that call for it). The Manager proposes it, the PO confirms it. Bigger work is a goal.
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
What `squad-process show <role>` prints for a role: its sections of `process.md` plus the title section, from the same one file. Every other role reads the whole file.
_Avoid_: split file, role copy

**Process changelog**:
The plugin's list of changes to the `process.md` template, one `##` per version and one `###` item per change (sections, kind, why, old and new wording), next to a pristine copy of every released version. The update reads it.
_Avoid_: release notes

**Process update**:
The skill `/squad:squad-process-update`. It shows the PO what a squad's `process.md` would become (the plugin's changes combined with the squad's own edits), and writes it only after the PO confirms the whole result.
_Avoid_: migration (that word is `squad-migrate`, for folder layouts)

**Home**:
A folder with its own roster, escalations, logs, `iterations/` and `roles/`: `goals/<g>/` or `scopes/<s>/` in a per-scope squad, the squad folder itself in a flat one.
_Avoid_: folder, workspace

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
The last task of a scope with several tasks: a Developer merges the scope's passed branches into its own branch and runs the targeted tests; the Tech Lead then runs the full suite.
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
A question that waits for the PO, written down by the Manager with options and a recommendation. An escalation is an answer item of the inbox; `escalations.md` stays the store of answer items.
_Avoid_: blocker (a blocked agent waits on anything; an escalation waits on the PO)

**Cost-weighted unit**:
Dollars at list price per model for input, cache read, cache write (5m, 1h) and output tokens.
_Avoid_: token count

**Real token saving**:
A change measured in cost-weighted units that saves at least 2% of total net squad spend, with no QA-AC regression. Net means after the cost the change adds. Below the bar it is "minor" or "unproven", never recommended.
_Avoid_: saving (unmeasured)

**Receipt**:
The proof of the Tech Lead's one full test run on the final sha: `suite-default.txt` and `suite-tz.txt` in the ticket's evidence folder, made by `tests/run_suite.py --receipt`.

## PO inbox

**Inbox**:
The PO-facing list in a Manager's session (a mod of the squad plugin): what the Manager needs the PO to read or answer, apart from the working chat. One per Manager home (a scope or a goal). Sources: `.scratch/po-inbox/`, `docs/adr/0007-inbox-sits-on-escalations.md`.
_Avoid_: notifications, todo list

**Item**:
One entry of the inbox, with a short id (`E3`, `R1`). A **read item** is for reading and is cleared by "mark read"; it lives in `inbox.jsonl` in the Manager's home. An **answer item** needs a decision or reply and is a row of `escalations.md`. Only the Manager writes items.
_Avoid_: message (a message is a `SendMessage`), ticket, task

**Structured body**:
An item's body drawn from a small markdown subset (headings, bullets, numbered lists, bold, code, fenced code, pipe tables, a leading `[rec]` tag); anything else shows as plain text. Display only: stored text and the PO's answer are never changed.

**Recommended option**:
The option whose key the Manager's `--rec` text starts with, exactly one existing key like `(c)`; marked "recommended". When the text names no key, several keys or an unknown key, no option is marked and the recommendation shows as its own line.

**Colour meaning**:
In the inbox green = passed, recommended, delivered; red = blocks work, failed, error; amber = warning, waiting, not verified; dim = metadata. One meaning per colour on every screen, as theme keys (`success`, `error`, `warning`, dim), never RGB; structure is carried by weight and shape, and meaning is never by colour alone. `blocks X` is red while the work is still blocked (open, or answered and waiting) and dim once released (delivered, answered in chat, withdrawn, read).

## Claude accounts

**Account launcher**:
One of the PO's shell commands that starts Claude Code on one of three Claude accounts: `c1`, `c2`, `c3`, `c` (the default account), plus `cswitch` and `cautoswitch` (bash only). Kept in `tools/claude-accounts/`; it is the PO's tooling, not a squad Role, and nothing in the plugin runs it.
_Avoid_: account script, switcher

**Global default**:
The account `c` and a plain shell use when no Workspace default applies; the one-digit file `default` in `~/.claude-accounts`, set by `cdefault 1|2|3`. Anything that is not 1, 2 or 3 reads as 1.
_Avoid_: default account (alone)

**Workspace default**:
The account a herdr workspace uses, kept as one file `workspace-default/<workspace id>` holding `1`, `2` or `3`. It wins over the Global default only inside herdr (`HERDR_ENV=1` and a valid id: `w` plus letters and digits). `c1`, `c2` and `c3` write it for the current workspace; `cdefault --ws [<id|panel number|label>] <1|2|3>` writes it for any workspace; files of workspaces herdr no longer lists are removed on the next write.
_Avoid_: pane default, per-tab default

**Account token**:
The display-only mark `account=c<N>` the launchers report to herdr for a workspace, shown in the spaces panel. A failed report is ignored; it never changes what a launcher does.
_Avoid_: badge, label

**Account install**:
`tools/claude-accounts/install.sh`, which the PO runs after merging: it makes `~/.claude-accounts` a real directory of per-file symlinks to the main checkout, links the skill folder, and leaves the state files (`default`, `workspace-default/`, `usage-*`, `cswitch.log`) alone.
_Avoid_: setup, deploy

## Squad report

**Elapsed**:
Wall clock from the scope's first event to its last.
**Agent-time**:
The sum over agents of their time in the four buckets.
**Parallelism**:
Agent-time / elapsed. A report never shows a bare "time": it says which.
**Bucket**:
Working / waiting / blocking / idle; sum of a scope's buckets = agent-time exactly (integer seconds). Working: model or tool running. Waiting: long tool call or background job. Blocking: BLOCKED/ASK sent, reply not yet in; or an escalation to the PO open. Idle: waiting for work from a peer, or for the PO's typed chat reply. A gap is classified by what ends it, not by its length; 5 min is only a stall guard.
**Digest**:
Up to 8 ranked signals inside `data.json`, the only part the analyze skill reads without a query.
**Attribution layer**:
How a second of agent-time got its task (message, branch, overhead).
**PO wait**:
An escalation open (`inbox.jsonl` `seen` to `answer`). Reported as elapsed intervals (count, total, longest), never as agent cost; any agent's time inside it is bucketed blocking with reason `po`. Agents sitting between the PO's typed chat messages with no escalation open are idle, reason "waiting for your chat reply", shown as a sub-line under idle.
**Review wait**:
A task's HANDIN to its PASS/FAIL verdict.
**Return**:
One FAIL message (label "returns (FAIL messages)": the Manager's own count can differ by one when a return came in another wording).
**Rework**:
FAIL to the task's next HANDIN (time and cost).
**Returns banner**:
The 3-return banner (`N task(s) reached 3 or more returns (Task 04: 3) of T in all`) counts tasks at 3 or more returns and gives each task's own count; the Returns KPI (T) counts all FAIL messages; every place showing a task's returns shows the same number.
**Closed scope**:
Never shows "still running"/partial, and never "no transcript" for an agent whose transcript exists; only agents with really no transcript are named.
**Worth-a-look reason**:
A return reason cut at 120 characters plus "…"; the full reason (≤ 200) is in the task drawer.
**Design check**:
The report is checked against the design mock per screen and state at 1440, 700 and 400 px: layout, copy, order and colour tokens, not pixel diff.
**Returned reason**:
The headline of the FAIL message (first line, cut to 200 characters), who returned it, and the pointer to the task's QA evidence file where the full findings are. Not classified (no LLM).
**`data.json`**:
The one shareable file of a scope. A teammate can send it; the PO's rollup reads only such files (no scope folder, no transcripts). A scope is identified by squad name + scope name.
**Task** (in a report):
A ticket id seen in messages/roster (e.g. `16`).
**Scope overhead**:
Agent-time and cost not attributable to any task.
**% attributed**:
Attributed non-idle seconds / non-idle seconds, i.e. working+waiting+blocking; cost share shown beside it; always shown; banner when under 60%.
**Derived**:
Every time figure in a report. **Estimated, list price**: every dollar figure. Labelled on the page.

## Relationships

- A **Squad** holds many **Scopes** and **Goals** over time, each with its own folder and fresh **Manager** (a **Goal** has one **goal Manager** for all its **Scopes**).
- A **Pod** delivers exactly one **Scope**; the **Scope**'s **Size** decides which **Roles** the **Pod** has.
- A **Scope** is split into **Tasks**; one **Developer** builds one **Task**.
- A **Task** is **Done** only when the checkers its **Size** names pass it.
- A **Home** belongs to one **Goal** or **Scope**.
- An **Inbox** shows the open **Escalations** of its **Home** (answer items) and its own read items; the PO's answer is written into the escalation's Answer cell.
- Rendering never drops or changes the Manager's or the PO's text: unknown markup shows as plain text and every word stays reachable.
- An **Account launcher** starts Claude Code on one account; the **Workspace default**, inside herdr, else the **Global default**, decides which one `c` picks, and the launchers report an **Account token** for the workspace.
