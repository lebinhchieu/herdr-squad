# Spawn events carry no start size

Status: needs-triage

Source: upstream-proposals Token Coach (iterations/1.coach.md, Plugin proposals), 2026-11-24.

## Problem
Developer first acts run 52-109k where the floor is 32-39k (rows dev-11 109k, dev-05 84k, dev-06 77k, dev-04 64k). Fourth scope with high Developer starts (warmcache, tl-always, fix-update coach files). No rule can name a cause, because the `spawn` event has no context size and `squad-usage` has no turns-before-first-edit.

## Proposed fix
Add `ctx` (first Stop-hook context) to the `spawn` event and a "turns before first Edit/Write" column to `squad-usage`. Ceiling saving about 1.4M per scope if all extra start is avoidable.

## Comments
