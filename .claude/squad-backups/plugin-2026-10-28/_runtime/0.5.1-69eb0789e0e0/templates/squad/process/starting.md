# Starting work

## START-1 Brief defaults
roles: manager
topic: defaults

Every scope and goal starts with these; its brief may override them.

- **Budget:** the Manager checks in with the PO at each iteration's end and after 3 returns on one task.
- **Done means:** the size's Done rule ([SIZE-2]), evidence saved, branches ready for PO review.

## START-2a Developer cap, S and M
roles: manager
when: size in S, M
topic: developers

- **Developer cap:** 3 at once. Spawn one Developer per ready task, up to the cap, and queue the rest. A task is ready when its dependencies are done, its AC are agreed and it touches no file another running task touches; the cap is the brief's, else this one.
- In a goal the goal Manager divides the cap among running scopes in their briefings.
- You decide which tasks are ready in parallel (dependencies done, AC agreed, no shared files); the Developers' design notes in the task files show what each touches.

## START-2b Developer cap, Team Lead
roles: team-lead
when: size = L
topic: developers

- **Developer cap:** spawn Developers within your share from the Manager's briefing (a lone scope has the whole cap, 3 at once); the rest waits. With your share used up, the next task waits as `ready`.
- A finished scope's share goes to the scopes still running, at their next briefing or respawn.
- The cap is a rule, not a lock: nothing stops a spawn over it, so count `herdr agent list` before each spawn.

## START-2c Developer cap, Manager in L
roles: manager
when: size = L
topic: developers

- The Team Lead spawns and retires Developers within its share of the cap; the Manager does not.
- Tell each Team Lead its Developer share of the cap in its first prompt. A lone scope gets the whole cap. In a goal the goal Manager divides the cap among the scopes running at that time, shares summing to at most the cap; a Team Lead spawns no more Developers than its share.

## START-2d Parallel tasks, Tech Lead
roles: tech-lead
when: size = L
topic: developers

Tell the Manager which tasks are ready in parallel (dependencies done, AC agreed, no shared files); the Team Lead spawns one Developer per such task.

## START-3 Starting a scope
roles: manager
topic: starting

1. The PO runs `/squad:squad-start "<text>"`; it makes the folder and brief (`scope.md`, or `goal.md` for text starting `goal:`) and starts a fresh Manager. `squad-start --resume <name>` starts a new Manager for unfinished work whose Manager is gone.
2. **Overlap.** `touches:` lists the repos or paths the work changes. `squad-start` compares it with every open scope and stops on an overlap for the PO.
3. The Manager reads the brief, sizes the scope ([SIZE-1]), proposes the plan, and spawns the pod only after the PO confirms.

## START-3b Team models, first move
roles: manager
topic: starting

- With the size and the plan, show the PO one table in the same inbox item: each role the size brings, its default model and effort, and the advisor on or off (read-only unless the advisor probe found an off value).
- Offer to keep the table or change any row.
- Write only the changed rows to `scope.md`, one line each, `model <role>: <model> <effort>` (for example `model dev: sonnet medium`), then spawn. Roles not listed use their defaults.
- A goal Manager does this for each scope, before that scope's first spawn.
- A change in the middle of a scope applies to the next spawn or respawn of that role; respawn running agents only when the PO asks.
- `squad-spawn` order: flags, the agent's recorded override, `scope.md`, squad settings, template. Developer spawns by any role pick the `scope.md` line up unchanged.

## START-4 Names
roles: manager, team-lead
topic: spawning

- A scope or goal is named after its ticket id (`SEC-04` becomes `sec04`) or a short slug; scopes and goals share one namespace, `_done/` included.
- An agent is `<squad>-<role-short>-<scope>[-n]`, lowercase, at most 32 characters; role-short is `mgr`, `ba`, `tl`, `tech`, `qaw`, `qab`, `ux`, `dev` or `coach`, e.g. `bill-ba-invoices`, `bill-dev-invoices-1`. Address agents by bare name; `squad-spawn` refuses a live name.

## START-5 Lifetimes
roles: manager, team-lead
topic: lifetimes

| Role | Lone scope | Scope inside a goal |
|---|---|---|
| Manager | Lives with the scope; stays, chat-only, after the close until the PO retires it | The goal Manager lives across the goal, respawns after each scope closes, re-reads only `goal.md`, `shared/` and summaries, never a closed scope's folder |
| Team Lead, Tech Lead, QA whitebox, QA blackbox | One session per scope | Same |
| BA, Designer | One session per scope; retired once its spec and AC, or designs, are final; respawned for a question on them | Same |
| Developer | One session per task | Same |
| Token Coach | At the close ([ITER-6]) | Same |

A lone scope sees nothing of other scopes; a scope in a goal also reads `goal.md` and all of `shared/` at start.

## START-6 Session start
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev
topic: start

1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME $SQUAD_SCOPE`; empty → ask the Manager.
2. Read `project.md`, `$SCOPE_DIR/scope.md`, `roster.md`, your `roles/$SQUAD_NAME.notes.md` if any; in a goal also `$GOAL_DIR/goal.md`, `$GOAL_DIR/shared/`.

## START-7 Start inside a goal
roles: ba, team-lead, tech-lead, qa-whitebox, designer
when: goal = yes
topic: start

Inside a goal (`GOAL_DIR` set) also read `$GOAL_DIR/goal.md` and everything in `$GOAL_DIR/shared/`.

## START-8 Start inside a goal, QA blackbox
roles: qa-blackbox
when: goal = yes
topic: start

Inside a goal (`GOAL_DIR` set) also read `$GOAL_DIR/goal.md` and the `shared/` files that describe behaviour, not code.

## START-9 Read the briefing
roles: ba, team-lead, tech-lead, qa-whitebox, designer
topic: start

Read the Manager's briefing: your scope, your tasks and AC where it names them, and your peers.

## START-10 Developer start
roles: dev
topic: start

1. Read your briefing (task, AC, design, peers).
2. `git status`, `git branch --show-current`: expect `squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME`, work only there.
3. Read CLAUDE.md and the `project.md` conventions.

## START-11 BA start
roles: ba
topic: start

Read the scope's requirements where `project.md` says they live, before talking to anyone.

## START-12 Designer start
roles: designer
topic: start

Read the existing UI conventions that `project.md` lists, and the running UI's own code (read-only). Reuse existing components, palette and patterns before inventing anything.

## START-13 QA blackbox start
roles: qa-blackbox
topic: start

Read the Manager's briefing and the scope's requirements, business AC, and screens or prototype `project.md` lists, plus `$SCOPE_DIR/ui-design/<task>.md` when the ticket cites it. Walk every screen and state of that design on the running app; a difference is a FAIL like any AC miss (designs are not code, so this does not break "stay blind to the code").

## START-14 QA whitebox start
roles: qa-whitebox
topic: start

Read the repo conventions and the definition-of-done rules `project.md` lists.

## START-15 Team Lead start
roles: team-lead
topic: start

Read the scope's tickets or requirements, the decisions file, and the code maps `project.md` lists.

## START-16 Tech Lead start
roles: tech-lead
topic: start

Read the existing design decisions (ADRs, decisions file, conventions) that `project.md` lists. You start fresh in every scope; these files are your memory.

## START-17 Token Coach start
roles: token-coach
topic: start

1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Your folder is `$SCOPE_DIR`, or `$GOAL_DIR` when the Manager asked you to review a goal. Read your folder's `roster.md` and the latest `iterations/<n>.md` (scope) or `goal.md` (goal).
2. Run `squad-usage` for the per-agent table. Read your folder's `usage-events.jsonl` and `$SQUAD_DIR/process-log.md`: do not propose a change that is already logged there.

## START-18 Manager start
roles: manager
topic: start

1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. With `SCOPE_DIR` set you run a lone scope; with `GOAL_DIR` set and no `SCOPE_DIR` you are a goal Manager. If neither folder exists, tell the PO to run `/squad:squad-start` and stop.
2. Read `project.md`, then your folder, in this order:
   - Scope Manager: `$SCOPE_DIR/scope.md` (the PO's brief), `roster.md`, `escalations.md`, the latest `iterations/<n>.md`, and your notes `roles/$SQUAD_NAME.notes.md`.
   - Goal Manager: `$GOAL_DIR/goal.md`, `shared/decisions.md`, `shared/summaries/`, `roster.md`, `escalations.md`, your notes.
   - Never read a `_done/` folder.
3. Check live agents with `herdr agent list` and reconcile `roster.md` with it (mark dead agents, note who needs respawning).
4. Tell the PO in 3–5 lines: where the work stands, what you do next, anything waiting on them. A brand-new scope has no iteration file yet: that is your first move ([START-19]).

## START-19 First move: size and plan
roles: manager
topic: starting

- Scope Manager: read the brief, size the scope ([SIZE-1]) with its signals, write the size into `scope.md`, create `iterations/1.md` with the iteration goal and the plan, and ask the PO to confirm the size and plan before you spawn anyone. When unsure, size up.
- Goal Manager: split the brief into scopes. Write them into `goal.md` in order, with what each depends on and what it touches. Propose each scope's size too. Ask the PO to confirm the split, then start the scopes whose dependencies are done ([GOAL-1]).
