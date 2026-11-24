# Sleep mode suspends the PC with open tickets and live agents over 50k

Status: needs-triage

Source: upstream-proposals Token Coach (iterations/1.coach.md, Plugin proposals), 2026-11-24.

## Problem
`sleep pc` suspended the machine at 2026-11-23T22:12:53Z with the pod mid-check (`watchdog.log`: "team idle with open tickets"); idle ended after 717 min. 7 of the 8 cache expiries of the scope came from that gap. A suspended machine does not run the watchdog, so COST-15 never fired.

## Proposed fix
Before `sleep pc`, run the COST-15 path for every agent over 50k (notes written, lazy respawn), or do not suspend while a ticket is open or a check runs. Saving about 0.4M input-equivalent per such suspend. Related: `plugin-followup-notes-cadence.md`.

## Comments
