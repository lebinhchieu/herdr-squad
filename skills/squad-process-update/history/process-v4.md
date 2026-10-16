# How this squad works

process-version: 4

Every role reads the sections its row names, at start and when the Manager says one changed. A Manager edits this file only after re-reading it, in small edits, each logged in `process-log.md`.

| Role | Reads at start |
|---|---|
| Developer, QA whitebox, QA blackbox | its task and AC (QA: also the task's evidence folder); the design sections the task cites (grep the heading); Messages, Task lifecycle, Cost rules, Safety. Not the whole spec, not other tasks |
| UI/UX Designer | the UI tasks and AC, the UI conventions row of `project.md`; Messages, Cost rules, Safety |
| Token Coach | what the Manager's briefing names |
| BA, Team Lead, Tech Lead, Manager | everything |

## Work is grouped by scope

A **request** from the PO is one of:
- **A lone task: one scope.** Own Manager and pod, isolated, fresh from the project docs.
- **A goal: several scopes.** One goal Manager lives across the goal; each scope gets a fresh pod. Scopes share only through `goals/<goal>/`.

A **pod** is the role sessions that deliver one scope.

| Level | Folder | Lives | Holds |
|---|---|---|---|
| Project | the repo | for good | Domain and goal knowledge (files `project.md` names) |
| Squad | `.claude/squads/<squad>/` | for good | This file, `project.md`, `process-log.md`, `settings/` |
| Goal | `goals/<goal>/` | until the goal closes | What its scopes share |
| Scope | `scopes/<scope>/` | until the scope closes | One piece of work |

| Variable | Set for | Meaning |
|---|---|---|
| `SQUAD_DIR` | every agent | Squad folder |
| `SCOPE_DIR` | agents of a scope | Scope folder |
| `GOAL_DIR` | goal Manager, agents of a scope in a goal | Goal folder |
| `SQUAD_NAME`, `SQUAD_ROLE`, `SQUAD_SCOPE` | every agent | Own name, role, scope |

Your folder is `$SCOPE_DIR` (`$GOAL_DIR` for the goal Manager); your roster, notes, logs and evidence live there. Touch nothing else unless this file says so.

## Files are the truth, messages are the talk

- Write a durable thing to a file first, then send a message pointing at it.
- `project.md` says where things live (requirements, AC, decisions, tickets, repos, test commands); use those files, never copy them into the squad folder.
- Edit structured files (`roster.md`, notes, tables) with a small script that keeps the rest, then check; never `command > file`.
- Scope files live in `scopes/<scope>/`. The goal folder holds `goal.md`, `shared/`, and the goal Manager's own `roster.md`, `escalations.md`, `roles/` and `messages.jsonl`.

| File | Owner | Holds |
|---|---|---|
| `project.md` | PO, Managers | Source map |
| `process.md`, `process-log.md` | Managers | This file; each change (date, change, why) |
| `scope.md` | Manager | PO's brief, `goal:`, `touches:`, `size:` and signals, `qa:`, constraints |
| `roster.md` | Manager; Team Lead for its Developers | Each agent: name, role, scope, owns, status, session |
| `escalations.md` | Manager | Waiting on the PO |
| `iterations/<n>.summary.md` | Team Lead (M, L) | Pod summary for the retro and check-in, at most 40 lines |
| `iterations/<n>.md`, `iterations/<n>.log.md` | Manager | Goal, plan, status, retro, check-in, at most 80 lines; per-ticket event log (nobody reads it at start) |
| `tasks/<id>.md` | Plan owner (Team Lead; Tech Lead in S) | Task state, if the project has no ticket files |
| `evidence/<task>/` | QAs, Developer, Tech Lead | `qa-w.md`, `qa-b.md`, `dev-evidence.md`, `tl-review.md`, screenshots, output |
| `ui-design/<task>.md` | Designer | One UI task's design (`.html` optional) |
| `promote.md` | Tech Lead | For the project docs |
| `roles/<agent>.notes.md` | each agent | Under 80 lines |
| `messages.jsonl`, `usage-events.jsonl` | hooks | Message log; cost-rule firings |
| `goal.md` | goal Manager | Brief, ordered scopes with dependencies, constraints, `promoted:` |
| `shared/decisions.md`, `shared/summaries/<scope>.md` | Tech Lead of the closing scope | Goal decisions; closed scope's summary |
| `shared/contracts/<name>.md` | Tech Leads of both scopes | Contract between scopes: API, event, status model |

## Defaults

Every scope and goal starts with these; its brief may override them.

- **Developer cap:** 3 at once. The Team Lead (S: the Manager) spawns up to it and queues the rest; in a goal the goal Manager divides it among running scopes in their briefings.
- **Budget:** the Manager checks in with the PO at each iteration's end and after 3 returns on one task.
- **Done means:** the size's Done rule (Sizes), evidence saved, branches ready for PO review.

## Starting work

1. The PO runs `/squad:squad-start "<text>"`; it makes the folder and brief (`scope.md`, or `goal.md` for text starting `goal:`) and starts a fresh Manager. `squad-start --resume <name>` starts a new Manager for unfinished work whose Manager is gone.
2. **Names.** A scope or goal is named after its ticket id (`SEC-04` becomes `sec04`) or a short slug; scopes and goals share one namespace, `_done/` included.
3. An agent is `<squad>-<role-short>-<scope>[-n]`, at most 32 characters; role-short is `mgr`, `ba`, `tl`, `tech`, `qaw`, `qab`, `ux`, `dev` or `coach`. Address agents by bare name; `squad-spawn` refuses a live name.
4. **Overlap.** `touches:` lists the repos or paths the work changes. `squad-start` compares it with every open scope and stops on an overlap for the PO.
5. The Manager reads the brief, sizes the scope (Sizes), proposes the plan, and spawns the pod's non-Developer roles only after the PO confirms.

## Lifetimes: every scope starts fresh

| Role | Lone scope | Scope inside a goal |
|---|---|---|
| Manager | Lives and ends with the scope | The goal Manager lives across the goal, respawns after each scope closes, re-reads only `goal.md`, `shared/` and summaries, never a closed scope's folder |
| BA, Team Lead, Tech Lead, QA whitebox, QA blackbox | One session per scope | Same |
| Designer | One session per scope; retired once every design is final | Same |
| Developer | One session per task | Same |
| Token Coach | At the close (Iterations) | Same |

A lone scope sees nothing of other scopes; a scope in a goal also reads `goal.md` and all of `shared/` at start. Cost rules respawn a role from its notes inside a long scope.

## Sizes: not every scope runs the full pod

The Manager proposes each scope's size with its signals, the PO confirms it at the goal check, and `size:` in `scope.md` records it. Scopes of a goal can differ.

| Size | Roles | Use when | Done = |
|---|---|---|---|
| **S** Quick fix | Manager, Tech Lead, Developers | 1–2 tasks, one repo, clear ticket, no new user-visible flow or risk flag | Tech Lead review PASS (`tl-review.md`) |
| **M** Feature | + BA, QA whitebox, QA blackbox, Team Lead | One scope, user-visible behaviour, spec or AC exist, about 3–6 tasks | QA whitebox PASS + QA blackbox PASS |
| **L** Full pod | As M | Unclear requirements or open questions, many tasks, cross-repo, ordering matters | QA whitebox PASS + QA blackbox PASS |

Work bigger than one L scope is a goal. A `design:` line in `scope.md` (`yes|no`, default `no`) adds the Designer to a scope of any size. **The Manager sets `design: yes` only when the PO asks; it never proposes it.** It logs the answer in the iteration file.

- **Signals:** tasks, repos touched, user-visible change, open questions, risk flags; when they disagree, task count loses.
- **Risk flags force at least M:** DB migration or data change, breaking API or contract change, security or permissions, anything another team will see. A security fix with no behaviour change may stay S when the Manager states the reason as a signal and the PO confirms.
- When unsure, size up.

### When a role is left out, its duties move. They are never dropped.

| Duty | S | M | L |
|---|---|---|---|
| Business AC | Ticket as written; business doubt moves it to M | BA | BA |
| Plan, order, assignment | Tech Lead | Team Lead | Team Lead |
| Code and test check | Tech Lead reads the diff, runs tests and lint | QA whitebox | QA whitebox |
| Behaviour check | Developer saves Playwright/API evidence (`dev-evidence.md`); Tech Lead checks it | QA blackbox | QA blackbox |
| UI/UX design (only when `design: yes`) | Designer | Designer | Designer |
| Built UI vs the design | Developer screenshots each screen and state in `dev-evidence.md`; Tech Lead checks them | QA blackbox | QA blackbox |
| Outside questions (open-points place in `project.md`) | Tech Lead writes it; scope moves to M | BA | BA |

The plan file has the same format in every size; only its owner changes.

### Changing size

- **Up:** the Manager moves a scope up on its own when a business gap, risk flag, user-visible change or more tasks appear, and reports it at the check-in. In S, a behaviour change found in review also moves it to M.
- **Down:** only at an iteration boundary, with the PO's OK; the Manager retires the roles that drop out.
- **Handover on moving up:** the Tech Lead writes a `## Handover` section in the scope plan (decided, built, open); a joining Team Lead takes the plan over from it; the Manager's briefing to each joining role points at it. Built work passes the new size's checks before it counts as done.
- The Manager logs every size change in `scope.md` and the iteration file.

## Inside a goal

- `goal.md` orders the scopes with their dependencies. The goal Manager makes each scope with `squad-start "<text>" --in-goal <goal> --name <scope> --touches <paths>` (its `scope.md` says `goal: <goal>`) and spawns its pod with `squad-spawn <role> <name> --scope <scope>`.
- Independent scopes may run at once (cap: Defaults).
- **Shared, and nothing more:** `shared/decisions.md`: one `- ` bullet per whole-goal decision or domain fact, under 80 lines, kept by the goal Manager.
- `shared/summaries/<scope>.md`: one page per closed scope: outcome, passed branch and commit, open items, pointers; no decisions or domain facts.
- `shared/contracts/<name>.md`: both Tech Leads agree it before either builds; one QA whitebox checks both sides against it before either scope is done.
- **Stacked branches.** Nothing merges until the PO asks, so a scope that needs an earlier scope's unmerged code builds on its passed branch:
  - A task that needs unmerged work is spawned with `--base <passed branch or commit>`, which the Manager checked and named in the iteration file.
  - Each scope ends with one integration task: a Developer branches from the scope's base, merges the passed task branches into its own, runs the full suite and hands in. The next scope builds on that branch; the PO merges it.
  - A one-task scope has no integration task: its passed branch is the integration branch.
  - **Check a merge target before naming it:** the Manager runs `git merge-base --is-ancestor <base> <sha>` and `git log --oneline <base>..<sha>` and quotes the output, never a ticket list.
- A lone scope builds on the project as the PO left it.

## Promotion: knowledge goes up to the project

A task, reviewed and merged like any other, writes what must outlive a scope or goal into the project docs before it closes.

- **Lone scope:** the Tech Lead keeps `promote.md` while work runs: each lasting decision, glossary term, business rule or ADR candidate, with its `project.md` target file and exact wording. The BA hands over business rules; in S the Tech Lead finds them.
- The scope's last task: a Developer commits `promote.md` to the project docs on the integration branch, by the project's rule for editing those files (`project.md`); the PO merges it with the code. With nothing to promote, `promote.md` says so and there is no task.
- **Goal:** scopes do not promote at their own close; lasting facts go to `shared/decisions.md`. Once, in the last scope, a promotion task turns `decisions.md` and the summaries into project-doc edits: the Tech Lead writes `goals/<goal>/promote.md`, a Developer commits it on that scope's integration branch.
- When it passes, the goal Manager adds `promoted: <date> <commit>` to `goal.md`.
- An abandoned goal keeps its knowledge in `goals/_done/<goal>/shared/`. `squad-close --goal` refuses while `decisions.md` has entries and `goal.md` has no `promoted:` line, unless the PO overrides with `--force`.

## Closing

- **Scope:** the PO confirms the close at a check-in; the Manager proposes it with evidence links, runs the Token Coach if Iterations says so, then `squad-close <squad> --scope <scope>`.
- `squad-close` retires the scope's agents (its Manager last), removes worktrees whose branch is merged and clean, reports every branch (never deletes one) and moves the folder to `scopes/_done/`; the Manager tells the PO which are unmerged.
- **In a goal,** the Tech Lead writes the scope's summary and appends its decisions to `shared/decisions.md` before the pod is retired; the goal Manager updates the `goal.md` table, runs `squad-close --scope` and respawns itself.
- **Goal:** closes once every scope is closed and the promotion passed. `squad-close <squad> --goal <goal>` retires the goal Manager and moves the folder to `goals/_done/`; it refuses while a scope is open.
- **Squad:** `squad-close <squad>` archives everything, evidence included, to `.claude/squads/_done/<squad>/`.

## Messages

Send with `SendMessage` to the agent name in your scope's `roster.md`, as `<TYPE> <TASK-ID>: <text>`:

| Type | Use it to |
|---|---|
| `ASK` | Ask a topic's owner |
| `ANSWER` | Reply to an ASK |
| `DECISION` | Announce a decision already in a file |
| `BLOCKED` | Say you can't continue, and on what |
| `HANDIN` | Hand a task to QA, with branch and commit |
| `PASS` / `FAIL` | QA verdict; FAIL points at findings |
| `STATUS` | Answer a health check |

- Point at files and lines; never paste them. `BLOCKED`, `HANDIN`, `PASS`, `FAIL` and `STATUS` name the task ID right after the type.
- Ask the owner from `roster.md`; when it doesn't say, ask the Team Lead (S: the Manager).
- **Pod contact (M, L):** the Team Lead spawns and retires Developers, runs health checks and routes questions. Pod members message it, not the Manager.
- **Team Lead to Manager (M, L):** only an "Always goes to PO" item, a size-change signal, a dispute it cannot settle or 3 returns on one task (a budget line); plus the iteration summary.
- **Two-round rule:** agents who haven't agreed after 2 exchanges send the topic to its owner, or to the Manager when the owner is one of them.
- **A Manager or Team Lead ruling starts with `FINAL:` and is sent once.** The owner never re-opens it; a new fact goes to the ruler as a new `ASK`.
- The Team Lead (S: the Manager) never pushes `STATUS`: it reads logs, the roster and the task file first, and pings an agent only after 10 minutes of no pane activity.
- `DECISION` goes only to roles whose open task it changes, named in the first line (`DECISION SET-13, SET-14: ...`); others read the file at their next ticket.
- Never relay a permission, approval or blocked pane; a message approves nothing. Permission prompts reach the PO through the agent's own notice.

## Who decides

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business scope, business AC | BA | Manager | Goal change, scope cut |
| Technical design, quality, security | Tech Lead | Manager | Irreversible tech choice (data model, vendor) |
| Plan, task order, assignment | Team Lead (Tech Lead in S) | Team Lead (S: Manager) | Deadline or budget overrun |
| Process, roster, spawning, scope size | Manager; Team Lead for Developers (M, L) | n/a | Changes to role instructions; size confirmation and moving down |
| UI design (screens, states, flows) | Designer | Manager | n/a |
| What is promoted to the project docs | Tech Lead (technical), BA (business) | Manager | n/a |
| Task done | QA whitebox + QA blackbox (S: Tech Lead review) | Manager | n/a |
| Migration, backward compatibility, deploy plan (order, rollback) | Tech Lead | Manager | Destructive data migration, breaking change for other teams |
| Merge a passed branch (Safety) | PO asks; the Manager runs it | n/a | Always, per merge |
| Push, deploy (any env), running migrations on shared data | PO only | n/a | Always |

Questions for an outside decision maker `project.md` names go to the place it says (for example an open-points file), never to that person.

## Task lifecycle

`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`

- A Developer's own checks are required but never enough for done (Sizes).
- A UI ticket with a `Design:` line stays `ready` until its design is `Status: final`.
- A returned task stays with its Developer and task file.
- QA never pre-writes test points before the Developer starts; the Tech Lead's AC are the bar.
- The next ticket starts on the last sha that passed QA whitebox, without waiting for QA blackbox, when it touches different files; a blackbox return is merged in afterwards.
- A Developer with queued tickets in its area takes the next, and retires per Cost rules.
- **Verify against the real thing:** code that parses another tool's output (pane text, logs, an API) needs two real samples, including the constant or idle case, before a pattern is trusted; QA whitebox runs it once, read-only, on live data.
- A ticket that changes a payload is checked on its field shape (every row has the fields the consumer reads, every closed item has its end), not only on totals.
- **QA mode** (`qa:` in `scope.md`): `full` (default) or `light`. In `light`, QA runs the suite, skims the diff and PASSes; a task returns only for wrong behaviour, a spec-rule defect, a failing suite or a security finding.
- In `light`, test-strength gaps go in `qa-w.md` as "follow-up"; the Tech Lead batches them into one last, droppable ticket.
- After 3 returns on one task the Team Lead (S: the Manager) steps in and decides whether the task, the AC or the Developer is the problem.
- Evidence goes where `project.md` says (default `$SCOPE_DIR/evidence/<task>/`); `qa-b.md` exists in M and L, `tl-review.md` in S.

## Iterations

Each iteration has `iterations/<n>.md`.

1. **Goal check:** the Manager and PO agree the goal in the iteration file; the PO confirms the size.
2. **Plan:** the roles (by size) talk freely; requirements, AC and tasks land in files.
3. **Build and verify:** event-driven; Developers build, QA checks, gaps go to owners.
4. **Retro:** the Manager writes the friction (loops, blocked panes, returns, unclear ownership) into the iteration file.
5. **Check-in:** the Manager shows the PO what is done, open escalations and proposed role-instruction changes; each answered escalation's outcome goes into the iteration file and its row leaves `escalations.md`.

**Token Coach:**
- The Manager spawns it at the close of every M or L scope and at goal close (S only when the PO asks): `squad-spawn token-coach <squad>-coach-<scope> --scope <scope>`, or `--goal <goal>`.
- It reads only `squad-usage` and `usage-events.jsonl` of the folder the Manager names, and writes `iterations/<n>.coach.md` (scope; n = last iteration) or `coach/<goal>.coach.md` in the goal folder.
- The Manager accepts at most the top 3 proposals into this file, logs each in `process-log.md`, moves the rest under the proposals file's `## Backlog`, and retires the Coach.
- The Coach proposes only `process.md` changes, never `agents/` or skills.

## Cost rules

A Stop hook (`squad-usage --check`) tells you when rule 2 or 3 fires and logs it to `usage-events.jsonl`. Limits are absolute tokens, never a percent.

1. **Reuse** a session while it stays on the same task and context is at most 120k.
2. **Fresh** when context is over 120k, after a compaction, or on a new task: write `roles/<you>.notes.md` in your folder, then `squad-respawn <you>`. A Developer retires at 120k or at the end of its area.
   - **The Manager is not exempt:** after every DONE, every PO message and at least every 25 turns it reads its `squad-usage` row; over 120k, after a compaction or a cache expiry it writes notes and runs `squad-respawn` at the next quiet moment.
3. **Idle** over 1h with context over 100k: start fresh from notes.
4. **Step-up** one notch of model or effort only on failure or escalation, for that task only.
5. **Messages point at files.** The Manager reads summaries, never transcripts.

## Notes

`roles/<agent>.notes.md` is a snapshot of now, not a log; a fresh session reads all of it.

- Rewrite it on every save, never append; hard cap about 80 lines.
- Fixed sections: `Now`, `Open threads`, `Decisions that bind later work`, `Pointers`. A decision goes in the file `project.md` names (in a goal: `shared/decisions.md`); the notes keep a one-line pointer.
- History lives in `iterations/<n>.md`, `process-log.md` and `shared/summaries/`, never in notes.
- A closed scope's notes go with it to `_done/`; a goal Manager keeps one pointer line per closed scope.
- `squad-respawn` warns when notes pass 100 lines; trim before the next save.

## Safety

- **No push or deploy.** Developers commit to their own `squad/<squad>/<scope>/<agent>` branch and worktree and `git merge` only inside it. Their settings deny `git push`, `git rebase`, `git reset --hard` and checking out `main` or `dev`.
- **Merge only on the PO's request.** Only the Manager merges into the PO's branch, and only when the PO asks in the Manager's own session. A passed branch, a green suite or an approved check-in is not a request.
  - **Which merge:** only what the PO names, into the branch checked out in the project root; the Manager never switches branches.
  - **Before:** check the target as in Stacked branches and that both checkers passed the sha. Refuse, with the reason, if the project root has uncommitted changes or the sha is not the passed one. Use `git merge --no-ff`.
  - **Conflict or failure:** `git merge --abort`, then tell the PO the files in conflict. The Manager never resolves a conflict and never uses `--force`, `rebase`, `reset --hard` or `push`.
  - **After:** quote `git log --oneline -1` and the result to the PO; note it in the iteration file.
- **No writes to Jira or Confluence.** Read only.
- **Long suites: run once, read the receipt.** A suite over ~2 minutes runs once per task. `project.md` may name the runner; it locks only its browser files and skips phases the diff cannot affect.
  - The Developer runs the full suite once, on the final sha after every fix, in the background, waits for its completion notice (never `pgrep -f` or `pkill -f`) and saves a receipt: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the suite's OK line. While building, only touched files.
  - QA checks the receipt (same sha as the `HANDIN`, clean tree, OK, its skipped-phase lines), then runs only targeted tests for the diff's files and reads the diff. It runs the full suite only when the receipt is missing or its sha differs, integration tasks included. Targeted runs are free.
- **Close what you open.** Before you report, end every browser session and stop every server or process you started, by PID. Never `pkill` or `killall` by name or pattern.
- **Stay in your lane:** edit only the files your role owns, plus your own notes file.
