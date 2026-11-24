# Evidence 03: plugin watchdog

## Behaviour

A scope with ticket 03 and two agents on a recorded herdr list (one agent of another squad, `other-dev-x`, is on the list too). The roster lists `t-dev-s1` twice and the log shows it once. Passes at 08:00, 08:05, 08:15 (ticket ready, nobody works), 08:20 (ticket done), 08:50 (the other squad still works), then 08:51, 08:55, 08:56, 09:30 (the other squad idle). The switch was turned on first with `squad-watchdog sleep on`; the suspend command was replaced by `echo SUSPEND-CALLED`, so no PC slept. `watchdog.log` after the run:

```
2027-01-15T08:00:00Z idle start: nobody works and work waits (03 ready). Agents: t-mgr-s1 idle, t-dev-s1 idle
2027-01-15T08:05:00Z nudge 5 min to t-mgr-s1: sent: WATCHDOG: nobody has worked for 5 minutes (since 08:00 UTC) and work is waiting. Waiting: 03 ready. Agents: t-mgr-s1 idle, t-dev-s1 idle. Message the agent who owns a ticket, or spawn one. If you only wait for the PO's answer, or a test run is going, you can ignore this.
2027-01-15T08:15:00Z nudge 15 min to t-mgr-s1: sent: WATCHDOG: still nobody working after 15 minutes (since 08:00 UTC). This is the last reminder of this idle period. Waiting: 03 ready. Agents: t-mgr-s1 idle, t-dev-s1 idle. Message the agent who owns a ticket, or spawn one. If you only wait for the PO's answer, or a test run is going, you can ignore this.
2027-01-15T08:20:00Z idle end after 20 min. Agents: t-mgr-s1 idle, t-dev-s1 idle
2027-01-15T08:56:00Z sleep pc: every ticket is done and nobody on this machine has worked for 5 min (the PO asked for sleep-when-done); the switch goes off, then the computer suspends
```

- The other squad worked until 08:50, so the 5 quiet minutes counted from 08:51 and the PC slept at 08:56, not at 08:25.
- `suspend.log` holds `SUSPEND-CALLED` once. The 09:30 pass did nothing: the switch had gone off (`watchdog.sleep` says `off`), so a wake-up does not sleep again.
- `squad-watchdog status` before `sleep on`: `sleep-when-done: off`; at the end: `last pass: 2027-01-15T09:30:00Z; idle since: -; sleep-when-done: off`.
- `tick` printed nothing on stdout. Without `sleep on` nothing sleeps (`test_the_pc_never_sleeps_unless_the_switch_is_on`).

No screenshots: there is no UI.
