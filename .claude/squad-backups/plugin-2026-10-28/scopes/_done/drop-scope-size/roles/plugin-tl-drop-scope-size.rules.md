# Your process rules
agent: plugin-tl-drop-scope-size · role: team-lead · scope: drop-scope-size (size L, design no, architecture yes, qa full, goal no)
plugin: 0.5.2 294957333ee4b2953e1db26e96e297637ed2343c · overlay: 0 operations applied · composed: 2026-10-27T17:43:24Z
rules: CORE-1 CORE-2 CORE-3 CORE-4 CORE-5 CORE-6 FILE-1 FILE-2 FILE-3 FILE-4 FILE-5c FILE-7 FILE-8 FILE-11 START-2b START-4 START-5 START-5a START-6 START-9 START-15 SIZE-2 SIZE-6b SIZE-17b PROMO-5 MSG-1 MSG-2 MSG-3 MSG-4b MSG-5 MSG-6 MSG-7b MSG-8b MSG-9 MSG-10 MSG-13 MSG-19 MSG-20 WHO-1b WHO-3b WHO-7 WHO-8c LC-5 LC-6 LC-7b LC-11d LC-15 LC-16 LC-17 LC-25 REV-3 REV-15 EVID-3b ITER-3 COST-1 COST-2 COST-3 COST-4b COST-6b COST-7 COST-9 COST-10b COST-11 COST-13b COST-14b NOTE-1 NOTE-3 SAFE-2 SAFE-3 SAFE-4 SAFE-5 SPAWN-1 SPAWN-5b SPAWN-6 SPAWN-7 SPAWN-8b SPAWN-9

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

## FILE-1 Requests, pods and levels
A **request** from the PO is one of:
- **A lone task: one scope.** Own Manager and pod, isolated, fresh from the project docs.
- **A goal: several scopes.** One goal Manager lives across the goal; each scope gets a fresh pod. Scopes share only through `goals/<goal>/`.

A **pod** is the role sessions that deliver one scope.

| Level | Folder | Lives | Holds |
|---|---|---|---|
| Project | the repo | for good | Domain and goal knowledge (files `project.md` names) |
| Squad | `.claude/squads/<squad>/` | for good | The squad's rule overlay, `project.md`, `process-log.md`, `settings/` |
| Goal | `goals/<goal>/` | until the goal closes | What its scopes share |
| Scope | `scopes/<scope>/` | until the scope closes | One piece of work |

## FILE-2 Variables and your folder
| Variable | Set for | Meaning |
|---|---|---|
| `SQUAD_DIR` | every agent | Squad folder |
| `SCOPE_DIR` | agents of a scope | Scope folder |
| `GOAL_DIR` | goal Manager, agents of a scope in a goal | Goal folder |
| `SQUAD_NAME`, `SQUAD_ROLE`, `SQUAD_SCOPE` | every agent | Own name, role, scope |

Your folder is `$SCOPE_DIR` (`$GOAL_DIR` for the goal Manager); your roster, notes, logs and evidence live there. Touch nothing else unless a rule says so.

## FILE-3 Where facts live
- `project.md` says where things live (requirements, AC, decisions, tickets, repos, test commands); use those files, never copy them into the squad folder.
- Scope files live in `scopes/<scope>/`. The goal folder holds `goal.md`, `shared/`, and the goal Manager's own `roster.md`, `escalations.md`, `roles/` and `messages.jsonl`.

## FILE-4 Editing structured files
- Edit structured files (`roster.md`, notes, tables) with a small script that keeps the rest, then check; never `command > file`.
- Write with `open(path, "w", encoding="utf-8", newline="\n")`: Python's default text mode writes CRLF on Windows, and a `\r` breaks bash `$(...)` parsing (ADR 0011). Check with `grep -c $'\r' <file>`, which must print `0`.

## FILE-5c Roster, Team Lead
Edit only the rows of the Developers you spawned (owns, status). Re-read the file just before writing and keep every other row; the Manager edits the others.

## FILE-7 Plan and iteration files
| File | Owner | Holds |
|---|---|---|
| `iterations/<n>.md`, `iterations/<n>.log.md` | Manager | Goal, plan, status, retro, check-in, at most 80 lines; per-ticket event log (nobody reads it at start) |
| `tasks/<id>.md` | Plan owner (Manager at S and M, Team Lead at L); the Developer for its design notes at S and M | Task state, if the project has no ticket files |

## FILE-8 Pod summary file
`iterations/<n>.summary.md`: the plan owner ([ITER-3]) writes the pod summary for the retro and check-in, at most 40 lines.

## FILE-11 Drafts never go in the project root
Every role except the Developer drafts tickets, specs and ADR text in `$SCOPE_DIR/tasks/`, never in the project root (a Developer worktree counts as root). The scope's first Developer task commits them to the paths `project.md` names; a later draft rides the next one. `squad-path-guard` refuses Write and Edit there, not a Bash redirect; `squad-close --scope` lists stray untracked files.

## START-2b Developer cap, Team Lead
- **Developer cap:** spawn Developers within your share from the Manager's briefing (a lone scope has the whole cap, 3 at once); the rest waits. With your share used up, the next task waits as `ready`.
- A finished scope's share goes to the scopes still running, at their next briefing or respawn.
- The cap is a rule, not a lock: nothing stops a spawn over it, so count `herdr agent list` before each spawn.

## START-4 Names
- A scope or goal is named after its ticket id (`SEC-04` becomes `sec04`) or a short slug; scopes and goals share one namespace, `_done/` included.
- An agent is `<squad>-<role-short>-<scope>[-n]`, lowercase, at most 32 characters; role-short is `mgr`, `ba`, `tl`, `tech`, `qaw`, `qab`, `ux`, `dev` or `coach`, e.g. `bill-ba-invoices`, `bill-dev-invoices-1`. Address agents by bare name; `squad-spawn` refuses a live name.

## START-5 Lifetimes
| Role | Lone scope | Scope inside a goal |
|---|---|---|
| Manager | Lives with the scope; stays, chat-only, after the close until the PO retires it | The goal Manager lives across the goal, respawns after each scope closes, re-reads only `goal.md`, `shared/` and summaries, never a closed scope's folder |
| Team Lead, Tech Lead, QA whitebox, QA blackbox | One session per scope | Same |
| BA, Designer | One session per scope; retired once its spec and AC, or designs, are final; respawned for a question on them | Same |
| Developer | One session per task | Same |
| Token Coach | At the close ([ITER-6]) | Same |

A lone scope sees nothing of other scopes; a scope in a goal also reads `goal.md` and all of `shared/` at start.

## START-5a Architect lifetime
| Role | Lone scope | Scope inside a goal |
|---|---|---|
| Architect | One session per scope; retired once `architecture.md` is final; respawned for a question on it | Same |

## START-6 Session start
1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME $SQUAD_SCOPE`; empty → ask the Manager.
2. Read `project.md`, `$SCOPE_DIR/scope.md`, `roster.md`, your `roles/$SQUAD_NAME.notes.md` if any; in a goal also `$GOAL_DIR/goal.md`, `$GOAL_DIR/shared/`.

## START-9 Read the briefing
Read the Manager's briefing: your scope, your tasks and AC where it names them, and your peers.

## START-15 Team Lead start
Read the scope's tickets or requirements, the decisions file, and the code maps `project.md` lists.

## SIZE-2 The three sizes
| Size | Roles | Use when | Done = |
|---|---|---|---|
| **S** Quick fix | Manager, Developers | 1–2 tasks, one repo, nothing user-visible, no risk flag, existing tests cover it | The Developer's checks + `evidence.md` + `## Review` (one fresh-context Sonnet review subagent (high effort) before `HANDIN`); the Manager only confirms both exist |
| **M** Feature | + QA whitebox, QA blackbox | 1–6 tasks, user-visible, clear ticket or AC, no business question, no risk flag | QA whitebox PASS + QA blackbox PASS |
| **L** Full pod | Every role: + BA, Team Lead, Tech Lead | Business questions, any risk flag, cross-repo, ordering matters | QA whitebox PASS + QA blackbox PASS |

## SIZE-6b Plan owner, L
The Team Lead owns the plan, task order and assignment, in the same plan file and format in every size. A task of those kinds cites its rule in the task file ([GOAL-6b], [PROMO-5], [REV-15]) because the Developer does not carry them.

## SIZE-17b Joining after a move up, Team Lead
Joining because a scope moved up: take over the existing plan file from the Manager (same format) and read its `## Handover` section first.

## PROMO-5 Promotion task, Developer
A promotion task commits `promote.md` into the project docs, following the rule `project.md` names for editing them. It is handed in like any task.

## MSG-1 Sending a message
Send to the agent name in your scope's `roster.md` ([CORE-2]). `HANDIN` carries branch and commit; `FAIL` points at findings.

## MSG-2 Point at files
Point at files and lines; never paste them. `BLOCKED`, `HANDIN`, `PASS`, `FAIL` and `STATUS` name the task ID right after the type.

## MSG-3 Task ID
Task ID = the ticket number `NN` alone, never an alias or slug. Name it after the type; never paste, point at files.

## MSG-4b Ask the owner, L
Ask the owner from `roster.md`; when it doesn't say, ask the Team Lead.

## MSG-5 Pod contact
The Team Lead spawns and retires Developers, runs health checks and routes questions. Pod members message it, not the Manager.

## MSG-6 Team Lead to Manager
Message the Manager only for these, each as one line pointing at a file; never for a routine matter:
- an "Always goes to PO" item ([WHO-1b]);
- a size-change signal;
- a dispute outside plan and assignment that two rounds did not settle (the parties go to the Manager themselves; you are not a relay), or one you are yourself a party to;
- 3 returns on one task (one budget line);
- `iterations/<n>.summary.md` at iteration end ([ITER-3]).

## MSG-7b Rulings, L
A Manager or Team Lead ruling starts with `FINAL:` and is sent once. The owner never re-opens it; a new fact goes to the ruler as a new `ASK`.

## MSG-8b No STATUS push, Team Lead
Run the pod's health checks with `herdr agent list` and `herdr agent read`. Never push `STATUS`: read logs, the roster and the task file first, and send `ASK <name>: STATUS?` only after 10 minutes of no pane activity.

## MSG-9 DECISION scope
`DECISION` goes only to roles whose open task it changes, named in the first line (`DECISION SET-13, SET-14: ...`); others read the file at their next ticket.

## MSG-10 Permission prompts
Never relay a permission, approval or blocked pane; a message approves nothing. Permission prompts reach the PO through the agent's own notice.

## MSG-13 Team Lead raises gaps
Raise gaps: business and backend facts to the BA; technical ones to the Tech Lead; the Manager only for the items of [MSG-6].

## MSG-19 Routing, Team Lead
Answer "who owns X" from `roster.md`.

`HANDIN`, `PASS` and `FAIL` go to the Developer and the checkers only; you are not copied. Run `squad-ledger` (`--task NN` for one) when you act on your own messages, at health checks and at iteration end.

## MSG-20 Questions on the architecture
Follow `architecture.md`, or send the Architect an `ASK`. With no agreement after 2 rounds, the Manager decides ([CORE-4]).

## WHO-1b Owners in L
| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business scope, business AC | BA | Manager | Goal change, scope cut |
| Plan, task order, assignment | Team Lead | Team Lead | Deadline or budget overrun |
| Task done | QA whitebox + QA blackbox | Manager | n/a |

## WHO-3b Process owner in L
| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Process, roster, spawning, scope size | Manager; Team Lead for Developers | n/a | Changes to role instructions; size confirmation and moving down |

## WHO-7 Outside decision makers
Questions for an outside decision maker `project.md` names go to the place it says (for example an open-points file), never to that person.

## WHO-8c Disputes, Team Lead
Settle plan, order and assignment disputes. Write the ruling where the plan lives, and send it as `FINAL:` ([MSG-7b]). When you are yourself a party to such a dispute, do not settle it; after the two-round rule it goes to the Manager.

## LC-5 Next ticket
The next ticket starts on the last sha that passed QA whitebox, without waiting for QA blackbox, when it touches different files; a blackbox return is merged in afterwards.

## LC-6 Queued tickets
A Developer with queued tickets in its area takes the next, and retires per [COST-5].

## LC-7b Three returns, L
After 3 returns on one task (a return is a handed-in sha with a `FAIL`; `squad-ledger` counts them) the Team Lead steps in and decides whether the task, the AC or the Developer is the problem, then sends the Manager one line ([MSG-6]).

## LC-11d Plan after the architecture, L
The Team Lead plans only after `architecture.md` reads `Status: final`. The Tech Lead designs each task inside it and answers the Architect's feasibility `ASK`s.

## LC-15 Shape the plan
Shape the plan with the Tech Lead. Each task fits one Developer session, has clear AC links, and names the files it will touch. No two parallel tasks touch the same files.

## LC-16 Write the plan
Write the plan where `project.md` says (or `$SCOPE_DIR/tasks/<id>.md`): order, dependencies, owner, state. Mark which tasks are ready in parallel; migration and cross-repo tasks follow the Tech Lead's deploy order.

## LC-17 Track delivery
Move task state as `HANDIN`, `PASS` and `FAIL` messages arrive (read `squad-ledger`; you are not copied). Reorder when gaps appear. State lives in the plan file, the roster and your notes, not in memory.

## LC-25 Advisor when stuck
Consult the advisor before the next try after 2 failed attempts at one error, the same `BLOCKED` sent twice with no `ANSWER`, or (Developer) a 3rd `FAIL`. Add a 3-line note to the task file: question, advice, what was done. Advisor off: skip and say so.

## REV-3 One verdict per final sha [aware]
The Tech Lead names one final sha per task before QA verdicts; doc-only edits wait until every finding is in, and each QA gives one verdict on that sha.

## REV-15 Report deliverables [aware]
Name this in the task file of a report or doc task: a report or doc deliverable is also copied into `$SCOPE_DIR/evidence/<task>/` at the sha handed in; the `HANDIN` names that path (QA blackbox cannot read worktrees).

## EVID-3b Reviewer files in M and L [aware]
`qa-w.md` and `qa-b.md` are the reviewer files in M and L.

## ITER-3 Pod summary
Write `iterations/<n>.summary.md` at iteration end: tasks done with a link to each ticket's `evidence.md`, each task's final passed sha, the checkers that passed it and the returns per task (all three from `squad-ledger`), friction, open items, at most 40 lines. It carries one line naming the residual risk "the cap is a rule, not a lock".

## COST-1 The cost hook
A Stop hook (`squad-usage --check`) tells you when rule [COST-3] or [COST-9] fires and logs it to `usage-events.jsonl`. Limits are absolute tokens, never a percent. When a Stop-hook message says a cost rule fired, write `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md`, then run `squad-respawn $SQUAD_NAME`.

## COST-2 Reuse
Reuse a session while it stays on the same task and context is at most 120k.

## COST-3 Fresh start
Start fresh when context is over 120k, after a compaction, on a new task, or when a Stop-hook message says a cost rule fired: write `roles/<you>.notes.md`, then `squad-respawn <you>`.

## COST-4b Plan owners respawn
Respawn once your plan and AC are in files.

## COST-6b Ticket assignment, Team Lead
Before spawning for a ticket touching at most 2 files, give it to a live Developer under 80k. Give a ticket on files a live Developer already changed to that Developer while it is under 120k.

## COST-7 After a respawn
After a respawn read your notes and the files they name; your rules are already attached. Never read the whole spec again.

## COST-9 Idle
Idle over 1h with context over 100k: start fresh from notes.

## COST-10b PO wait, L
Before a PO wait (a merge, a check-in answer, a close), the Manager retires every pod role over 60k; the Team Lead respawns the roles the next iteration needs.

## COST-11 Step-up
On failure or escalation, consult the advisor first ([LC-25]). Effort may step up for that task only; a model never changes in a live session, only by respawn.

## COST-13b Nothing left to do, L
A role with no open ticket and its deliverable file written (Team Lead: the iteration file; Tech Lead: the final sha named; QA: its verdict posted) answers a fresh event from notes only and never runs `squad-respawn`; the Team Lead retires it once its work is accepted.

## COST-14b Short life, L
A role whose fresh event comes under 15 minutes after its previous respawn tells the Team Lead first; the Team Lead splits the remaining tickets or narrows what the role reads to the diff and the files its AC name.

## NOTE-1 Notes file
`roles/<agent>.notes.md` is a snapshot of now, not a log: rewrite on every save, about 80 lines (`Now`, `Open threads`, `Decisions that bind later work`, `Pointers`).

## NOTE-3 Team Lead respawn
You are not copied on `HANDIN`, `PASS` or `FAIL` (read `squad-ledger`), yet still will cross 120k. On respawn read your notes, the plan, `roster.md` and `herdr agent list`.

## SAFE-2 No Jira or Confluence writes
No writes to Jira or Confluence. Read only.

## SAFE-3 Close what you open
Before reporting, end every browser session and stop every server or process you started, by PID; never `pkill`/`killall`.

## SAFE-4 Stay in your lane
Edit only the files your role owns, plus your own notes file.

## SAFE-5 PO's branch
No squad role commits on the PO's branch: it commits only on its own `squad/` branch; ticket and spec edits ride a Developer branch.

## SPAWN-1 The spawn command
Spawn with the `squad-spawn` command (on your PATH from this plugin): `squad-spawn <role> <agent-name> --scope <scope> [--repo DIR [--base REF]] [--title "<text>"] [--prompt "first message"]`. The scope is yours (`$SQUAD_SCOPE`), or the scope you are running inside the goal.

## SPAWN-5b Developers, Team Lead
Spawn a Developer with `squad-spawn dev <squad>-dev-<scope>-<n> --scope <scope> --repo <repo> [--base <ref>] --title "<id> words" --prompt "<briefing>"`; the name is at most 32 characters. Pass `--base` only with the ref the Manager checked and named in the iteration file ([GOAL-5]).

## SPAWN-6 The first prompt
The first prompt is the agent's only briefing. Include: its scope and folder, what it owns, the files to read first (the brief, and in a goal `goal.md` and `shared/`), and who it works with by name.

## SPAWN-7 Titles and labels
Pass `--title` when the agent has a specific task: a Developer gets the ticket id and a few words (for example `TAB-04 tab labels`), a checker the ticket it checks; leave it out otherwise.

When you point an agent at a new ticket, relabel it: `squad-label --agent <name> "<text>"` (`""` clears). Labels are display only: messages and `roster.md` use the address name.

## SPAWN-8b Retiring, Team Lead
Retire a Developer with `squad-retire <agent-name>` after its task is done: it asks the agent to save its notes, then closes its pane; its branch stays for the PO.

## SPAWN-9 Team Lead spawns only Developers
Spawn and retire only Developers: no second Team Lead, no Tech Lead, BA, QA or Designer.
