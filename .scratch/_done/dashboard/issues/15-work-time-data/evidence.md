# Evidence 15 work time data

## Behaviour
Reader `bin/squadboard_worktime.py` (route `/api/worktime`, found by the `ROUTE` discovery of ticket 03). Tests: `tests/test_squadboard_worktime.py` (21 tests, id in each name). Samples: `tests/fixtures/board/worktime/` (`normal.jsonl`, `long-gap.jsonl`, README).

| AC | What I saw |
|---|---|
| T15.AC1 | Dev on task 03 for 2 h: working 3600 s + waiting 1800 s + idle 1800 s = 7200 s, equal to `squadreport._sum_segs` for the same segments. Real normal sample: the four buckets equal the report. |
| T15.AC2 | Time with no task is `{"seconds","hours","minutes","label":"1 h 0 min"}`; the JSON text of the payload holds no `%`. Live run on this scope (3 days): total unattributed `6 h 51 min`. |
| T15.AC3 | Every piece with a task has `approx: true`; idle and untasked pieces `false`. Marks carry exactly `ts, kind, agent, task` (commit marks `ts, kind, sha`): no `approx`. |
| T15.AC4 | Agent with no transcript: `{"agent": "ghost", "pieces": [], "note": "no transcript: ghost"}`, no `totals`, no time taken from its messages; `unknown` lists `transcript`. |
| T15.AC5 | Sample with a `system` record ending a 11.2 h gap: that piece is `working`, `collapsible: true`, and sits in `collapsed_s`, not in `counted_s.working` (under 1 h). |
| T15.AC6 | Idle gap of 12 h across Europe/Berlin (2026-10-25) and America/New_York (2026-11-01) with `TZ` set: 43200 s and label `12 h 0 min` both times. Seconds come from UTC epochs. |
| T15.AC7 | `from`/`to` clip the pieces (600..1200 gives pieces starting at 600 and ending at 1200); a range with no data gives `[]`; `from >= to` or non-numeric gives `{"refused": 400, "error": ...}`; no choice gives `refused 400 "selection required"` (the server also answers 400 before the reader runs). |

Technical points: pieces are unfiltered (a 5 s piece is kept; `_segments` with 30 s drops it). `gap_min` is clamped to 15..240 (14 gives 15, 241 gives 240, text gives 60). Waiting and blocked pieces never collapse. Commit marks come from `git log` on `squad/<squad>/<scope>/*`; with `git` missing: no commit marks and `unknown: ["git"]`. Broken sources (truncated last JSONL line, bad messages line, no git) do not raise.

Cost, live, this scope (20 agents, 3-day range): cold 2.0 s, warm 0.02 s (memory cache by file mtime + size; a test shows a grown transcript is read again). Nothing is written (test snapshots the folder).

Not done, by design: `worktree` and `branch` stay empty (M10); no `unfiltered` edit of `squadreport_tasks.py` was needed (pieces are built from `collect` segments), so that file is unchanged. A still-open piece is not stretched to `now`; every piece has `open: false`.
