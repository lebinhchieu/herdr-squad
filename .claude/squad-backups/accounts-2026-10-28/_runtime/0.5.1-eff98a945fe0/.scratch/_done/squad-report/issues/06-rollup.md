Status: ready-for-agent
Type: task
Task ID: 06
Design: `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/squad-report/ui-design/rollup.md` (Status: final; mock `rollup.html` next to it; read by absolute path)
Touches: `bin/squadreport_rollup.py` (replaces 04's stub: data + page), `templates/report/rollup.html`, `templates/report/rollup.css`, `templates/report/rollup.js` (all new; the palette variables are copied from the design, `report.css` is not edited), `tests/test_squadreport_rollup.py` (new)
Does not touch: `bin/squad-report`, `bin/squadreport.py`, `bin/squadreport_tasks.py`, `bin/squadreport_html.py`, `templates/report/{template.html,report.css,report.js}` (05's), `bin/squadreport_embed.py` (use it)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_rollup test_squad_report_cli`. Inputs are `data.json` files written by `report_fixtures` (several squads/scopes); no transcript, no squad folder.
Blocked by: 04. Parallel with 05, 07, 08, 09.

# 06: Rollup over a list of `data.json` files (and a goal)

**Done when `squad-report rollup <data.json>...` and `squad-report <goal>` write `index.html` + `data.json` (kind rollup) built from the given files only.** Business S5 (AC5.1, 5.3-5.8), AC6.2 data side; spec → Technical → "Round-3 follow-ups" and the rollup schema.

## What
- `run(argv)` implements `rollup <files|folder>... [--out DIR]`, default `--out ./squad-rollup/`; goal form resolves the goal's scopes' `report/data.json` in the squad (scope without one: status `no_data`, row lists the command to create it, totals partial). Everything else comes from the files: key `(scope.squad, scope.name)`; duplicate key keeps the newest `generated_at` and lists the other as `skipped`; wrong `schema_version` or `kind`, unreadable or non-JSON = `schema_mismatch`/`skipped` with the reason; totals marked partial; the run never fails because of one bad file (exit 0; exit 2 only when no file is usable).
- `report_href`: relative link to a `report.html` beside the file when it exists, else null (disabled "no report" state). `--redact` files show "not shared" in reason/title columns. Different `config.prices` -> "mixed price tables" note, each file's own `cost_usd` summed.
- Page per the design: KPIs, scopes table (totals footer), share bars, role x scope grid, per-scope 60% attribution banner; the "When" calendar strip is a Could view (drop first). Same security rules as 05 (embed helper, `textContent` only).

## Technical AC
1. Fixture of 5 files: ok, ok from another squad with the same scope name, duplicate key (older), wrong `kind`, garbage JSON, plus one `--redact` file and one with other prices: the table has the right rows/statuses, the skipped ones list a reason, totals are partial and equal the sum of the ok files only (hand-computed).
2. Nothing but the given files is opened: the test removes the squad and transcript folders and runs from another cwd; no absolute path appears in the output.
3. Goal form: a squad with a goal of 3 scopes, one without `data.json` -> `no_data` row with the command, others summed; same output code path as the file form (one function).
4. XSS plant in a scope name and title in the input files, same assertions as 05 AC2 (structure test; screenshot evidence of states normal, mixed, files, single, empty, error from the design's State table).
5. `report_href` is relative, null when no `report.html` sits beside the file, and survives moving the rollup folder with its inputs (test with a relative layout).
6. Reduced scope: the calendar strip may be dropped on the Team Lead's `FINAL:`.
7. Real-output input: at least one test input is the real output of `squad-report` (a build of the 02/03 fixture scope through `squadreport_build.build`), not a hand-written `data.json`, so a renamed field fails here and not in production.
8. Primary behaviour only (qa: light).
