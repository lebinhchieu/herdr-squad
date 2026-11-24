# 08: Event wake-up for the plan owner
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: B (after 07)
Files: `bin/squad-watchdog` and/or `hooks/hooks.json` + a new hook script, tests
Source: idea 9. First read `squad-watchdog` (it nudges the Manager when idle) and `squad-task`; extend, do not duplicate.

## Business AC
1. On a ticket state change to `passed`, on a 3rd return, and when a pane is `blocked` for more than 10 minutes, the plan owner gets one message (event name, ticket, shas). No message when nothing changed. Never more than one message per event.
2. It never relays a permission prompt or approves anything (MSG-10, SAFE-1b): a blocked-pane message says "Chieu's to answer".
3. Off switch: same style as `squad-watchdog sleep on|off`; default on only for the Manager of the scope.
4. Tests for each event and for the no-repeat guard.
