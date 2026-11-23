# Squad

A self-managing dev team made of Claude Code sessions. For each request from a human, the PO, a fresh Manager runs the work as one scope or one goal. Sources: `README.md`, `agents/*.md`, `templates/squad/process/`.

## People

**PO**:
The human who makes the requests, confirms each scope's team, and alone decides a merge (the Manager runs it on request), a push or a deploy.
_Avoid_: user, owner, client

**Manager**:
The role that runs one scope (a lone task) or one goal (several scopes): proposes the team, owns the plan (which tasks, their order, the iteration goal) and settles disputes. The Manager spawns the Team Lead and, at the close, the Token Coach; the Team Lead spawns, respawns and retires the rest of the pod and keeps it unblocked (ADR 0032). It starts fresh for each request and never does another role's work. The one running a goal is the **goal Manager**.
_Avoid_: orchestrator, lead

**BA**:
The role that owns the business need and the business AC of one scope. Optional: on the team when the Manager proposes it and the PO confirms.
_Avoid_: analyst, product owner

**Team Lead**:
The **Coordinator** of the pod, always on the team: spawns, respawns and retires every pod role on `team:` and the Developers (never the Manager, the Token Coach or another Team Lead, ADR 0032), assigns tasks per the Manager's plan, tracks STATUS messages and the ledger, checks on the pod, routes its questions, and is the pod's **single point of contact**. Never reorders the plan (ADR 0030).
_Avoid_: project manager, scrum master

**Coordinator**:
The Team Lead's role: spawns, respawns and retires the pod and the Developers, assigns tasks per the plan, tracks STATUS and the ledger, health-checks the pod, escalates to the Manager only on fixed triggers, and never reorders the plan. Always on the team (ADR 0030).
_Avoid_: scheduler, project manager

**Plan owner** (retired):
Was the role that owned the plan, a Team Lead or, without one, the Manager (the `plan-owner` duty). Retired by ADR 0030: the Manager owns the plan, the Team Lead coordinates.

**Single point of contact**:
The role every pod member messages for routine matters: the Team Lead. The Manager hears from it only an escalation to the PO, a team-change signal, a dispute the pod could not settle, 3 returns on one task and one summary per iteration (`iterations/<n>.summary.md`).
_Avoid_: relay, gateway

**Manager traffic**:
The four things the Manager hears from the Team Lead: an escalation to the PO, a team-change signal, a dispute the pod could not settle, and the iteration summary; plus one line when a task has had 3 returns.
_Avoid_: status, relay

**Tech Lead**:
The role that owns technical design, quality and security of one scope. Its task dependencies go into the plan the Manager owns. Optional. With `architecture: yes` its per-task design stays inside the **Architect**'s `architecture.md`.

**QA whitebox**:
The role that checks a task is built right: reads the diff, runs tests and lint. Agrees the technical AC with the Tech Lead, else with the Developer. Optional; its team key is `qa-white`.
_Avoid_: code reviewer, tester

**QA blackbox**:
The role that checks the running app does what the business asked, without reading code. Agrees the business AC with the BA; with no BA the ticket is the AC. Optional; its team key is `qa-black`.
_Avoid_: tester, acceptance tester

**UI/UX Designer**:
The role that delivers a design (screens, states, flows, optional HTML prototype) for a scope's UI tasks before they are built. It joins only when the PO confirms it for the team (`designer`), delivers a design only, and does not check the built UI.
_Avoid_: UX, designer (alone), design reviewer

**Architect**:
The role that designs a scope's architecture before the plan: components, boundaries, contracts, constraints, and the list of irreversible choices with options and a recommendation. It writes `architecture.md` and ADR drafts, never code, and checks no built code. It joins only when the PO confirms it for the team (`architect`), sits above the Tech Lead and, with none, above the Developer's design notes, proposes irreversible choices but never decides them (the PO does), and retires once `architecture.md` is `Status: final`.
_Avoid_: system designer, tech lead (the Tech Lead owns per-task design, quality and security inside the architecture)

**Developer**:
The role that builds one task in its own worktree until the checkers pass it.
_Avoid_: engineer, coder

**Token Coach**:
The role started when a scope with a QA, or a goal, closes, that finds wasted tokens and proposes changes to the process rules. It never changes anything itself.
_Avoid_: cost bot, optimizer

**Role**:
A job definition, for example BA or Developer.
_Avoid_: persona, type

**Agent**:
One live, named copy of a role. Each agent is a row in the roster.
_Avoid_: session (that is the process behind the agent), bot

## Structure

**Squad**:
The standing setup of one project or module: how the team works (`process.local.md`, settings) and where the project's truth lives (`project.md`). It holds many scopes and goals over time, and several squads can run side by side.
_Avoid_: project

**Scope**:
The unit of work and of freshness: one task or one part of a goal. It has its own folder, a fresh pod, and closes with one move. A lone scope shares nothing with other scopes.
_Avoid_: module, workstream

**Pod**:
The group of agents that delivers one scope.
_Avoid_: squad (a squad is the whole)

**Team**:
The optional roles of one scope, on the `team:` line of `scope.md`: any subset of `ba`, `tech-lead`, `qa-white`, `qa-black`, `designer`, `architect` (the Manager, the Team Lead and Developers are always there). The Manager proposes each role with its signal; the PO confirms. The keys `qa-white`/`qa-black` name the QA whitebox and QA blackbox roles; the term QA stays. Every subset is valid. Bigger work is a goal. Replaces the S, M, L presets (ADR 0018).
_Avoid_: tier, preset

**Duty owner**:
The role that owns one duty (business AC, code check, behaviour check, suite run and so on) on a given team: the first present role in that duty's fallback chain, every chain ending at the Manager or the Developer. One table (`DUTIES`) derives it; rules target it with a duty fact in `when:`.
_Avoid_: responsible role

**Checker**:
A role on the team that checks a task before it is done: QA whitebox, QA blackbox, and the Designer's built-UI check. With none on the team the HANDIN evidence check (squad-evidence check) decides; no role confirms.
_Avoid_: reviewer, approver

**Risk flag**:
A sign that the team needs more roles: data migration, breaking API change, security, or anything another team sees. A business doubt asks for a BA. The Manager names it in the team proposal.
_Avoid_: red flag

**Contract**:
An agreement between two scopes of one goal, such as an API, an event or a status model, kept in the goal's `shared/contracts/`.
_Avoid_: interface, spec

**Rule**:
One `## <ID> <title>` block in `templates/squad/process/*.md` with `roles:`, `aware:`, `when:` and `topic:` lines: a single instruction one role follows.
_Avoid_: clause, section, paragraph of the process

**Rule ID**:
The stable name of a rule (for example `REV-22`). Never reused, never renamed in place; a changed rule keeps its ID and gets a new hash.
_Avoid_: rule number, key

**Overlay**:
A squad's `process.local.md`: `replace`, `add` and `remove` operations on rule IDs, each pinned to a hash of the plugin text it changes, with a `why:` and an `upstream:` status.
_Avoid_: local copy, fork, patch

**Composed rules**:
The file `roles/<agent>.rules.md` that `squad-process compose` writes at spawn and respawn: the rules whose `roles` or `aware` name the role and whose `when` matches the scope, plus `core.md`. The agent reads this and nothing else of the process.
_Avoid_: process view, role copy

**Plugin pin**:
The plugin version and commit (`plugin:` in `scope.md`/`goal.md`, `plugin.pin` in the squad) a scope runs on until it closes, with its **runtime** in `_runtime/<version>-<sha12>/`. An upgrade leaves it alone unless Chieu confirms a **Pin move** of that home.
_Avoid_: version lock, process version

**Tombstone**:
The entry in `process/_removed.md` for a removed rule ID (`why:`, `replaced_by:`), so the ID is never reused.
_Avoid_: deleted rule, deprecated rule

**Composed mode** / **Legacy mode**:
A squad is in composed mode when `process.local.md` exists, and then needs a pin to spawn; with only `process.md` it is in legacy mode and its roles get the running plugin's rules with no overlay.
_Avoid_: new/old squad

**Failing sha**:
A handed-in sha with at least one FAIL. The process counts these as a task's returns; the squad report's **Return** counts FAIL messages, so the two can differ.
_Avoid_: bounce

**Process changelog**:
The plugin's list, per released version, of the rule IDs added, changed, removed and retargeted, each with a reason (`skills/squad-process-update/changelog.md`). The upgrade reads it.
_Avoid_: release notes

**Process update**:
The skill `/squad:squad-process-update`, which drives `squad-process upgrade` and then `squad-process homes`: it applies every rule the **Overlay** does not touch, lists for the PO only the stale operations (target hash changed), the operations whose target was removed, and the local rules that share a `topic` with a changed plugin rule, and then offers a **Pin move** of the Manager's home. Nothing is written without the PO's yes.
_Avoid_: migration

**Home**:
A folder with its own roster, escalations, logs, `iterations/` and `roles/`: `goals/<g>/` or `scopes/<s>/` in a per-scope squad, the squad folder itself in a flat one.
_Avoid_: folder, workspace

**Pin move**:
Rewriting the `plugin:` line of a **Home** (and of a goal's open scopes) to the squad's `plugin.pin`, on the PO's yes, then respawning that home's live agents so they read the new rules (`squad-process homes`). ADR 0031.
_Avoid_: scope upgrade

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
Writing what must outlive a scope or goal into the project's own docs, through a reviewed task. A lone scope promotes at its close; a goal once, in its last scope. The squad keeps no domain knowledge.
_Avoid_: export, archiving

**Stacked branch**:
A branch that builds on a passed but unmerged branch, so a later scope of a goal need not wait for the PO's merge.
_Avoid_: dependent branch

**Integration task**:
The last task of a scope with several tasks: a Developer merges the scope's passed branches into its own branch and runs the targeted tests; the suite owner (the Tech Lead, else QA whitebox, else the Developer) then runs the full suite.
_Avoid_: merge task

## Work

**Iteration**:
One work cycle inside a scope: goal check, plan, build and verify, retro, check-in. A scope can have several.
_Avoid_: sprint

**Away mode**:
The state of a **Home** while the file `<home>/away` exists, set by the PO saying "I am away" to a **Manager** and cleared by "I am back". The team keeps working on clear points and leaves only key decisions to the PO (the "Always goes to PO" items, merge, push, deploy); unclear questions are parked. It also turns **Sleep-when-idle** on. Rule ITER-17.
_Avoid_: vacation mode, offline mode

**Sleep-when-idle**:
The opt-in switch of the **Watchdog** (`squad-watchdog sleep on|off`, off by default). While on, the computer suspends once when no agent on the machine has worked for N minutes (default 5), for any reason and whatever the tickets say; the log names the reason. It switches itself off after one sleep.
_Avoid_: sleep-when-done

**Watchdog**:
`bin/squad-watchdog`, one per **Home**. It logs idle spells, nudges the scope's Team Lead (the Manager as fallback), and runs **Sleep-when-idle**. Inside herdr it runs alone in its own tab labelled `watchdog`; when the tab cannot be opened it falls back to a detached process.
_Avoid_: monitor, supervisor

**Lazy respawn**:
A respawn (`squad-respawn <name> --lazy`) that starts the new session but sends no prompt. A marker `roles/<name>.lazy` holds the new session's id; `bin/squad-lazy-hook` adds "read your notes" before the first message to that session. The **Watchdog** does it to an agent with a **Cold cache** risk (ADR 0033).
_Avoid_: soft respawn

**Cold cache**:
A session whose 1h prompt cache has expired; its next turn rewrites the whole context at 2x. The **Watchdog** acts at 55 min idle (see **Idle**), over 50k context.

**Idle**:
Two meanings. Of a **Home**: nobody is working while work waits (idle spell, nudges, **Sleep-when-idle**). Of one agent: its last main-thread turn is at least 55 min old (the **Cold cache** pass). The "idle" entries elsewhere in this file are the first meaning or transcript buckets.

**Goal check**:
The start of an iteration, where the Manager and PO agree the iteration's goal and the PO confirms the scope's team.
_Avoid_: kickoff

**Check-in**:
The end of an iteration, where the Manager shows the PO what is done, open escalations and proposed role changes.
_Avoid_: demo, review

**Retro**:
The step after build and verify where the Manager collects friction. The Token Coach proposes savings when an M or L scope or a goal closes.
_Avoid_: retrospective meeting

**Task**:
One piece of work for one Developer. It moves ready → building → handed in → checking → passed or returned, and a passed task is merged.
_Avoid_: ticket (a ticket lives in the project's own tracker), story

**AC**:
Acceptance criteria a task must pass. **Business AC** is agreed by the BA and QA blackbox; **technical AC** by the Tech Lead and QA whitebox.
_Avoid_: requirements, definition of done

**Passed**:
A task is passed when every non-retired QA on the team sent `PASS` for its current sha; with no QA on the team, when the `HANDIN` evidence check (`squad-evidence check`) exits 0. No role confirms it. Passed is not done: only a merged task is done. A tip that moved after the PASS reads "sha changed after PASS"; a commit that touches only the ticket's evidence folder does not move it. The watchdog and the board read `passed` from the event store, else from ledger verdicts, never from the ticket `Status:` word.
_Avoid_: done, finished, complete, ready for review

**Finding**:
One problem a checker (QA whitebox, QA blackbox, or the Team Lead with no QA) writes in its verdict file (`qa-w.md`, `qa-b.md`) for a handed-in sha: file:line or what it saw, why it matters, what would pass. A finding causes a `FAIL` (a **Return**) or goes in the `PASS` as a **Follow-up**; all findings of one sha go in one verdict (REV-17).
_Avoid_: issue, bug, comment, remark

**Follow-up**:
A finding that does not block the `PASS`: listed under `Follow-ups` in the verdict file, and batched by the Team Lead into one last, droppable ticket (LC-22b). In `qa: light` mode (LC-21, LC-22a) test-strength gaps are follow-ups; in the plugin squad, any finding that breaks no written AC and no test is one (overlay SQ-4, local only).
_Avoid_: nit, nice-to-have, backlog item

**Merged**:
A passed task whose branch is in `main`. The board derives it from git; `squad-merge-record` or `squad-task merged NN` records it when git cannot show it.

**Task event**:
A fact about one ticket (claim, handin, pass, fail, blocked, decision, merged), appended to `task-events/<slug>.jsonl` by the `squad-task` module; the board derives every state word from the events.

**Evidence**:
A file that proves a task works, such as a QA report or a Developer's run output.
_Avoid_: proof, report

**Evidence folder**:
The folder `<ticket path minus .md>/` next to a ticket (old `<stem>.evidence/` folders stay readable), holding `evidence.md` (the one file the PO reads) and `img/`. The reviewers' working files (`qa-w.md`, `qa-b.md`, `tl-review.md`) and suite receipts stay in `$SCOPE_DIR/evidence/<task>/`. A ticket never has two evidence folders. After the passed sha only `evidence.md` and `img/` may change (`squad-evidence check --base`); legacy `*.evidence/` folders keep the old any-file rule.
_Avoid_: evidence dir, proof folder

**Evidence sha**:
The commit where the Developer assembled the reviewers' files into `evidence.md` after every checker passed; its diff to the passed sha touches only evidence folders, and the Manager may merge it as the passed sha.

**Check table**:
`evidence/<NN>/checks.md` in the scope folder: one row per AC, columns Dev, QA whitebox and QA blackbox. Each role fills only its own column, with a command and its result, never code. `squad-evidence checks <file>` checks the table; once `## Checks` is in `evidence.md`, `squad-evidence check` also requires every QA cell (`-` is allowed).

**Phase rule**:
A Manager-only rule tagged `phase: merge|close|coach`. It is not attached to the Manager: the tool that starts the phase prints it (`squad-merge-check`, `squad-close`, `squad-spawn token-coach`), and `squad-process phase <name> --home D` prints it by hand. The rule index lists only its ID.

**Review pack**:
`squad-review-pack NN` writes `evidence/<NN>/pack.md` (full) and `pack-blackbox.md` (business AC only) for one `HANDIN`.

**Shots are a starting point**:
A Developer's screenshots start QA blackbox's check and never replace it: QA blackbox looks at the running app.

**Irreversible choice**:
A merge, close, advisor use or full suite. The PO decides each one. Roles ask through the Manager and never assume a yes.

**Ticket phase**:
In the squad report, a ticket's phases (spawn, build, `HANDIN`, each QA check, returns) are windows of work with their turns and tokens, not owners. A phase with no data shows `n/a`, not `0`.

**Task prompt**:
`squad-spawn --task NN` builds a Developer's first prompt from the ticket (Duties, Files), the `team:` line of `scope.md` and `roster.md`. A missing field or roster row stops the spawn before any side effect. The `HANDIN` target comes from the team's duty chain (`squadrules.resolve_duties`), never a second copy.

**Merge check**:
`squad-merge-check` reads the branch before a merge. Untracked files outside `.claude/squads/` are a warning; a dirty tracked file refuses; a `merge-base` failure fails closed.

**Handover**:
A plan section the Tech Lead writes when a role is added to a scope: what was decided, built and left open. Not the same as a HANDIN.
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

## Dashboard

**Dashboard**:
The PO's read-only local page (`squad-board`) for one goal or one scope at a time. It reads the squad's files, git, herdr and transcripts; the one file it writes is `board-ui.json`. Where the PO must act, it shows the command to copy.
_Avoid_: board (alone; the old live board was removed by 0009), monitor, console

**Picker**:
The first screen of the dashboard: the list of the squad's open goals and scopes, each with a few facts (needs you, stuck, tasks done, last active), and a Done list. The dashboard shows nothing else until the PO chooses one.
_Avoid_: home page, overview, all view

**Choice**:
The one goal or scope the dashboard shows. Squad-wide items (a permission prompt) show under every choice.
_Avoid_: filter, selection (a filter hides rows; a choice picks the folder that is read)

**Panel**:
One block of the dashboard (Needs you, Tasks, Agents now, Files, Scopes of this goal, Work time). Its height is its content height, capped; the PO sets only its order, width and visibility.
_Avoid_: widget, card

**Grid column**:
One column of the dashboard's page grid. The count (2, 4 or 6) follows the window width and text size; the PO does not set it.
_Avoid_: column (alone; iteration 2 had PO-chosen columns, now retired)

**Span**:
How many grid columns a panel takes. The PO sets it by dragging the panel's right edge; a panel has a smallest span it cannot go under.
_Avoid_: width (alone; the saved width is the tracks)

**Tracks**:
A panel's saved width as twelfths of the row (1..12, in `board-ui.json`), so it keeps its share when the window changes. Written only after the PO resizes the panel; a value above 12 reads as 12, the full width.
_Avoid_: pixels, columns

**Demo board**:
`squad-board --demo`: the dashboard on a temporary copy of the test fixture, labelled DEMO, with sample data. Nothing real is read or written, and the copy is removed on exit.
_Avoid_: sandbox, test board

**Needs you**:
The dashboard's squad-wide count of what waits on the PO: open questions, answers to read, tasks ready to merge and permission prompts; items outside the choice show as "N more need you in <name>". A parked question is not counted.
_Avoid_: notifications, todo list

**Squads pane**:
The `/squads` mod pane: a read-only, list-only index of every squad, goal and scope of the active repo, each row with the board list's six facts and a Next step; the picked row shows its commands. It writes nothing and runs no command; a click copies one. Data comes from `squad-tree` (ADR 0026).
_Avoid_: board (it shows one choice; the pane shows all), inbox

**Next step**:
The one phrase on a Squads pane row, chosen from the row's facts by fixed rules (for example "Answer 1 question(s)" when needs you is above 0). Not a task state.
_Avoid_: status, action item

**Commands table**:
The single list of squad commands in `bin/squadcommands.py`: who runs each, what it changes and when it applies. The Squads pane filters it by the picked row; a new command is added in this one place.
_Avoid_: commands doc, help text

**Parked question**:
A question the PO put aside, kept as a `## Q<n>` block in `open-questions.md` of its level (scope, goal or squad). It is not an inbox item; `squad-inbox park|unpark|resolve` is the only writer and the Manager never waits on it.
_Avoid_: deferred escalation, backlog

**Approx**:
The label on a figure the dashboard derives or models instead of reading it from a record, such as work time per task. "Unknown" is not approx: it means no source records the value.
_Avoid_: estimate (the report uses "estimated" for dollars)

**Work time**:
The working, waiting, blocked or idle time of an agent, from transcripts (ADR 0014); the dashboard shows it as swimlanes. A model of "working", not a stopwatch.
_Avoid_: timesheet, activity

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
- A **Pod** delivers exactly one **Scope**; the **Scope**'s **Team** decides which **Roles** the **Pod** has.
- A **Scope** is split into **Tasks**; one **Developer** builds one **Task**.
- A **Task** is **Passed** only when every **Checker** on the **Team** has passed it.
- Each duty has one **Duty owner** on the **Team**.
- A **Home** belongs to one **Goal** or **Scope**.
- A **Home** has at most one **Watchdog** running; the PO's "I am away" turns on **Away mode** and **Sleep-when-idle** together.
- An **Inbox** shows the open **Escalations** of its **Home** (answer items) and its own read items; the PO's answer is written into the escalation's Answer cell.
- Rendering never drops or changes the Manager's or the PO's text: unknown markup shows as plain text and every word stays reachable.
- The **Squads pane** lists every **Squad**, **Goal** and **Scope** once, each with a **Next step**, and offers the **Commands table** entries that fit the picked row; the **Dashboard** is where one **Choice** is read in full.
- The **Dashboard** shows exactly one **Choice** (a **Goal** with its **Scopes**, or one **Scope**) and many **Panels**; its **Picker** lists the choices.
- A **Parked question** belongs to one level (scope, goal or squad) and is kept apart from the **Inbox**; the **Dashboard** only reads it.
- An **Account launcher** starts Claude Code on one account; the **Workspace default**, inside herdr, else the **Global default**, decides which one `c` picks, and the launchers report an **Account token** for the workspace.
- A **Scope** runs on one **Plugin pin** from start to close.
- An **Agent** reads its **Composed rules**, built from the plugin's **Rules** and the squad's **Overlay**.
- A **Rule ID** is never reused; a removed rule leaves a **Tombstone**.
