# Notes are missing between respawn lines

Status: needs-triage

Source: upstream-proposals retro (iterations/1.md, 1.summary.md Friction), 2026-11-24.

## Problem
At 18:34 the Team Lead, Tech Lead and QA blackbox had no notes file. The watchdog cannot save before the computer suspends (sleep mode suspended it with the pod open). A manual close at that point loses their state.

## Proposed fix
Write or refresh notes at each task close (PASS, FAIL, DECISION, STATUS passed), and have sleep mode ask for notes before it suspends.

## Comments
