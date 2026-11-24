# Task 17: squad-respawn logs a respawn event

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Source of the change: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. No version bump in this task (it rides the last task of the goal's last scope, SQ-5).

Status: ready (after 16, same worktree)
Source: finding 5 of the review. COST-14 ("under 15 minutes after the previous respawn") cannot be checked without it.
Files: bin/squad-respawn, tests/test_squad_respawn.py; read `bin/squad-usage-hook` only to match the `usage-events.jsonl` line shape
Ticket: commit this file's content as `.scratch/process-fixes/issues/17-respawn-event-log.md` in your first commit.
Base: your worktree after task 16. No merge.

## AC
- AC1 Before it starts the new session, `squad-respawn` appends one line `{"rule": "respawn", "agent": <name>, "ts": <UTC ISO>}` to the scope's (else goal's) `usage-events.jsonl`, same file and shape rules as the usage hook.
- AC2 No line when the run is refused (AC1 of task 16) or fails before the spawn; `--dry-run` logs nothing.
- AC3 `squad-usage-hook` and `squad-manager-guard` (the only readers of `usage-events.jsonl`; `squad-report` is not one) still read the file with the new line in it (a test with a mixed file).
- AC4 One test per AC.

## Technical AC (QA whitebox, plugin-qaw-respawn-guard, 2026-11-11; Developer: reply in `## Review` or `ASK 17` if you disagree)
- T1 Shape. The appended line is valid JSON on one line: `{"ts": "<YYYY-MM-DDTHH:MM:SS.mmmZ>", "agent": <name>, "rule": "respawn"}` plus the `role` field if cheap (the usage hook writes `ts, agent, role, session, rule, action`). `ts` uses the hook's exact format (`date -u +%Y-%m-%dT%H:%M:%S.%3NZ`); the test matches it with a regex. Build the JSON with `jq -nc --arg` (never string concatenation: a name is data).
- T2 File. Path is `$home/usage-events.jsonl` (the same `$home` the script already picks: scope, else goal, else squad dir). Created if missing. Append, never rewrite: existing lines stay byte-identical (the test compares the old lines before/after).
- T3 Locking. Same append discipline as `bin/squad-usage-hook` (flock where present, else the mkdir lock). Reuse by sourcing or copy of the same short block; a plain `>>` is not enough. A test with the lock path held (`usage-events.jsonl.lock` as a directory) still ends in a written line and exit 0 is not required to be fast but must not hang over ~10 s. If the Developer shows `flock` is on PATH in the test env, one test with `flock` hidden from PATH (or the no-flock branch exercised) covers the second branch.
- T4 Order. The line is written after the notes check (task 16) and after `old_pane` is found (a missing live agent is a refusal, no line), and before the `squad-spawn` call. Test: a spawn that fails (the existing failing-spawn fixture) leaves the line written; the AC2 text "no line when it fails before the spawn" is met by: refused (missing notes), `no live agent`, `--dry-run`, and a hand-off (a pinned run logs nothing from this script; the pinned script is the engine). Four assertions across at most two tests; state in `## Review` which is which. If the Developer reads AC2 differently for a failing spawn, send `ASK 17` before coding.
- T5 Logging failure never blocks a respawn: an unwritable log (a directory named `usage-events.jsonl`, or a read-only home) prints at most one warning on stderr and the respawn goes on, exit 0. One test.
- T6 Readers (AC3). The real readers of this file today are `bin/squad-usage-hook` (jq dedupe) and `bin/squad-manager-guard` (`seen_keys`). `bin/squad-report` and its `squadreport*.py` do not read the file (QA whitebox grep: `grep -rn usage-events bin/` shows none); the Developer re-runs that grep and says so in `## Review`. One test with a mixed file (a hook line, a guard line, the new respawn line, plus the new line has no `session`) shows: the Stop hook still fires and dedupes the same rule for its own session, and the Manager guard's `seen_keys` result is unchanged. Do not change either reader.
- T7 No change to the dry-run output text, to the hand-off, or to any other file than `bin/squad-respawn`, `tests/test_squad_respawn.py` and the `.scratch` ticket. No version bump.
- T8 SQ-10. As task 16 T9 (`tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`, `tests/test_squad_respawn.py`, `tests/test_squad_usage_hook.py`, `tests/test_squad_manager_guard.py`), results quoted in `## Behaviour`.
- T9 One test per AC1-AC4 (test economy); T5 is the only extra and is a real regression risk (a log problem must not strand an agent without a fresh session).
