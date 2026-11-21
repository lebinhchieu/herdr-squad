# usage-events.jsonl: fresh carries ctx, line, turns; retire and spawn are logged
Status: needs-triage
Type: task
Source: tl-always Token Coach plugin proposal (ITER-15).

## Problem
A `fresh` with no later `respawn` cannot be told apart from a retire, and no event carries the context size (tl-always iterations/1.coach.md, plugin proposal 2; carried from fable-advisor and watchdog-shell).

## AC (draft)
- AC1 `fresh` events carry `ctx`, `line` and `turns`.
- AC2 `retire` and spawn-after-retire events are logged.
- AC3 `squad-usage` flags a `fresh` with no later `respawn` or `retire`.
- AC4 Version bump (SQ-5): plugin version 0.10.0 -> 0.10.1; `grep -rn '0\.10\.0' .claude-plugin/` prints no version line.

## Base dry run (SQ-15, main 432b8ea, Manager)
tests/test_squad_usage.py: OK, 26 tests. AC4 grep: `.claude-plugin/plugin.json:4: "version": "0.10.0"` on base (the bump changes it).

## Comments
