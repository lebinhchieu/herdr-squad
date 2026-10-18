Status: ready-for-agent
Type: task
Task ID: 07
Touches: `bin/squadreport_query.py` (replaces 04's stub), `skills/squad-report/SKILL.md` (new), `skills/squad-report-analyze/SKILL.md` (new), `tests/test_squad_report_query.py` (new)
Does not touch: `bin/squad-report`, any other `bin/squadreport*`, `templates/report/*`, `skills/` other than the two new folders
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_report_query test_instructions test_templates`. Fixtures: a `data.json` from `report_fixtures` written to a temp scope. Read an existing skill (`skills/squad-process-update/SKILL.md`) and `tests/test_instructions.py` for the frontmatter and wording rules before writing.
Blocked by: 04. Parallel with 05, 06, 08, 09.

# 07: `query` command, `/squad:squad-report` skill, analyze skill

**Done when an agent can read the digest and drill into one slice without loading the whole `data.json`, and the PO can run the report from a chat command.** Business S8 (AC8.1-8.4), AC6.5.

## What
- `query <scope> digest|totals|tasks|roles|task|role|matrix|blocks|returns|iterations [--task X] [--role R] [--top N] [--refresh]`: compact lines (`--json` for JSON) from `data.json` only; `--refresh` runs `status` and, when not fresh, the build first. Output ASCII, no ANSI, bounded (default `--top 5`).
- `skills/squad-report/SKILL.md` (`/squad:squad-report <scope|goal|file list>`): runs the same command as the CLI (scope, goal or `rollup`), relays the path and the 5-line summary; writes nothing else. `disable-model-invocation` per repo convention for slash-only skills.
- `skills/squad-report-analyze/SKILL.md`: when `data.json` is fresher than the last message (`status` exit 0) read only `query digest`; otherwise run collect first (AC8.2); each finding cites its digest signal and proposes one change; drill-downs only through `query`; writes no file and never edits `process.md` (AC8.3). The text is short (read at every use): no rule repeated from `process.md`.

## Technical AC
1. `query` on the fixture returns the hand-computed digest order, `task X` row, `blocks` (longest 3, who waited on whom), `returns` (reason headline per return of the top task, AC4.5); `--top` bounds output; an unknown `what` or missing data exits 2 with a one-line message; stale data with no `--refresh` prints a first line `stale`.
2. It reads `data.json` only: running it with transcripts and squad folders deleted works.
3. Both skills pass the repo's skill/instruction tests (frontmatter, name = folder, referenced commands exist); the analyze skill text contains no write step (a test greps for `Write`/`Edit` instructions and `process.md` edits).
4. Real-output input: at least one test input is the real output of `squad-report` (a build of the 02/03 fixture scope through `squadreport_build.build`), not a hand-written `data.json`, so a renamed field fails here and not in production.
5. Primary behaviour only (qa: light).
