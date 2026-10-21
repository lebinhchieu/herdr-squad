# Spawning and retiring

## SPAWN-1 The spawn command
roles: manager, team-lead
topic: spawning

Spawn with the `squad-spawn` command (on your PATH from this plugin): `squad-spawn <role> <agent-name> --scope <scope> [--repo DIR [--base REF]] [--title "<text>"] [--prompt "first message"]`. The scope is yours (`$SQUAD_SCOPE`), or the scope you are running inside the goal.

## SPAWN-2a Roles the Manager spawns, S
roles: manager
when: size = S
topic: spawning

You spawn `tech-lead`, `dev`, `designer` (only with `design: yes`) and `token-coach` (only when the PO asks, [ITER-6a]).

## SPAWN-2b Roles the Manager spawns, M and L
roles: manager
when: size in M, L
topic: spawning

You spawn `ba`, `team-lead`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer` (only with `design: yes`) and `token-coach`. The Team Lead spawns Developers.

## SPAWN-3 Size in the first prompt
roles: manager
topic: spawning

Tell every agent its scope's size in the first prompt, so it knows which duties it carries ([SIZE-2]).

## SPAWN-4 Designer
roles: manager
when: design = yes
topic: spawning

Spawn the Designer only when `scope.md` has `design: yes`, and never suggest it to the PO. Spawn it after the Tech Lead's plan names the UI tasks and before their Developers; retire it once every design is final ([START-5]).

## SPAWN-5a Developers, Manager in S
roles: manager
when: size = S
topic: spawning

Developers always get `--repo <code repo>` so they work in their own git worktree `.worktrees/<squad>/<scope>/<agent>` on branch `squad/<squad>/<scope>/<agent>`. Take the repo from the task's `repos` and `project.md`. `--base <passed branch or commit>` starts the branch from work that is passed but not merged ([GOAL-5]).

## SPAWN-5b Developers, Team Lead
roles: team-lead
when: size in M, L
topic: spawning

Spawn a Developer with `squad-spawn dev <squad>-dev-<scope>-<n> --scope <scope> --repo <repo> [--base <ref>] --title "<id> words" --prompt "<briefing>"`; the name is at most 32 characters. Pass `--base` only with the ref the Manager checked and named in the iteration file ([GOAL-5]).

## SPAWN-6 The first prompt
roles: manager, team-lead
topic: spawning

The first prompt is the agent's only briefing. Include: its scope and folder, what it owns, the files to read first (the brief, and in a goal `goal.md` and `shared/`), and who it works with by name.

## SPAWN-7 Titles and labels
roles: manager, team-lead
topic: spawning

Pass `--title` when the agent has a specific task: a Developer gets the ticket id and a few words (for example `TAB-04 tab labels`), a checker the ticket it checks; leave it out otherwise.

When you point an agent at a new ticket, relabel it: `squad-label --agent <name> "<text>"` (`""` clears). Labels are display only: messages and `roster.md` use the address name.

## SPAWN-8a Retiring, Manager in S
roles: manager
when: size = S
topic: spawning

Retire with `squad-retire <agent-name>`: it asks the agent to save its notes, then closes its pane. Developers retire after their task is done; their branch stays for the PO.

## SPAWN-8b Retiring, Team Lead
roles: team-lead
when: size in M, L
topic: spawning

Retire a Developer with `squad-retire <agent-name>` after its task is done: it asks the agent to save its notes, then closes its pane; its branch stays for the PO.

## SPAWN-9 Team Lead spawns only Developers
roles: team-lead
when: size in M, L
topic: spawning

Spawn and retire only Developers: no second Team Lead, no Tech Lead, BA, QA or Designer.

## SPAWN-10a Health checks, Manager in S
roles: manager
when: size = S
topic: spawning

Check every time you get a message and at least between iterations:
- `herdr agent list`: who is `working`, `idle`, `blocked`, or gone.
- Idle with work assigned → send `ASK <name>: STATUS?`.
- Looping (the same two agents exchanging messages on one topic past 2 rounds) → step in, decide or route to the owner.
- Context filling (a long-running agent getting confused or repeating itself) → ask it to update its notes, retire it, respawn with the same name and a briefing that points at its notes.

## SPAWN-10b Health checks, Manager in M and L
roles: manager
when: size in M, L
topic: spawning

Watch the Team Lead only; the Team Lead runs the pod's health checks.
- `herdr agent list`: is the Team Lead alive. Dead or stuck → respawn it from its notes; Developers keep running.
- Context filling (the Team Lead confused or repeating itself) → ask it to update its notes, retire it, respawn with the same name and a briefing that points at its notes and the plan file.
- Read `iterations/<n>.summary.md` for the retro and the check-in, never transcripts.

## SPAWN-11 A blocked pane
roles: manager
topic: spawning

A `blocked` pane (permission prompt or question) is the PO's to answer: each agent's own toast reaches them, and nobody relays it.
