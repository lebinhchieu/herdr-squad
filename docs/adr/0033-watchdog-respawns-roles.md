# 0033: The watchdog respawns roles lazily before the cache goes cold

Status: accepted. Extends 0029 (the watchdog's idle test) and 0028 (goal-based idle test); neither text changes.

## Context
A session whose 1h prompt cache has expired pays 2x to rewrite its whole context on its next turn (**Cold cache**). The rules only told the Manager to respawn after a long PO wait, when the cache was already cold, and no role watched the clock.

## Decision
- The **Watchdog**, infrastructure and not a role, respawns roles, the Manager and the Team Lead included. When an agent's last main-thread turn is at least 55 min old (the idle of one agent, not of a **Home**) and its context is over 50k with work open, it prompts the role once to write `roles/<name>.notes.md` (NOTE-1), checks the file is newer than the prompt, then runs `squad-respawn <name> --lazy` (a **Lazy respawn**: no prompt; `bin/squad-lazy-hook` adds "read your notes" to the first message).
- The role holds the state and writes the notes; the watchdog verifies and restarts. A role-run `squad-respawn` is droppable (the role forgets) and unverifiable (nobody checks the notes exist).
- Exception to "a Team Lead may not respawn the Manager or another Team Lead" (0032): the watchdog starts inside an agent's env, so it scrubs `SQUAD_ROLE`, `SQUAD_NAME`, `SCOPE_DIR` and `GOAL_DIR` from the child's env and sets the home's own; `squad-respawn` then sees no role to refuse.
- Guards: notes newer than the prompt; blocked, background-shell and working agents skipped; at most 2 prompts then "gave up"; never `--force`; kill switch `SQUAD_WATCHDOG_COLD=0`. A context under 50k expires; a role with nothing open is reported to the Team Lead for retirement (COST-13b), not restarted.
- Rejected: each role runs `squad-respawn` itself on a prompt (see above).

## Consequences
- The Stop-hook and Manager-guard expiry notices stay as a safety net; `cache_expiries` stay in the report.
- A lazy respawn still logs `rule: respawn` (with `lazy: true`), so COST-5/COST-14 counters keep counting it.
- Rules COST-8b (rewritten) and COST-15 (new). A running watchdog keeps its old code until restarted; agents get the hook at their next respawn.
- Plugin 0.10.10; changelog v28.
