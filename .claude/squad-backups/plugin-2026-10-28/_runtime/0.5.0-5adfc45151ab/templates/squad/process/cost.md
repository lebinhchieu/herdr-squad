# Cost rules

## COST-1 The cost hook
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

A Stop hook (`squad-usage --check`) tells you when rule [COST-3] or [COST-9] fires and logs it to `usage-events.jsonl`. Limits are absolute tokens, never a percent. When a Stop-hook message says a cost rule fired, write `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md`, then run `squad-respawn $SQUAD_NAME`.

## COST-2 Reuse
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

Reuse a session while it stays on the same task and context is at most 120k.

## COST-3 Fresh start
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

Start fresh when context is over 120k, after a compaction, on a new task, or when a Stop-hook message says a cost rule fired: write `roles/<you>.notes.md`, then `squad-respawn <you>`.

## COST-4a Tech Lead splits
roles: tech-lead
when: size = L
topic: cost

The Tech Lead splits a task likely to need a respawn.

## COST-4b Plan owners respawn
roles: tech-lead, team-lead
when: size = L
topic: cost

Respawn once your plan and AC are in files.

## COST-5 Developer retires
roles: dev
when: size = L
topic: cost

Retire (no `squad-respawn`) at 120k with the ticket merged-ready, or when no open ticket touches your files. Mid-ticket respawn once, then the Team Lead splits the rest. Never reuse a retired name.

## COST-5a Developer retires, S and M
roles: dev
when: size in S, M
topic: cost

At 120k with the ticket merged-ready, or when no open ticket touches your files, retire (no `squad-respawn`). Mid-ticket, respawn once, then the Manager splits the rest. A retired name is never reused.

## COST-6a Ticket assignment, Manager in S and M
roles: manager
when: size in S, M
topic: cost

A ticket touching at most 2 files goes to a live Developer under 80k before a new spawn. A ticket on files a live Developer already changed goes to it while under 120k.

## COST-6b Ticket assignment, Team Lead
roles: team-lead
when: size = L
topic: cost

Before spawning for a ticket touching at most 2 files, give it to a live Developer under 80k. Give a ticket on files a live Developer already changed to that Developer while it is under 120k.

## COST-7 After a respawn
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

After a respawn read your notes and the files they name; your rules are already attached. Never read the whole spec again.

## COST-8 Manager reads its usage
roles: manager
topic: cost

The Manager is not exempt: after every DONE, every PO message and before every spawn read your `squad-usage` row. Over 100k, after a compaction or a cache expiry: write notes, run `squad-respawn` before your next spawn or PO reply. A hook adds one `context <n>k` notice to the result of your next `squad-spawn` or `squad-inbox add`; act on it then.

## COST-9 Idle
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

Idle over 1h with context over 100k: start fresh from notes.

## COST-10a PO wait, Manager in S and M
roles: manager
when: size in S, M
topic: cost

Before a PO wait (a merge, a check-in answer, a close), retire every pod role over 60k, and respawn the roles the next iteration needs.

## COST-10b PO wait, L
roles: manager, team-lead
when: size = L
topic: cost

Before a PO wait (a merge, a check-in answer, a close), the Manager retires every pod role over 60k; the Team Lead respawns the roles the next iteration needs.

## COST-11 Step-up
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

On failure or escalation, consult the advisor first ([LC-25]). Effort may step up for that task only; a model never changes in a live session, only by respawn.

## COST-12 Messages point at files
roles: manager
topic: cost

Messages point at files. The Manager reads summaries, never transcripts.

## COST-13a Nothing left to do, S and M
roles: qa-whitebox, qa-blackbox, designer
aware: manager
when: size in S, M
topic: cost

A role with no open ticket and its deliverable file written (QA: its verdict posted) answers a fresh event from notes only and never runs `squad-respawn`; the Manager retires it once its work is accepted.

## COST-13b Nothing left to do, L
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
aware: manager
when: size = L
topic: cost

A role with no open ticket and its deliverable file written (Team Lead: the iteration file; Tech Lead: the final sha named; QA: its verdict posted) answers a fresh event from notes only and never runs `squad-respawn`; the Team Lead retires it once its work is accepted.

## COST-14a Short life, S and M
roles: qa-whitebox, qa-blackbox, designer
aware: manager
when: size in S, M
topic: cost

A role whose fresh event comes under 15 minutes after its previous respawn tells the Manager first; the Manager splits the remaining tickets or narrows what the role reads to the diff and the files its AC name.

## COST-14b Short life, L
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
aware: manager
when: size = L
topic: cost

A role whose fresh event comes under 15 minutes after its previous respawn tells the Team Lead first; the Team Lead splits the remaining tickets or narrows what the role reads to the diff and the files its AC name.
