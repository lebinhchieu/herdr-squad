Status: ready-for-agent
Type: task
Task ID: 19
Touches: `templates/report/report.css` (`section h2` 17px→16px, line ~28), `templates/report/report.js` and `bin/squadreport_digest.py` only for the three small items below, matching tests
Does not touch: schema, anything else
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_ui test_squadreport_collect test_squadreport_html test_squadreport_digest test_squadreport_rollup test_squadreport_rollup_ui test_squadreport_tasks test_squadreport_embed test_squad_report_cli`
Blocked by: 17 (start on 17's last QA-whitebox-passed sha; Tech Lead confirms the base)

# 19: Integration of 14-18 and small leftovers

**Done when** one branch holds tickets 14-18 and the leftovers below, targeted tests green, handed to the Tech Lead for the full `--tz` run.

## What
1. Branch from 5aa4bcb (ticket 17 tip, linear chain 14>15>16>17; Tech Lead confirms if 17 gets a new sha). `git merge ee0abba` (ticket 18, files disjoint; no conflict expected). Run `git merge-base --is-ancestor` for both and quote the output.
2. Leftovers (Tech Lead FINAL), each with a test, only where the mock differs, skip any needing a data-shape change:
   - QA whitebox AC17: merge the two `report.css` rules `.digest button` and `.digest>li>div` into one (no overlapping props, no behaviour change).
   - Overview `section h2` 17px → 16px (`report.css:28`).
   - "1 escalations" grammar → singular.
   - "roles · dev" digest sub-line; idle_share / parallelism cards sharing one sub-line.
3. Targeted tests (Harness) green. Do NOT run the full suite.
4. Hand in to Tech Lead (HANDIN 19, branch + sha, cc team lead); QAs re-check only the leftovers diff. Screenshot the Overview at 1440x900 vs mock `?state=done`, save in `.claude/squads/plugin/scopes/report-ui-fix/evidence/19/dev-evidence.md`.
