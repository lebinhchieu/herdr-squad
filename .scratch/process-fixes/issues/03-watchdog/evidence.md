# Evidence 03: plugin watchdog

## Behaviour

A scope with tickets 03 (ready) and 04 (building); the Manager, the Developer are idle and QA is blocked. Three passes at minute 0, 5 and 15 (`W.tick` with a recorded herdr file; the Manager message is captured, not sent). `watchdog.log` after the run:

```
2027-01-15T08:00:00Z idle start: nobody works and work waits (03 ready, 04 building). Agents: t-mgr-s1 idle, t-dev-s1 idle, t-qa-s1 blocked
2027-01-15T08:05:00Z nudge 5 min to t-mgr-s1: sent: WATCHDOG: nobody has worked for 5 minutes (since 08:00 UTC) and work is waiting. Waiting: 03 ready, 04 building. Agents: t-mgr-s1 idle, t-dev-s1 idle, t-qa-s1 blocked. Message the agent who owns a ticket, or spawn one. If you only wait for the PO's answer, you can ignore this.
2027-01-15T08:15:00Z nudge 15 min to t-mgr-s1: sent: WATCHDOG: still nobody working after 15 minutes (since 08:00 UTC). This is the last reminder of this spell. Waiting: 03 ready, 04 building. Agents: t-mgr-s1 idle, t-dev-s1 idle, t-qa-s1 blocked. Message the agent who owns a ticket, or spawn one. If you only wait for the PO's answer, you can ignore this.
```

Sleep: with no `watchdog.sleep` file nothing is retired, even for a done ticket and 30 idle minutes (`test_nothing_sleeps_unless_the_po_named_the_agent`). No screenshots: there is no UI.
