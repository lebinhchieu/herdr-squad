# 0028: The watchdog follows the goals file

Status: accepted. Supersedes the ticket-based idle test behind 0022 line 9 (the sleep reasons `all tickets passed`, `team idle with open tickets`); the reasons themselves stay.

## Context
The watchdog woke the Manager on every `passed` ticket and judged idleness from ticket states. A pass is the plan owner's business ([MSG-19]); the Manager heard it twice, or bypassed the Team Lead.

## Decision
- `<home>/goals.md` holds one row per PO request: `in progress`, `done` or `blocked` + reason. Only the Manager writes it ([START-19b], [FILE-6]).
- When nobody works and a goal is not `done`, the watchdog nudges the Manager at 5 and 15 minutes. When every goal is `done` it stops; `squad-watchdog ensure` restarts it.
- No goals file: ticket-based idle check as before.
- No `passed` wake. The Developer sends the plan owner `STATUS NN: passed <sha>`; the Team Lead tells the Manager only a goal done or blocked ([MSG-6]).
- Sleep-when-idle and the blocked-pane wake of 0022 are unchanged.

## Consequences
- The Manager is woken for an open goal, never for a ticket.
- A Manager who forgets to write a goal gets the old behaviour, not silence.
- Plugin 0.9.5; changelog v18.

Amended by 0030 (team-lead-always): the nudge goes to the scope's Team Lead; the goal's watchdog wakes the goal Manager only on `goals.md` events.
