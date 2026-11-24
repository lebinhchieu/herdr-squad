# 03: Mod: `/squads` pane

Status: ready-for-agent
Type: task
Blocked by: 01
Touches: `hooks/squads/**` (not the fixtures from 01), `hooks/hooks.json`, `tests/test_hooks_json.py`, `tests/test_po_inbox_mod.py`
Read first: `$SCOPE_DIR/tasks/spec.md`, `design-notes.md`, `tech-ac.md` (same folder)

## Do
`Design: ui-design/squads-mod.md` (Status: final; copy only, nothing runs, no run output, no new pane), design-notes.md section 4, tech-ac.md T2.1-T2.12 (incl. T2.6b; no run branch), spec.md AC5-AC7. Use the `plugin-authoring` skill. LC-9: the two shared test files break when a second module is added; fix both. At hand-in save `hooks/squads/fixtures/real.json` from real `squad-tree --json` if 02 is merged, else say so.

## Hand-in for QA blackbox (cannot read code)
HANDIN names one command that prints the drawn pane as text for a given JSON file (`tree.json`, `tree-empty.json`, `real.json`) at a given rows x columns (cover 6/11/40 rows, 40/60/100 columns), plus the keys for copy, Esc back, filter and the refresh error. Show its output in `evidence.md`. Also `squad-tree --json` on a scratch squad must feed the same command.

## AC
The AC named above are the ticket's AC; both QAs check them. Test economy: targeted tests while building, one test per risk.

## Comments
