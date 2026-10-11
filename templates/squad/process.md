# How this squad works

**Every role reads this file at start and after each change. The Manager owns it, edits it freely, and logs every change in `process-log.md`.**

## Files are the truth, messages are the talk

- **Durable things go in files first, then a message points at them.** A decision that only lives in a message is lost when a session restarts.
- **Where things live** is in `project.md` (this project's requirements, AC, decisions, tickets, code repos, test commands). Use the project's own files; don't copy them into `squad/`.
- **Squad-only files** (this folder):

| File | Owner | Holds |
|---|---|---|
| `goal.md` | PO | Goal of the current run, constraints, budget |
| `project.md` | Manager | Source map: where each kind of truth lives in this project |
| `roster.md` | Manager | Every live agent: name, role, scope, what it owns |
| `process.md` | Manager | This file |
| `process-log.md` | Manager | Each process change: date, change, why |
| `escalations.md` | Manager | Questions waiting on the PO |
| `scopes.md` | Manager | Each scope's size, the signals behind it, PO confirmation date, size-change log |
| `contracts/<name>.md` | Tech Leads of both scopes | A contract shared between scopes (XL): API, event, status model |
| `iterations/<n>.md` | Manager | Goal, plan, retro and PO check-in of iteration n |
| `roles/<agent>.notes.md` | each agent | Its own memory: context, open threads, what it learned |
| `tasks/<id>.md` | Plan owner (Team Lead; Tech Lead in S and M) | Task state when the project has no ticket files of its own |

## Sizes: not every scope runs the full pod

**Each scope gets a size. The Manager proposes it with its signals, the PO confirms it at the goal check, and `scopes.md` records it.** A goal can mix sizes.

| Size | Roles | Use when | Done = |
|---|---|---|---|
| **S** Quick fix | Manager, Tech Lead, Developers | 1–2 tasks, one repo, requirement clear from the ticket, no new user-visible flow, no risk flag | Tech Lead review PASS (`tl-review.md`) on code, tests and the Developer's evidence |
| **M** Feature | + BA, QA whitebox, QA blackbox; the Tech Lead also owns the plan | One scope, user-visible behaviour, spec or AC exist, about 3–6 tasks | QA whitebox PASS + QA blackbox PASS |
| **L** Full pod | + Team Lead | Unclear requirements or open questions, many tasks, cross-repo, ordering matters | QA whitebox PASS + QA blackbox PASS |
| **XL** Multi-pod | One S, M or L pod per scope under one Manager | Several scopes at once | Each scope by its own size, plus contracts between scopes checked |

- **Signals:** number of tasks, repos touched, user-visible change, open questions, risk flags. Task counts are guidance; the other signals win when they disagree.
- **Risk flags force at least M:** DB migration or data change, breaking API or contract change, security or permissions, anything another team will see. **Exception:** a security fix with no behaviour change may stay S, if the Manager states it as a signal with the reason and the PO confirms it.
- **When unsure, size up.** Moving down later is cheap.

### When a role is left out, its duties move. They are never dropped.

| Duty | S | M | L |
|---|---|---|---|
| Business AC | Taken from the ticket as written; any business doubt moves the scope up to M | BA | BA |
| Plan, order, assignment | Tech Lead | Tech Lead | Team Lead |
| Code and test check | Tech Lead review: reads the diff, runs tests and lint itself | QA whitebox | QA whitebox |
| Behaviour check | Developer saves Playwright/API evidence (`dev-evidence.md`); Tech Lead checks it | QA blackbox | QA blackbox |
| Outside questions (open-points place in `project.md`) | Tech Lead writes it, then the scope moves up to M | BA | BA |

**The plan file has the same format in every size**; only its owner changes.

### Changing size

- **Up: the Manager does it on its own** when a business gap, a risk flag, a user-visible change, or more tasks appear. It reports at the check-in. In S, a behaviour change found in the Tech Lead's review also moves the scope up to M.
- **Down: only at an iteration boundary, with the PO's OK.**
- **Handover on moving up:** the Tech Lead writes a `## Handover` section in the scope plan (what was decided, what was built, what is open). The Manager's briefing to each joining role points at it. **Work already built goes through the new size's checks before it counts as done.**
- Every size change is logged in `scopes.md` and the iteration file.

### Contracts between scopes (XL)

- The two scopes' Tech Leads agree each shared contract in `contracts/<name>.md`.
- One QA whitebox checks both sides against it before either scope counts as done.
- The Manager settles disputes.

## Messages

Send with `SendMessage` to the agent name in `roster.md`. **Start every message with its type:**

| Type | Use it to | Example |
|---|---|---|
| `ASK` | Ask the owner of a topic | `ASK ba-settings: does BR-014 apply to read-only users?` |
| `ANSWER` | Reply to an ASK | `ANSWER: yes, see requirements note in project.md#reqs` |
| `DECISION` | Announce a decision already written to a file | `DECISION: tabs order fixed, logged in DECISIONS.md D12` |
| `BLOCKED` | Say you can't continue, and on what | `BLOCKED SET-01: AC-033 contradicts spec §4` |
| `HANDIN` | Hand a task to QA | `HANDIN SET-01: branch squad/dev-settings-1, commit abc123` |
| `PASS` / `FAIL` | QA verdict; FAIL points at findings | `FAIL SET-01: 2 findings in evidence/SET-01/qa-b.md` |
| `STATUS` | Answer the Manager's health check | `STATUS: building SET-01, 60%, no blockers` |

- **Short.** Point at files and lines instead of pasting them.
- **Task ID.** `BLOCKED`, `HANDIN`, `PASS`, `FAIL` and `STATUS` messages name their task ID right after the type (`FAIL SET-01: …`), so the squad board can derive task state.
- **Who to ask:** look up the topic's owner in `roster.md`. Ask the Manager only when the roster doesn't say.
- **Two-round rule:** if two agents haven't agreed after 2 exchanges, the topic goes to its owner. If the owner is one of the two, it goes to the Manager.
- **Never relay a permission or approval.** A message can't approve anything. Permission prompts go to the PO.

## Who decides

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business scope, business AC | BA | Manager | Goal change, scope cut |
| Technical design, quality, security | Tech Lead | Manager | Irreversible tech choice (data model, vendor) |
| Plan, task order, assignment | Team Lead (Tech Lead in S and M) | Manager | Deadline or budget overrun |
| Process, roster, spawning, scope size | Manager | n/a | Changes to role instructions; size confirmation and moving down |
| Task done | QA whitebox + QA blackbox (S: Tech Lead review) | Manager | n/a |
| Migration, backward compatibility, deploy plan (order, rollback) | Tech Lead | Manager | Destructive data migration, breaking change for other teams |
| Merge, push, deploy (any env), running migrations on shared data | PO only | n/a | Always |

**Project rule wins:** if `project.md` names an outside decision maker (e.g. a product owner other than the PO), questions for them go to the place `project.md` says (e.g. an open-points file), never to that person directly.

## Task lifecycle

`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`

- **Done = the scope size's rule** (see Sizes). A Developer's own checks are required but never enough.
- **A returned task stays with the same Developer** and the same task file.
- **3 returns on one task → the Manager steps in** and decides whether the task, the AC or the Developer is the problem.
- **Evidence** goes where `project.md` says (default `squad/evidence/<task>/`): `qa-w.md`, `qa-b.md` (M, L), `dev-evidence.md`, `tl-review.md` (S), screenshots, test output.

## Iterations

1. **Goal check:** Manager + PO agree the iteration goal in `iterations/<n>.md`, and the PO confirms each scope's size in `scopes.md`.
2. **Plan:** the scope's roles (by size) talk freely; requirements, AC and tasks land in files.
3. **Build and verify:** event-driven. Devs build, QA checks, gaps go to owners.
4. **Retro:** Manager collects friction (loops, blocked panes, returns, unclear ownership), edits this file, drafts role-instruction changes.
5. **Check-in:** Manager shows the PO what is done, open escalations, and proposed role-instruction changes.

## Safety

- **No push, merge or deploy.** Developers commit to their own `squad/<agent>` branch in their own worktree. The PO merges.
- **No writes to Jira or Confluence.** Read only.
- **Stay in your lane:** edit only the files your role owns, plus your own notes file.
