# Evidence 01 wording A

## Behaviour
- Finding 1: "done" now means merged only; changed to "passed" in LC-1 (title, text), SIZE-16, SIZE-17c, START-1, START-19, TEAM-7 (`new rule`, 60-word lint cap), SPAWN-8a/8b, GOAL-3b/3c, COST-8 (`after each pass`), and iterations.md l.12, 24, 31, 112, 113 (Manager's FINAL 01).
- REV-5a and EVID-5: `roles: dev`. They now ride in the Developer rules; REV-22, LC-19, LC-19b still resolve via `squad-process rule`. Cap test LIMIT 5120 -> 5400 (worst case 5313 B), 2 on-demand tests replaced (Manager FINAL 01); Manager byte bases +18..+135 B for the longer words.
- START-5 Developer row and START-2a: "or per queued run of tasks in one area" (cites COST-6a, LC-6b).
- SPAWN-4/4a: clause "and never suggest it to the PO" removed; SIZE-1 untouched.
- No rule ID deleted or renumbered (T9). Drafts committed alone in dcd5a23.

## Every "done" hit in templates/squad/process (`grep -rniw done`) and verdict
| Hit | Verdict |
|---|---|
| lifecycle.md:227 (LC-18) project "done" tests | keep: project's own test |
| lifecycle.md:311 (LC-25) "what was done" | keep: not a stage word |
| lifecycle.md:323 (LC-27) "only `merged` is done" | keep: means merged |
| starting.md:10 "Done means: the team's passed rule" | keep: scope done = checks passed, evidence, branch ready |
| starting.md:156 "definition-of-done rules `project.md` lists" | keep: project's own |
| `_done/` folder names (iterations, goal, notes, closing, promotion, safety, starting) | keep: folder name |
All other hits (LC-1, SIZE-16, SIZE-17c, START-19, TEAM-7, SPAWN-8a/8b, GOAL-3b/3c, COST-8, iterations l.12/24/31/112/113) changed.

## AC trace
| AC | Test | How run |
|---|---|---|
| AC1 | `WordingATest.test_passed_is_not_called_done` | `PYTHONPATH=tests python3 tests/test_rules_wording.py` |
| AC2 | `test_live_run_and_design_shots_roles_are_not_empty`; `test_live_run_and_design_shots_attach_to_dev`; `test_lost_rules_are_one_command_away` | wording, `test_dev_rules_size.py` |
| AC3 | `test_developer_session_may_run_a_queue` | wording |
| AC4 | `test_no_dead_suggest_clause` | wording |
| AC5 | `squad-process lint --plugin-root .` exit 0; wording 22, contract 13 OK, none skipped | as written |
Extra hits run, all OK: test_dev_rules_size 9, test_team_duties 20, test_squad_manager_guard 25, test_sizes 8, test_small_files_equivalence 2, test_architect_handoff 11, test_squadrules 43.
Red check: the new wording asserts search for old strings that exist on base (`never enough for done`, `Done rule`, `never suggest it to the PO`, empty `roles:` of REV-5a/EVID-5).
Full suite: not run (QA whitebox owns it, after Chieu's yes).
