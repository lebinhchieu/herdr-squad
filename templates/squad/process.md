# How this squad works

**Every role reads this file at start and after each change. It is shared by every scope and goal in the squad. A Manager edits it only after re-reading it, keeps each edit small, and logs it in `process-log.md`.**

## Work is grouped by scope

A **request** from the PO is one of:

- **A lone task: one scope.** Its own Manager and pod, isolated from everything else and fresh from the project docs.
- **A goal: several scopes.** One goal Manager lives across the goal and every scope inside gets a fresh pod. Only the scopes of one goal share anything, and only through `goals/<goal>/`.

A **pod** is the group of role sessions that delivers one scope. **Nothing a scope learns stays in the squad.** Lasting facts and decisions are **promoted** to the project's own docs (Promotion below); the squad keeps only how the team works.

| Level | Folder | Lives | Holds |
|---|---|---|---|
| **Project** | the repo | for good | Domain and goal knowledge, in the files `project.md` points at |
| **Squad** | `.claude/squads/<squad>/` | for good | How the team works: this file, `project.md`, `process-log.md`, `settings/` |
| **Goal** | `goals/<goal>/` | until the goal closes | What its scopes share |
| **Scope** | `scopes/<scope>/` | until the scope closes | Everything for one piece of work |

```
.claude/squads/<squad>/
  process.md  project.md  process-log.md  settings/            standing
  scopes/<scope>/
    scope.md  roster.md  escalations.md  promote.md             the brief, who is in the pod, what waits on the PO
    iterations/<n>.md  tasks/<id>.md  evidence/<task>/          plan, task state, proof
    roles/<agent>.notes.md  messages.jsonl  usage-events.jsonl  memory and logs
  scopes/_done/<scope>/                                         closed scopes
  goals/<goal>/
    goal.md  roster.md  escalations.md  roles/  messages.jsonl  the goal Manager's own files
    shared/decisions.md  shared/summaries/<scope>.md  shared/contracts/<name>.md
  goals/_done/<goal>/                                           closed goals
```

| Variable | Set for | Meaning |
|---|---|---|
| `SQUAD_DIR` | every agent | The squad folder |
| `SCOPE_DIR` | agents of a scope | Their scope folder |
| `GOAL_DIR` | the goal Manager, and agents of a scope inside a goal | The goal folder |
| `SQUAD_NAME`, `SQUAD_ROLE`, `SQUAD_SCOPE` | every agent | Own name, role and scope |

**Your folder** is `$SCOPE_DIR`, or `$GOAL_DIR` for the goal Manager. Your roster, notes, logs and evidence live there. Nothing else in the squad is yours to read or write unless this file says so.

## Files are the truth, messages are the talk

- **Durable things go in files first, then a message points at them.** A decision that only lives in a message is lost when a session restarts.
- **Where things live** is in `project.md` (this project's requirements, AC, decisions, tickets, code repos, test commands). Use the project's own files; don't copy them into the squad folder.

| File | Owner | Holds |
|---|---|---|
| `project.md` | PO and Managers | Source map: where each kind of truth lives in this project |
| `process.md`, `process-log.md` | Managers | This file; each change to it (date, change, why) |
| `scope.md` | Manager | The PO's brief as written, `goal:`, `touches:`, `size:` and its signals, constraints |
| `roster.md` | Manager | Every agent of the scope (or goal): name, role, scope, what it owns, status, session |
| `escalations.md` | Manager | Questions waiting on the PO |
| `iterations/<n>.md` | Manager | Goal, plan, retro and PO check-in of iteration n |
| `tasks/<id>.md` | Plan owner (Team Lead; Tech Lead in S and M) | Task state when the project has no ticket files of its own |
| `evidence/<task>/` | QAs, Developer, Tech Lead | `qa-w.md`, `qa-b.md`, `dev-evidence.md`, `tl-review.md`, screenshots, test output |
| `promote.md` | Tech Lead | What the scope found that must reach the project docs (Promotion) |
| `roles/<agent>.notes.md` | each agent | Its own memory, a snapshot under 80 lines (see Notes) |
| `messages.jsonl`, `usage-events.jsonl` | hooks | Message log; one line each time a cost rule fires |
| `goal.md` | goal Manager | The goal's brief, its scopes in order with dependencies, constraints, `promoted:` |
| `shared/decisions.md` | Tech Lead of the scope that closes | Decisions and domain facts that hold for the whole goal |
| `shared/summaries/<scope>.md` | Tech Lead of the scope that closes | Outcome, passed branch and commit, open items of a closed scope |
| `shared/contracts/<name>.md` | Tech Leads of both scopes | A contract shared between scopes: API, event, status model |

## Defaults

Every scope and goal starts with these. Its brief may override them.

- **Developer cap:** 3 at once; in a goal, counted across all its scopes. The Manager queues the rest.
- **Budget:** check in with the PO at the end of every iteration, and after 3 returns on one task.
- **Done means:** the size's rule (Sizes), evidence saved, branches ready for the PO to review.

## Starting work

1. The PO runs `/squad:squad-start "<text>"`. `squad-start` makes the folder and the brief (`scope.md`, or `goal.md` for text starting with `goal:`) and starts a fresh Manager. `squad-start --resume <name>` starts a new Manager for unfinished work whose Manager is gone.
2. **Names.** A scope or goal is named after its ticket id (`SEC-04` becomes `sec04`) or a short slug. Scopes and goals share one namespace, `_done/` included. An agent is `<squad>-<role-short>-<scope>[-n]` with `mgr`, `ba`, `tl`, `tech`, `qaw`, `qab`, `dev`, `coach` as role-short, at most 32 characters. Agents are addressed by bare name, and `squad-spawn` refuses a name that is already live.
3. **Overlap.** The brief's `touches:` lists the repos or paths the work changes. `squad-start` compares it with every open scope and stops on an overlap so the PO decides. Two scopes on the same files only collide at merge.
4. **First move of the Manager:** read the brief, size the scope (Sizes), propose the plan to the PO, and spawn the pod only after the PO confirms.

## Lifetimes: every scope starts fresh

| Role | Lone scope | Scope inside a goal |
|---|---|---|
| Manager | Lives and ends with the scope | The goal Manager lives across the goal. It respawns after each scope closes and re-reads only `goal.md`, `shared/` and the summaries, never a closed scope's folder |
| BA, Team Lead, Tech Lead, QA whitebox, QA blackbox | One session per scope | One session per scope |
| Developer | One session per task | One session per task |
| Token Coach | At the close (Retro) | At the close |

A lone scope sees nothing of other scopes. A scope inside a goal also reads `goal.md` and everything in `shared/` at start. Inside one long scope the Cost rules still respawn a role from its notes.

## Sizes: not every scope runs the full pod

**Each scope gets a size. The Manager proposes it with its signals, the PO confirms it at the goal check, and the `size:` line in `scope.md` records it.** The scopes of a goal can have different sizes.

| Size | Roles | Use when | Done = |
|---|---|---|---|
| **S** Quick fix | Manager, Tech Lead, Developers | 1–2 tasks, one repo, requirement clear from the ticket, no new user-visible flow, no risk flag | Tech Lead review PASS (`tl-review.md`) on code, tests and the Developer's evidence |
| **M** Feature | + BA, QA whitebox, QA blackbox; the Tech Lead also owns the plan | One scope, user-visible behaviour, spec or AC exist, about 3–6 tasks | QA whitebox PASS + QA blackbox PASS |
| **L** Full pod | + Team Lead | Unclear requirements or open questions, many tasks, cross-repo, ordering matters | QA whitebox PASS + QA blackbox PASS |

Work bigger than one L scope is a goal with several scopes.

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
- Every size change is logged in `scope.md` and the iteration file.

## Inside a goal

- **`goal.md`** lists the goal's scopes in order with what each depends on. The goal Manager makes each scope with `squad-start "<text>" --in-goal <goal> --name <scope> --touches <paths>` (a scope folder whose `scope.md` says `goal: <goal>`, no Manager of its own) and spawns its pod with `squad-spawn <role> <name> --scope <scope>`. The goal Manager's own roster is `$GOAL_DIR/roster.md`; a pod's is `scopes/<scope>/roster.md`.
- **Order and parallelism.** Scopes with no dependency between them may run at the same time. The Developer cap counts across the whole goal.
- **What is shared**, and nothing more:
  - `shared/decisions.md`: decisions and domain facts that hold for the whole goal, one bullet each (a line starting `- `), under 80 lines. The Tech Lead of a closing scope appends; the goal Manager keeps it within the cap.
  - `shared/summaries/<scope>.md`: one page per closed scope: outcome, passed branch and commit, open items, pointers to what was recorded. **No decisions or domain facts**: those go in `decisions.md`.
  - `shared/contracts/<name>.md`: a contract between scopes. The two Tech Leads agree it before either side builds on it, and one QA whitebox checks both sides against it before either scope counts as done.
- **Stacked branches.** Only the PO merges, so a scope that needs an earlier scope's unmerged code builds on its passed branch:
  - A task that needs unmerged work is spawned with `--base <passed branch or commit>`.
  - Each scope ends with **one integration task**: a Developer branches from the scope's base, merges the scope's passed task branches into its **own** branch, runs the full suite, and hands in like any task. That branch is what the next scope builds on and what the PO merges.
  - Developers may run `git merge` inside their own branch; their settings still deny `git push`, `git rebase`, `git reset --hard` and checking out `main` or `dev`. Nothing is merged into the PO's branches or pushed.
- **A lone scope has none of this.** It reads no `shared/` and builds on the project as the PO left it.

## Promotion: knowledge goes up to the project

**The project's docs are where knowledge lives.** Before a scope or goal closes, what must outlive it is written into them by a task that is reviewed and merged like any other.

- **Lone scope.** The Tech Lead keeps `promote.md` while the work runs: each lasting decision, glossary term, business rule or ADR candidate, with the target file from `project.md` and the exact wording (the BA hands the Tech Lead the business rules; in S the Tech Lead finds them). As the scope's last task a Developer commits it to the project docs on the scope's integration branch, following the project's own rule for editing those files (`project.md` names it, for example a required skill). It is checked with the rest, and the PO merges it with the code. If there is nothing to promote, `promote.md` says so and there is no task.
- **Goal.** Scopes do **not** promote at their own close: their lasting facts go to `shared/decisions.md`, which every later scope reads. **Once**, in the goal's last scope, a promotion task turns `shared/decisions.md` and the summaries into project-doc edits (the Tech Lead writes `goals/<goal>/promote.md`, a Developer commits it on that scope's integration branch). When it passes, the goal Manager adds a line `promoted: <date> <commit>` to `goal.md`.
- **A goal that is abandoned** keeps its knowledge in `goals/_done/<goal>/shared/`. `squad-close --goal` refuses while `decisions.md` has entries and `goal.md` has no `promoted:` line, unless the PO overrides it with `--force`.

## Closing

- **A scope closes when the PO confirms it** at an iteration check-in; the Manager proposes it with the evidence links. The Manager then runs the Token Coach if Retro says so, and `squad-close <squad> --scope <scope>`: it retires the scope's agents (the scope's own Manager last), removes worktrees whose branch is merged and clean, reports every branch (never deletes one), and moves the folder to `scopes/_done/`. Tell the PO which branches are still unmerged.
- **In a goal,** before the pod is retired the Tech Lead writes the scope's summary and appends its goal-wide decisions. The goal Manager updates the `goal.md` table, runs `squad-close --scope`, and respawns itself.
- **A goal closes** once every scope is closed and the promotion passed: `squad-close <squad> --goal <goal>` retires the goal Manager and moves the folder to `goals/_done/`. It refuses while a scope of the goal is open.
- **Closing the whole squad** (`squad-close <squad>`) archives everything, evidence included, to `.claude/squads/_done/<squad>/`.

## Messages

Send with `SendMessage` to the agent name in your scope's `roster.md`. **Start every message with its type:**

| Type | Use it to | Example |
|---|---|---|
| `ASK` | Ask the owner of a topic | `ASK bill-ba-invoices: does BR-014 apply to read-only users?` |
| `ANSWER` | Reply to an ASK | `ANSWER: yes, see requirements note in project.md#reqs` |
| `DECISION` | Announce a decision already written to a file | `DECISION: tabs order fixed, logged in DECISIONS.md D12` |
| `BLOCKED` | Say you can't continue, and on what | `BLOCKED SET-01: AC-033 contradicts spec §4` |
| `HANDIN` | Hand a task to QA | `HANDIN SET-01: branch squad/<squad>/<scope>/bill-dev-invoices-1, commit abc123` |
| `PASS` / `FAIL` | QA verdict; FAIL points at findings | `FAIL SET-01: 2 findings in evidence/SET-01/qa-b.md` |
| `STATUS` | Answer the Manager's health check | `STATUS: building SET-01, 60%, no blockers` |

- **Short.** Point at files and lines instead of pasting them.
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
| What is promoted to the project docs | Tech Lead (technical), BA (business) | Manager | n/a |
| Task done | QA whitebox + QA blackbox (S: Tech Lead review) | Manager | n/a |
| Migration, backward compatibility, deploy plan (order, rollback) | Tech Lead | Manager | Destructive data migration, breaking change for other teams |
| Merge, push, deploy (any env), running migrations on shared data | PO only | n/a | Always |

**Project rule wins:** if `project.md` names an outside decision maker (e.g. a product owner other than the PO), questions for them go to the place `project.md` says (e.g. an open-points file), never to that person directly.

## Task lifecycle

`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`

- **Done = the scope size's rule** (see Sizes). A Developer's own checks are required but never enough.
- **A returned task stays with the same Developer** and the same task file.
- **3 returns on one task → the Manager steps in** and decides whether the task, the AC or the Developer is the problem.
- **Evidence** goes where `project.md` says (default `$SCOPE_DIR/evidence/<task>/`): `qa-w.md`, `qa-b.md` (M, L), `dev-evidence.md`, `tl-review.md` (S), screenshots, test output.

## Iterations

A scope runs one or more iterations; each has its file `iterations/<n>.md` in the scope folder.

1. **Goal check:** Manager + PO agree the iteration goal in `iterations/<n>.md`, and the PO confirms the scope's size.
2. **Plan:** the scope's roles (by size) talk freely; requirements, AC and tasks land in files.
3. **Build and verify:** event-driven. Devs build, QA checks, gaps go to owners.
4. **Retro:** the Manager writes the friction (loops, blocked panes, returns, unclear ownership) into the iteration file.
5. **Check-in:** Manager shows the PO what is done, open escalations, and proposed role-instruction changes. Each answered escalation's outcome goes into the iteration file and its row is deleted from `escalations.md`.

**Token Coach.** At the close of every M or L scope and at goal close (an S scope only when the PO asks), the Manager spawns it (`squad-spawn token-coach <squad>-coach-<scope> --scope <scope>`, or `--goal <goal>`), tells it the folder to review and that it reads only `squad-usage` and `usage-events.jsonl`, then reads its proposals file: `iterations/<n>.coach.md` for a scope (n = the last iteration), `coach/<goal>.coach.md` in the goal folder for a goal. The Manager accepts at most the top 3 proposals into this file (each logged in `process-log.md`), moves the rest under the file's `## Backlog`, and retires the Coach. It may only propose `process.md` changes, never `agents/` or skills. This file is shared by every scope, so the lessons carry over.

## Cost rules

**Tokens are spent on context, so keep sessions small and fresh. A Stop hook (`squad-usage --check`) tells you when rule 2 or 3 fires; it logs to `usage-events.jsonl` in your folder.**

1. **Reuse** a session while it stays on the same task and context is under 50%.
2. **Fresh** when context is over 60%, after a compaction, or on a new task: write `roles/<you>.notes.md` in your folder, then `squad-respawn <you>`. The Manager is exempt from the hook; it applies this rule itself after every PO check-in, and a goal Manager after every scope close.
3. **Idle** over 1h (the cache lifetime) with context over ~100k: fresh from notes.
4. **Step-up** one notch of model or effort only on failure or escalation, for that task only.
5. **Messages point at files.** The Manager reads summaries, never transcripts.

## Notes

**`roles/<agent>.notes.md` is a snapshot of now, not a log. A fresh session reads all of it at start, so its size is your starting context.**

- **Rewrite it on every save; never append.** Hard cap: about 80 lines.
- **Fixed sections:** `Now`, `Open threads`, `Decisions that bind later work`, `Pointers`. A decision goes in the file `project.md` names (inside a goal: `shared/decisions.md`), and the notes keep a one-line pointer to it.
- **History lives elsewhere:** `iterations/<n>.md`, `process-log.md`, `shared/summaries/`. Don't copy it into notes.
- **A closed scope takes its notes with it** to `_done/`. A goal Manager drops a closed scope's detail from its own notes and keeps one pointer line.
- `squad-respawn` warns when a notes file is over 100 lines. Trim it before the next save.

## Safety

- **No push, merge or deploy.** Developers commit to their own `squad/<squad>/<scope>/<agent>` branch in their own worktree, and may merge only inside it. The PO merges.
- **No writes to Jira or Confluence.** Read only.
- **Stay in your lane:** edit only the files your role owns, plus your own notes file.
