# 09 Fresh check also runs at a tool boundary

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/01-fresh-fires-late.md`, Token Coach proposal 1)
Blocked by: 10, 11
Aim: Agents get the respawn notice during long tool runs
Estimate: 2h
Depends on: 10, 11

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/09.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead.
Files: `bin/squad-usage-hook`, `hooks/hooks.json`, README row `squad-usage` (Stop hook text), `tests/test_squad_usage_hook.py`, `tests/test_hooks_json.py`

## Problem
The `fresh` check runs only in the Stop hook. An agent that makes many tool calls in one turn never stops, so `fresh` fires late or never: a Developer ended 70k over its line, and a Tech Lead session reached 417k with no `fresh`. Base: `hooks/hooks.json` has `squad-usage-hook` under Stop only.

## Change
`squad-usage-hook` reads `hook_event_name`. On `PostToolUse`: the same exemptions as Stop (Manager, no scope, `stop_hook_active`), then a throttle: stat the transcript, read the stamp `<home>/roles/<agent>.usage-check` (one JSON line: ts, session, size, ctx, line, overwritten), and run `squad-usage --check-detail` only when the transcript grew at least 65,536 bytes since the stamp (about 7k tokens) or there is no stamp. Write the stamp after every run, and from the Stop path too, so a miss shows as an old `ts`. A `fresh` result goes through the existing once-per-session dedupe and the same `usage-events.jsonl` record. On PostToolUse the notice is JSON `hookSpecificOutput.additionalContext`, exit 0; on Stop it stays exit 2. Fail open everywhere. `hooks.json` gets one PostToolUse entry, no matcher, `timeout` 10. Running agents get it at their next session start.

## AC
- AC1: `hooks.json` has exactly one `squad-usage-hook` entry under PostToolUse and the Stop one is kept (base: 0 and 1).
- AC2: PostToolUse input, transcript past its line, no prior record: stdout JSON with `additionalContext` naming `fresh`, exit 0, one `fresh` record; a second call prints nothing and leaves one record.
- AC3: transcript grown under 65,536 bytes since the stamp: `squad-usage` is not run (stamp unchanged).
- AC4: Manager role, unknown session, missing transcript: exit 0, no output.
- AC5: after a PostToolUse run and after a Stop run the stamp holds ts, size, ctx, line.
- AC6: the 13 existing Stop tests still pass. Latency: 100 skipped PostToolUse calls on a 1 MB fixture finish in under 10 s in total (about 100 ms each); `## Behaviour` quotes the measured figure.

## Comments
