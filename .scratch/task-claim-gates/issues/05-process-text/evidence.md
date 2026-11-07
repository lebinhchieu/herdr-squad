# Evidence 05

## Behaviour

The process text now says what `tasks/states.md` s4 and s6 say. No behaviour is built: the check is the composed rule text.

| Where | Change |
|---|---|
| CORE-1 | stages end `checking → passed`; `done` is gone |
| WHO-1b, TEAM-1..3, SIZE-2, LC-20a/b/e | `Done` becomes `Passed`; no confirmer: the Manager and Team Lead send no `PASS` |
| TEAM-3, LC-20a/e, new LC-27 | no QA: `HANDIN` runs `squad-evidence check`, exit 0 is `passed` |
| REV-1, REV-1b, REV-20 | confirmer sends `FAIL` only; QA whitebox `PASS` passes the task |
| MRG-4 | the hook records `merged`; fallback `squad-task merged NN` |
| LC-27 (manager, team-lead, tech-lead, QAs) | gates warn, never block; hook-missed steps by `squad-task`; `squad-task passed NN` overrides |
| SPAWN-5a, SPAWN-5b | `--task NN` claims the ticket |
| starting.md | "dependencies done" becomes "passed" |
| `.claude-plugin/plugin.json` | 0.7.5 → 0.7.6 |

Dev rules stay under 5 KiB at every team shape (LC-27 is not given to the Developer). Manager byte baselines in `tests/test_dev_rules_size.py` went up 678 to 742 B, with a comment, as earlier tasks did.

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 text matches states.md s4 (no QA: evidence check, never `0 of 0`) | `tests/test_rules_wording.py` `TaskStageWordsTest`; TEAM-3 and LC-27 text | `cd tests; python3 -m unittest test_rules_wording` |
| AC2 text matches states.md s6 (warn, never block; `squad-task` manual command; merged fallback) | same test (LC-27, MRG-4) | same |
| AC3 version bump with grep | `grep -rn "0\.7\.5" tests bin hooks skills agents docs templates README.md CLAUDE.md` prints nothing | grep |
| Regression: Developer rules under 5 KiB, process lint clean | `test_dev_rules_size`, `test_rules_wording`, `test_squadrules` | `cd tests; python3 -m unittest <names>` |

Targeted run (all hits of `grep -rl` for the touched paths and strings): `test_dev_rules_size test_instructions test_qab_optional test_rules_contract test_rules_wording test_sizes test_squadrules test_team_duties test_process_writing test_processlint test_architect_handoff test_small_files_equivalence test_squadcompose` OK (225); `test_promotion_0_6_0 test_squad_respawn test_squadruntime test_squadsettings test_squad_spawn test_squad_team test_squadupgrade` OK except the known `test_a_failed_agent_start_leaves_the_old_overrides_file`. `test_squad_start` OK (44); `squadtest` is a helper module, no tests.
