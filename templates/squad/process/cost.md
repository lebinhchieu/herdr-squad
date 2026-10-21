# Cost rules

## COST-1 The cost hook
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

A Stop hook (`squad-usage --check`) tells you when rule [COST-3] or [COST-9] fires and logs it to `usage-events.jsonl`. Limits are absolute tokens, never a percent. When a Stop-hook message says a cost rule fired, write `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md`, then run `squad-respawn $SQUAD_NAME`.

## COST-2 Reuse
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

Reuse a session while it stays on the same task and context is at most 120k.

## COST-3 Fresh session
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, dev
topic: cost

Start fresh when context is over 120k, after a compaction, on a new task, or when a Stop-hook message says a cost rule fired: write `roles/<you>.notes.md`, then `squad-respawn <you>`.

## COST-4a Tech Lead splits
roles: tech-lead
topic: cost

The Tech Lead splits a task likely to need a respawn.

## COST-4b Plan owners respawn
roles: tech-lead, team-lead
topic: cost

Respawn once your plan and AC are in files.

## COST-5 Developer retires
roles: dev
topic: cost

A Developer retires at 120k or when no open ticket touches its files; its name is never reused.

## COST-6a Ticket assignment, Manager in S
roles: manager
when: size = S
topic: cost

A ticket touching at most 2 files goes to a live Developer under 80k before a new spawn. A ticket on files a live Developer already changed goes to it while under 120k.

## COST-6b Ticket assignment, Team Lead
roles: team-lead
when: size in M, L
topic: cost

Before spawning for a ticket touching at most 2 files, give it to a live Developer under 80k. Give a ticket on files a live Developer already changed to that Developer while it is under 120k.

## COST-7 After a respawn
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

After a respawn read your notes and the files they name; your rules are already attached. Never read the whole spec again.

## COST-8 Manager reads its usage
roles: manager
topic: cost

The Manager is not exempt: after every DONE, every PO message and before every spawn it reads its `squad-usage` row; over 100k, after a compaction or a cache expiry it writes notes and runs `squad-respawn` before its next spawn or PO reply.

## COST-9 Idle
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

Idle over 1h with context over 100k: start fresh from notes.

## COST-10a PO wait, Manager in S
roles: manager
when: size = S
topic: cost

Before a PO wait (a merge, a check-in answer, a close), retire every pod role over 60k, and respawn the roles the next iteration needs.

## COST-10b PO wait, M and L
roles: manager, team-lead
when: size in M, L
topic: cost

Before a PO wait (a merge, a check-in answer, a close), the Manager retires every pod role over 60k; the Team Lead respawns the roles the next iteration needs.

## COST-11 Step-up
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer
topic: cost

Step up one notch of model or effort only on failure or escalation, for that task only.

## COST-12 Messages point at files
roles: manager
topic: cost

Messages point at files. The Manager reads summaries, never transcripts.
