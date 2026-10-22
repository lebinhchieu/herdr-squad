# Files and folders

## FILE-1 Requests, pods and levels
roles: manager, team-lead, tech-lead, ba
topic: structure

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
roles: manager, ba, team-lead, tech-lead
topic: structure

| Variable | Set for | Meaning |
|---|---|---|
| `SQUAD_DIR` | every agent | Squad folder |
| `SCOPE_DIR` | agents of a scope | Scope folder |
| `GOAL_DIR` | goal Manager, agents of a scope in a goal | Goal folder |
| `SQUAD_NAME`, `SQUAD_ROLE`, `SQUAD_SCOPE` | every agent | Own name, role, scope |

Your folder is `$SCOPE_DIR` (`$GOAL_DIR` for the goal Manager); your roster, notes, logs and evidence live there. Touch nothing else unless a rule says so.

## FILE-3 Where facts live
roles: manager, ba, team-lead, tech-lead
topic: structure

- `project.md` says where things live (requirements, AC, decisions, tickets, repos, test commands); use those files, never copy them into the squad folder.
- Scope files live in `scopes/<scope>/`. The goal folder holds `goal.md`, `shared/`, and the goal Manager's own `roster.md`, `escalations.md`, `roles/` and `messages.jsonl`.

## FILE-4 Editing structured files
roles: manager, team-lead
topic: files

- Edit structured files (`roster.md`, notes, tables) with a small script that keeps the rest, then check; never `command > file`.
- Write with `open(path, "w", encoding="utf-8", newline="\n")`: Python's default text mode writes CRLF on Windows, and a `\r` breaks bash `$(...)` parsing (ADR 0011). Check with `grep -c $'\r' <file>`, which must print `0`.

## FILE-5a Roster, S
roles: manager
when: size = S
topic: roster

`roster.md` must always match reality. `squad-spawn` adds an agent's row (name, role, scope, session); the Manager fills in what it owns and its status, and edits every row.

## FILE-5b Roster, Manager in M and L
roles: manager
when: size in M, L
topic: roster

`roster.md` must always match reality. `squad-spawn` adds an agent's row (name, role, scope, session); the Manager fills in what it owns and its status for the agents it spawned. The Team Lead edits its Developers' rows.

## FILE-5c Roster, Team Lead
roles: team-lead
topic: roster

Edit only the rows of the Developers you spawned (owns, status). Re-read the file just before writing and keep every other row; the Manager edits the others.

## FILE-6 Squad and brief files
roles: manager
topic: files

| File | Owner | Holds |
|---|---|---|
| `project.md` | PO, Managers | Source map |
| `process.local.md`, `process-log.md` | Managers | The squad's rule changes; each change (date, change, why) |
| `scope.md` | Manager | PO's brief, `goal:`, `touches:`, `size:` and signals, `qa:`, constraints |
| `roster.md` | Manager; Team Lead for its Developers | Each agent: name, role, scope, owns, status, session |
| `escalations.md` | Manager | Waiting on the PO |
| `promote.md` | Tech Lead | For the project docs |
| `messages.jsonl`, `usage-events.jsonl` | hooks | Message log; cost-rule firings |

## FILE-7 Plan and iteration files
roles: manager, team-lead, tech-lead
topic: files

| File | Owner | Holds |
|---|---|---|
| `iterations/<n>.md`, `iterations/<n>.log.md` | Manager | Goal, plan, status, retro, check-in, at most 80 lines; per-ticket event log (nobody reads it at start) |
| `tasks/<id>.md` | Plan owner (Team Lead; Tech Lead in S) | Task state, if the project has no ticket files |

## FILE-8 Pod summary file
roles: team-lead, manager
when: size in M, L
topic: files

`iterations/<n>.summary.md`: the Team Lead writes the pod summary for the retro and check-in, at most 40 lines.

## FILE-9 Task evidence files
roles: qa-whitebox, qa-blackbox, tech-lead, designer
topic: files

| File | Owner | Holds |
|---|---|---|
| `<ticket path minus .md>/` | Developer | `evidence.md`, the one file the PO reads; `img/` holds its screenshots |
| `evidence/<task>/` | QAs, Tech Lead | Reviewers' working files `qa-w.md`, `qa-b.md`, `tl-review.md` and suite receipts; the PO never needs it |
| `ui-design/<task>.md` | Designer | One UI task's design (`.html` optional) |

## FILE-10 Goal files
roles: manager, tech-lead
when: goal = yes
topic: files

| File | Owner | Holds |
|---|---|---|
| `goal.md` | goal Manager | Brief, ordered scopes with dependencies, constraints, `promoted:` |
| `shared/decisions.md`, `shared/summaries/<scope>.md` | Tech Lead of the closing scope | Goal decisions; closed scope's summary |
| `shared/contracts/<name>.md` | Tech Leads of both scopes | Contract between scopes: API, event, status model |

## FILE-11 Drafts never go in the project root
roles: tech-lead, ba, team-lead, manager, qa-whitebox, qa-blackbox, designer, token-coach
topic: files

Every role except the Developer drafts tickets, specs and ADR text in `$SCOPE_DIR/tasks/`, never in the project root (a Developer worktree counts as root). The scope's first Developer task commits them to the paths `project.md` names; a later draft rides the next one. `squad-path-guard` refuses Write and Edit there, not a Bash redirect; `squad-close --scope` lists stray untracked files.
