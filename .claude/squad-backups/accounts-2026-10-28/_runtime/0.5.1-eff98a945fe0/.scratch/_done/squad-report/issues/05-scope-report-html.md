Status: ready-for-agent
Type: task
Task ID: 05
Design: `/home/chieule/workspace/squad/.claude/squads/plugin/scopes/squad-report/ui-design/scope-report.md` (Status: final; mock `scope-report.html` next to it; read by absolute path, the worktree does not contain `.claude/`)
Touches: `bin/squadreport_html.py` (new), `templates/report/template.html`, `templates/report/report.css`, `templates/report/report.js` (all new), `tests/test_squadreport_html.py` (new)
Does not touch: `bin/squadreport_embed.py` (use it), `bin/squad-report`, `bin/squadreport_build.py` (it already imports `render_scope` lazily)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_html test_squad_report_cli`. UI check: `playwright-cli` over `file://` on reports built from `report_fixtures` (state fixtures below). Python-only in CI; no node, no browser in the suite.
Blocked by: 04. Parallel with 06, 07, 08, 09.

# 05: Scope report HTML

**Done when `squad-report <scope>` also writes one self-contained `report.html` matching the final design for every in-scope screen and state.** Business AC1.2-1.4, 1.7, S2, S3 views, 7.1-7.3, 4.3; spec → Technical → "Security and data rules". `Design:` AC: built UI matches the design: every screen and state.

## What
- `render_scope(data, out_dir)`: reads `templates/report/{template.html,report.css,report.js}` via `squadreport_embed`, writes `report.html` (atomic). One file, no external URL, font, script or request. Palette: Mango Parrot light only (tokens in the design file); colour encodings have a second cue.
- Tiers (the BA's cut): **Must** header, 6 KPI cards, digest, longest blocks, by-iteration, task table (sort + filter), role table (group-by-role of `roles[]`, agent and respawn counts), honesty labels ("derived", "estimated, list price"), banners (partial, attribution < 60%, missing transcript), empty/partial/missing states, return reasons (when present), drawer. **Could, build last and drop first if the Team Lead says so:** Task x role grid, agent timeline (idle > 1 h compressed with a true-scale toggle, PO-wait lane). Dropping a Could view leaves `matrix` and `segments` in the data.
- `report.js`: builds DOM with `textContent` / `setAttribute` only, never `innerHTML`; reads the embedded `<script type="application/json">`; keyboard-focusable sortable headers (Enter), drawer closes on Esc; print hides nav and drawer.
- States come from the data, not a query string: running (`partial`), flagged task (>= 3 returns), low attribution, missing transcript, empty scope, unreadable/newer schema (`schema_mismatch` card).

## Technical AC
1. Structure test: single file, no `http(s)://` and no `src=`/`href=` to a non-fragment URL; embedded JSON `==` `data.json`; the three template placeholders are all replaced.
2. XSS plant: a ticket title, an escalation title, a role name and a return reason set to `</script><img src=x onerror=alert(1)>` and `"><svg onload=1>`: the page's script tag still closes only once; in `playwright-cli` the planted text shows as text and no `alert`/network request fires (Developer evidence: screenshot + console log).
3. Developer evidence: a screenshot of each state fixture (done, running, flag, lowattr, missing, empty, schema_mismatch) and of the task drawer, listed in `dev-evidence.md` against the design's "States" table; deviations named.
4. Numbers: KPI and table cells equal `data.json` (a test reads the DOM-free `render` model, or QA spot-checks 3 cells per table); parallelism = `agent_s / wall_s`; every time figure carries "derived" and every dollar figure "estimated, list price"; `cost_reported_usd` line only when present (AC1.7).
5. `--redact` data: the page has no reason/title text and shows "not shared" where the design says so.
6. Reduced scope is allowed only with the Team Lead's `FINAL:` on the Could views.
7. Real-output input: at least one test input is the real output of `squad-report` (a build of the 02/03 fixture scope through `squadreport_build.build`), not a hand-written `data.json`, so a renamed field fails here and not in production.
8. **Timeline reconciles:** the lane/segment widths drawn and the 'longest blocks' list come from `data.json` as is; a test on a real build output asserts no drawn block is longer than its agent's bucket total.
9. Primary behaviour only (qa: light): QA blackbox opens the report from `file://`, checks the Must views and the 7 states.
