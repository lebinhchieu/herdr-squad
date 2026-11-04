# Evidence 28: tasks from the scope's definition

## Behaviour
One function, `squadtickets.scope_tasks(scope_home, repo_root, name)`, now decides the tasks of a scope. Order: `tickets:` line, `.scratch/<scope>/issues`, the scope's `tasks/NN*.md` and `tasks/issues/NN-*.md`, a plan table. First source with a task wins; no guess from other scopes. The board reader, the scope picker and the report all call it. Rows gain `where`, `abs`, `ticket_status`. The Tasks panel has a "Where it lives" column (last, on by default) and the empty text "No task files found. Looked in: ...".

Live run (read-only), `python3 -c` calling `squadtickets.scope_tasks` on the real folders:
- `.claude/squads/accounts/scopes/cswitch-bg`: source `scope`, 4 tasks 01-04, status `done`.
- `.claude/squads/board/scopes/dashboard`: source `scratch`, 21 tasks (main repo `.scratch/dashboard/issues`).

## AC table
| Item | Shown by |
|---|---|
| T28.AC1/AC2 cswitch-bg 4 rows, title, where | tests/test_squadboard_tasks.py `ScopeFilesShape`; live run above |
| T28.AC3/AC5/AC12 source order, fall-through | tests/test_squadtickets.py `test_T28_TA1_source_order_and_fall_through` |
| T28.AC4/AC8 no other scope's folder | `test_T28_TA2_no_guess_from_other_scope` |
| T28.AC5 plan table, "plan table, plan.md" | `test_T28_AC14_drafts_and_plan_and_looked` |
| T28.AC6 status words and stages | `test_T28_TA5_status_word`; bin/squadboard_tasks.py `stage()` |
| T28.AC7 empty text with folders | panel_tasks.js draw(); `Tasks28` in test_squadboard_panels.py |
| T28.AC9 report same function | bin/squadtickets.py `find_tickets` adapter; test_squadreport_tasks.py (fixture `tickets: feat`) |
| T28.AC10 Where column default on | panel_tasks.js COLS; test_squadboard_panels.py Panels20 pins |
| T28.AC13 evidence folders, TEMPLATE, non-numbered not rows | `test_T28_TA1_...` (TEMPLATE.md, `03-evidence/`) |
| T28.AC14 dashboard drafts in `tasks/issues` | `test_T28_AC14_...` |
| T28.AC15 picker y = rows | bin/squadboard_list.py `_tickets` uses `scope_tasks` |
| T28.AC11 goal view rows carry scope + where | bin/squadboard_tasks.py row dict (scope set in `read`) |
| TA1 one rule | `grep -n "scope_tasks" bin/*.py`; test_T19_same_folder_rule_as_list |
| TA4 row keys | `ScopeFilesShape` |
| TA6 list agrees | `ScopeFilesShape` (`_tickets` -> done/handed in) |

## Open gaps
- A user's saved column list (board-ui.json) that lacks `where` hides it (`board.js` colFull is not in my files). It shows after "Reset columns".
- Plan source reads `plan.md` and `tasks/plan.md` only, not "the iteration plan the scope names".

## Tests changed on purpose
- test_squadtickets.py: old token-favour test kept (still true: `tickets:` line wins); "falls back" test still passes.
- test_squadboard_tasks.py `test_T19_same_folder_rule_as_list`: now compares `_tickets` with `scope_tasks`.
- test_squadreport_tasks.py `build()`: one line `tickets: feat`.
- test_squadboard_panels.py: Tasks column pins (7 -> 8 columns) in Panels12 and Panels20.
- None skipped.

## Tests run
`grep -rl "squadtickets\|_ticket_folder\|find_tickets\|_tickets\|panel_tasks\|No tasks yet" tests/` hits: test_squadboard_page, test_squadboard_panels, test_squadboard_tasks, test_squad_evidence, test_squadreport_ui, test_squadtickets. All run OK, plus test_squadboard_list, test_squadreport_tasks, test_windows_safe, test_no_bare_bash, test_old_language_inventory. (test_squad_evidence run below.)

## Return 1 (fc32dc4 + this commit)
QA whitebox 1-8: `.coach.md`/`.summary.md` refused (`NOT_TASK`); `TEXT_MAX` 256 KB cap on ticket and plan reads; `iterations/N.md` read newest first; `_plan_ids` deleted; tests: `test_T28_AC13_TA1_I_...`, `test_T28_TA13_TA1_H_...`, `Tasks28` (rendered DOM, untrusted title, empty state), real heads in `tests/fixtures/board/t28/`, layout C + symlink, goal rows, REV-8, picker y.
QA blackbox, design-v7 s5: label `Where`, column right after Title, Title bold + 2-line clamp + tooltip, no title = italic muted file name (`untitled` row flag), Where = muted folder + bold file name (`data-abs` for ticket 30; plan-table rows muted), dashed empty note with one line per source (`scope.md (tickets: line)` first).
Open: `Loading tasks…` and the 500 error note are drawn by `board.js` `renderPanel` (not my file; the panel's `render` is not called then). The Where click/link is ticket 30 (the cell carries `data-abs`).
Pins changed (Tasks column order/count): test_squadboard_panels Panels12, Panels20.
