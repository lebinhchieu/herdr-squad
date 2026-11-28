# Cost rules

## COST-2 Reuse
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
topic: cost

Reuse a session on the same task until `fresh` fires ([COST-3]).

## COST-3 Fresh start
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
topic: cost

`squad-usage --check` fires `fresh` at your respawn line: 600k context, the same for every session; limits are absolute tokens, never a percent. Start fresh then, after a compaction, on a Stop-hook cost message, or when a new ticket or PO wait makes old context useless: write `roles/<you>.notes.md`, then `squad-respawn <you>`.

## COST-4a Tech Lead splits
roles: tech-lead
when: tech-lead = yes
topic: cost

The Tech Lead splits a task likely to need a respawn.

## COST-4b Plan and AC written, respawn
roles: tech-lead, team-lead
topic: cost

Respawn once your plan and AC are in files.

## COST-4c Tech Lead respawns
roles: tech-lead
when: tech-lead = yes
topic: cost

Respawn once your design and AC are in files.

## COST-5 Developer retires
roles: dev
topic: cost

Retire (no `squad-respawn`) when the hook says `fresh` with the ticket merged-ready, or when no open ticket touches your files. Mid-ticket respawn once; the Team Lead splits the rest. Never reuse a retired name.

## COST-16 Read your usage row
roles: dev, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
aware: manager
topic: cost

Run `squad-usage` in the same command as each `git commit`, `HANDIN`, `PASS`, `FAIL` or `DECISION` you send. Past your `line` column, save your findings or notes first, then act as [COST-3] says, or [COST-5] for a Developer. A Developer ends each `HANDIN` with `ctx <n>k`.

## COST-6b Ticket assignment, Team Lead
roles: team-lead
topic: cost

Before spawning for a ticket touching at most 2 files, give it to a live Developer under 80k. Give a ticket on files a live Developer already changed to that Developer while it has no `fresh` signal.

## COST-7 After a respawn
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
topic: cost

After a respawn read your notes and the files they name; your rules are already attached. Never read the whole spec again.

## COST-8 Manager reads its usage
roles: manager
topic: cost

The Manager is not exempt: after each pass, every PO message and before every spawn read your `squad-usage` row. On `fresh`, after a compaction or a cache expiry: write notes, run `squad-respawn` before your next spawn or PO reply. A hook adds one `context <n>k` notice to the result of your next `squad-spawn` or `squad-inbox add`; act on it then.

The hook does not watch the Manager between those calls. Read the `line` column of your `squad-usage` row: when `last ctx` is past it, write notes and run `squad-respawn`.

## COST-8b Long PO wait, Manager
roles: manager
topic: cost

Before a PO wait passes the 1h cache lifetime (`CACHE_TTL_S` in `bin/squadtranscript.py`), your notes are written and you are respawned lazily; the watchdog does it at 55 min idle over 50k (COST-15). Knowing the wait is long, run `squad-respawn --lazy` yourself at the next quiet point.

## COST-10b PO wait, Team Lead plans
roles: manager, team-lead
topic: cost

Before a PO wait (a merge, a check-in answer, a close), the Team Lead retires every pod role over 60k and respawns the roles the next iteration needs.

## COST-11 Step-up
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
topic: cost

On failure or escalation, consult the advisor first ([LC-25]). Effort may step up for that task only; a model never changes in a live session, only by respawn.

## COST-12 Messages point at files
roles: manager
topic: cost

Messages point at files. The Manager reads summaries, never transcripts.

## COST-13b Nothing left to do, Team Lead plans
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
aware: manager
topic: cost

A role with no open ticket and its deliverable file written (the iteration file, the final sha named, or its verdict posted) answers a fresh event from notes only and never runs `squad-respawn`; the Team Lead retires it once its work is accepted.

## COST-14b Short life, Team Lead plans
roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect
aware: manager
topic: cost

A role whose fresh event comes under 15 minutes after its previous respawn tells the Team Lead first; the Team Lead splits the remaining tickets or narrows what the role reads to the diff and the files its AC name.

## COST-15 Cold cache, watchdog restarts you
roles: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, architect, dev
aware: manager
topic: cost

Idle 55 min or more, context over 50k, work open: the watchdog prompts you once to write `roles/<you>.notes.md` (NOTE-1), one turn, then restarts you lazily. Under 50k you expire; with nothing open the Team Lead retires you (COST-13b); the Manager and Team Lead are restarted either way. Your first message after it is preceded by "read your notes".
