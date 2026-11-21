# Spawning and retiring

## SPAWN-1 The spawn command
roles: manager, team-lead
topic: spawning

Spawn with the `squad-spawn` command (on your PATH from this plugin): `squad-spawn <role> <agent-name> --scope <scope> [--repo DIR [--base REF]] [--title "<text>"] [--task NN] [--prompt "first message"]`. The scope is yours (`$SQUAD_SCOPE`), or the scope you are running inside the goal.

## SPAWN-2b Roles the Manager spawns, Team Lead plans
roles: manager
topic: spawning

You spawn `team-lead`, every other role on `team:` and `token-coach` as [ITER-6b] says. `squad-spawn` refuses a role that is not on the team.

## SPAWN-2c Developers, Team Lead plans
roles: manager
topic: spawning

The Team Lead spawns Developers; you do not.

## SPAWN-3 Team in the first prompt
roles: manager
topic: spawning

Tell every agent its scope's team in the first prompt, so it knows which duties it carries ([SIZE-2]).

## SPAWN-4 Designer
roles: manager
when: design = yes
topic: spawning

Spawn the Designer only when `designer` is on `team:`. Spawn it after the plan names the UI tasks and before their Developers; retire it once every design is final ([START-5]).

## SPAWN-4a Architect
roles: manager
when: architecture = yes
topic: spawning

Besides the roles of [SPAWN-2b], spawn `architect` only when `architect` is on `team:`. Spawn it after the goal check and before the plan: before your task split or the plan. Retire it once `architecture.md` is `Status: final`; respawn it for a question on it.

## SPAWN-5b Developers, Team Lead
roles: team-lead
topic: spawning

Spawn a Developer with `squad-spawn dev <squad>-dev-<scope>-<n> --scope <scope> --repo <repo> [--base <ref>] --title "<id> words" --task <id> --prompt "<briefing>"`; `--task` claims the ticket for the Developer ([LC-27]); the name is at most 32 characters. Pass `--base` only with the ref the Manager checked and named in the iteration file ([GOAL-5]).

Reuse: when a Developer's next task in the scope has no parallel task running, give it the previous Developer's worktree and branch with `--worktree <previous worktree>` instead of `--repo` and `--base`. A task that runs in parallel gets a new worktree.

## SPAWN-6 The first prompt
roles: manager, team-lead
topic: spawning

The first prompt is the agent's only briefing. Include: its scope and folder, what it owns, the files to read first (the brief, and in a goal `goal.md` and `shared/`), and who it works with by name.

## SPAWN-7 Titles and labels
roles: manager, team-lead
topic: spawning

Pass `--title` when the agent has a specific task: a Developer gets the ticket id and a few words (for example `TAB-04 tab labels`), a checker the ticket it checks; leave it out otherwise.

When you point an agent at a new ticket, relabel it: `squad-label --agent <name> "<text>"` (`""` clears). Labels are display only: messages and `roster.md` use the address name.

## SPAWN-8b Retiring, Team Lead plans
roles: team-lead
topic: spawning

Retire a Developer with `squad-retire <agent-name>` after its task has passed: it asks the agent to save its notes, then closes its pane; its branch stays for the PO.

## SPAWN-9 Team Lead spawns only Developers
roles: team-lead
topic: spawning

Spawn and retire only Developers: no second Team Lead, no Tech Lead, BA, QA or Designer.

## SPAWN-10b Health checks, Team Lead plans
roles: manager
topic: spawning

Watch the Team Lead only; the Team Lead runs the pod's health checks.
- `herdr agent list`: is the Team Lead alive. Dead or stuck → respawn it from its notes; Developers keep running.
- Context filling (the Team Lead confused or repeating itself) → ask it to update its notes, retire it, respawn with the same name and a briefing that points at its notes and the plan file.
- Read `iterations/<n>.summary.md` for the retro and the check-in, never transcripts.

## SPAWN-11 A blocked pane
roles: manager
topic: spawning

A `blocked` pane (permission prompt or question) is the PO's to answer: each agent's own toast reaches them, and nobody relays it.

## SPAWN-12 Subagent model and effort
roles: manager
topic: spawning

Subagents you spawn default to `model: sonnet` and `effort: high` (Agent tool parameters, not your own model). Before each spawn pick model and effort for the task: gathering and exploring stay sonnet high; a judgment call may use opus or a higher effort. A fork is allowed when it helps; it runs on your model, so choose it on purpose.
