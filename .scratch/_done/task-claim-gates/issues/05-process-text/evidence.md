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

## QA whitebox

### QA whitebox 05 (3a3e883): PASS
Diff read (10 process files, plugin.json, 2 tests) against states.md s4, s6 and the ticket AC.
- CORE-1 ends `checking → passed`; LC-20a/b/e, SIZE-2, TEAM-1..3, WHO-1b use Passed; REV-1/1b: confirmer sends FAIL only, never PASS; TEAM-3 and LC-27: no QA = HANDIN `squad-evidence check`, exit 0 passed, else warning and `in progress`; LC-27 states warn-never-block, `squad-task` manual commands, `passed` override warns; MRG-4 fallback `squad-task merged NN`; SPAWN-5a/5b `--task`.
- LC-27 roles list has no dev; every rule that cites [LC-27] is given to a role in that list; dev rules stay under 5 KiB (test_dev_rules_size OK).
- Version: `grep -rn "0\.7\.5"` over tests bin hooks skills agents docs templates README.md CLAUDE.md .claude-plugin: no hit. plugin.json 0.7.6.
Ran in worktree tcg-6: test_rules_wording test_dev_rules_size test_squadrules test_processlint test_rules_contract test_process_writing test_sizes test_team_duties: 143 OK.
Follow-ups (not FAIL): templates/squad/process/starting.md:10 "the team's Done rule ([SIZE-2])" and teams.md:49 "the new Done" still use the old word (SIZE-2 is now titled Passed); manager byte baselines raised 678-742 B (a limit moved, not a regression).

## QA blackbox

### QA blackbox, task 05 (process text), sha 3a3e883
Checked live on the handed-in checkout (`bin/squad-process`), against tasks/states.md s4, s6, s9 (R3, R12).

| AC | how | what I saw | result |
|---|---|---|---|
| Text matches s4 (no-QA path) | live: `squad-process rule LC-27`, `TEAM-3` | LC-27: HANDIN hook runs `squad-evidence check`; exit 0 = `passed`; else a warning and the ticket stays `in progress`. TEAM-3 "Passed, no QA": evidence check exit 0; code-check owner reads both and sends FAIL, never PASS. | pass |
| Text matches s6 / s9 (no confirmer, warn gates, manual command) | live: `rule LC-27` | "Gates warn, never block"; `passed` = every QA on the roster sent PASS for the current sha; PASS from anyone else warns, not counted; `squad-task claim\|handin\|pass\|fail\|blocked\|merged NN`, `squad-task passed NN` overrides and warns. Verbs match the real `squad-task` usage. | pass |
| `merged` recorded (s2) | live: `rule MRG-4` | "The hook records `merged`; for a ticket it did not record, run `squad-task merged NN`." | pass |
| R3: `done` not a stage word | live: `rule CORE-1`; grep of templates/squad/process for `done`; grep for confirmer / ready for review | CORE-1 ends `checking → passed \| returned → building`. No `confirmer`, no `ready for review`. Remaining `done` hits are plain English, not stage lists (see follow-ups). | pass |
| Version bump | live: plugin.json | 0.7.6 | pass |
| Rules lint | `squad-process lint` | exit 0, no output | pass |
| LC-27 reaches roles | `squad-process compose manager` | LC-27 present in the composed Manager rules; other roles cannot compose in a temp home (team undecided), so not checked. | pass (Manager only) |

Targeted tests run: test_rules_wording.py (18 OK), test_dev_rules_size.py (9 OK).

Follow-ups (not fails): prose still says "done" for completion in iterations.md 5, 24, 112-113, goal.md 34/41, starting.md 194 ("scopes whose dependencies are done"), spawning.md 87/94 ("task is done"), sizes.md 167/189, lifecycle.md LC-1 title. They are not stage lists, so R3 holds, but a reader may take them as "done = passed". Consider "merged" or "passed" where the meaning is the board state.

## Tech Lead review

### Tech Lead review, ticket 05 (process text, version bump)

Final sha for QA verdicts: 3a3e883 (branch squad/plugin/task-claim-gates/plugin-dev-tcg-6, on top of 10's 65302ed).

- Text read against states.md s4 (no QA: evidence check, never `0 of 0`) and s6 (warn never block, `squad-task`, W6 override): matches. CORE-1 ends `passed`; Done -> Passed in WHO-1b, TEAM-1..3, SIZE-2, LC-20a/b/e; REV-1, REV-1b: no PASS from a confirmer; REV-20 QA whitebox PASS passes the task; MRG-4 `squad-task merged NN` fallback; SPAWN-5b `--task <id>` (dev only, D5); new LC-27 is not given to the Developer (Dev rules stay under 5 KiB).
- Version: 0.7.5 -> 0.7.6; `grep -rn 0\.7\.5` over tests, bin, hooks, skills, agents, docs, templates, README, CLAUDE.md, .claude-plugin: no hits (SQ-5).
- Tests: `python3 -m unittest test_rules_wording test_dev_rules_size test_squadrules test_processlint test_team_duties test_sizes test_rules_contract` -> 142 run, OK. The Developer's longer targeted list is in evidence.md; the known `test_squad_spawn` failure is not ours.
- Manager byte baselines raised 678-742 B with a comment (as earlier tasks did).

Not blocking (cosmetic, put in the summary):
- LC-20a/LC-20e say "Passed at `HANDIN`". A no-QA HANDIN is passed only when the evidence check exits 0 (W9 otherwise). Wording could read "Passed when the HANDIN evidence check exits 0".
- LC-1 still says "never enough for done ([SIZE-2])"; SIZE-2 is now titled "Passed". Harmless.

Verdict on text: PASS. `squad-evidence check` runs after both QAs PASS and the Developer sends the evidence sha (EVID-2c).
