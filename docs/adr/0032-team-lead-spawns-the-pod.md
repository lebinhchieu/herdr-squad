# 0032: The Team Lead spawns, respawns and retires the pod

Status: accepted (tl-spawns-pod; Chieu confirmed the team, plan and open points at E1 (c) on 2026-11-22)

Amends 0010 and 0030: "the Team Lead spawns and retires Developers only" no longer holds. Overrides the Manager-spawns-the-pod line of 0010.

**Decision:** with a Team Lead on the team (always), the Team Lead spawns, respawns and retires every role on `team:` (BA, Tech Lead, QA whitebox, QA blackbox, Designer, Architect) and the Developers. The Manager spawns only the Team Lead and, at the close, the Token Coach, and watches the Team Lead. The Team Lead never spawns, respawns or retires `manager`, `token-coach` or another `team-lead`.

**Why:**
- COST-10b already told the Team Lead to respawn the roles the next iteration needs, but `squad-spawn` and `squad-retire` let it touch only `dev`, so it had to ask the Manager to respawn both QAs (tl-wake-status).
- One owner for the pod's sessions: the Team Lead already routes the pod, sees its context and runs its health checks.

**Consequences:**
- Enforcement: `squad-spawn`, `squad-retire` and `squad-respawn` refuse the three never-roles when `SQUAD_ROLE=team-lead`; a spawn under a name that has a roster row must carry that row's role (else a never-role is reachable through a dead Manager's name); the `team:` gate still refuses a role not on the team; `settings/team-lead.json` allows `squad-spawn` per allowed role only (defence in depth, the scripts decide).
- A late role (SIZE-13): the Manager runs `squad-team add` and writes the `## Handover`; the Team Lead spawns the joiner and respawns the roles `squad-team` lists. Designer and Architect still need the PO's yes first.
- Roster: `squad-spawn` adds the row; whoever spawned an agent fills its Owns and Status; the Manager keeps its own row and the Team Lead's.
- A home runs the scripts, rules and settings of its pin (the pinned runtime's `bin/` leads each agent's `PATH`), so the change takes effect only where the home's pin is 0.10.5 or later: after the plugin update the PO runs `/squad:squad-process-update` (squad upgrade, then `squad-process homes --apply --yes`), which moves the pins and respawns the live agents. A bare respawn under the old pin changes nothing.
- Known limit: a Team Lead can spawn a second live copy of a role under a fresh name (cost, not security); not guarded.
- Known limit: the Architect is spawned before the plan, so the Manager spawns the Team Lead first when an Architect is on the team; not exercised in tl-spawns-pod.

**Alternatives rejected:**
- Allow-list the seven roles in each script: three scripts to keep in step, no gain over refusing the three never-roles.
- Let the Team Lead spawn the Token Coach: the Token Coach reads the whole scope at the close and is the Manager's (ITER-6).
- Keep the Manager as the spawner of QAs and respawn them on the Team Lead's ask: the round trip COST-10b was written to avoid.
