# 11 Integration: merge the passed branches of the scope

Status: ready-for-agent
Blocked by: 01, 02, 03, 04, 05, 06, 07, 10 (all passed)

GOAL-6b integration task. Start on branch `squad/plugin/task-claim-gates/plugin-dev-tcg-6` (tip 855c2a7). It already holds 01, 07, 03, 04, 10 and 05. Two passed branches are not in it yet:

| Order | Branch | Ticket | Tip |
|---|---|---|---|
| 1 | `squad/plugin/task-claim-gates/plugin-dev-tcg-3` | 02 hooks record | 7529110 |
| 2 | `squad/plugin/task-claim-gates/plugin-dev-tcg-5` | 06 merge record | 1e79ce5 |

Merge each with a merge commit (`git merge --no-ff`), one at a time, in that order. Both change `bin/squad-task`, `bin/squadledger.py`, `bin/squadtask.py` and `tests/test_squadtask.py`, which 07 also changed. The Tech Lead's dry run with `git merge-tree` shows no conflict for (tcg-6 + tcg-3) and then + tcg-5. If a conflict appears anyway, keep both sides' lines and keep 07's no-confirmer rules (design.md D7); say what you did in `## Behaviour`. Do not change any behaviour while merging.

Files: no new edits expected. Allowed: the conflict lines above. Version stays 0.7.6 (`grep -rn "0\.7\.5"` over tests bin hooks skills agents docs templates README.md CLAUDE.md finds nothing).

Technical AC:
1. Both merges are merge commits, in the order above; `git log --oneline --first-parent` shows them.
2. Targeted tests pass on the final sha: `cd tests; python3 -m unittest test_squadtask test_squad_log_message test_squad_spawn test_squad_merge_record test_squad_ledger test_squadboard_tasks test_squadboard_list test_squadboard_active test_squadboard_inbox test_board_fixtures test_squadboard_panels test_squadboard_demo test_rules_wording test_dev_rules_size test_squadrules test_processlint`. Known failures, same on main (fixed fixture dates against the real clock; not ours): panels T12 and T14, list T04, demo T37, and `test_squad_spawn` `test_a_failed_agent_start_leaves_the_old_overrides_file`. Any other failure is a finding. Run each file once; commit a fix before a rerun.
3. One end-to-end check that no single ticket had (02 writes events, 03 reads them, 06 records the merge). In a temp squad folder (`SQUAD_DIR` pointing at a temp dir, a temp git repo, never the real `task-events/`): send a `HANDIN`, two QA `PASS` messages, through `bin/squad-log-message`; read `/api/tasks` of `bin/squad-board` (or `squadboard_tasks.read` as the existing tests do) and see `passed`; run `bin/squad-merge-record` for a `git merge` of that branch and see `merged`. Put the commands and the rows seen in `## Behaviour`.
4. Real store untouched: `sha256sum .claude/squads/plugin/task-events/task-claim-gates.jsonl` is the same before and after (it still holds two fake events of tasks 08 and 09 until Chieu deletes them; do not delete them).
5. `squad-evidence check` on this ticket's evidence folder passes.

Suite: targeted only (GOAL-6b, SUITE-1). The Tech Lead asks the Manager for a full run through `ASK 11: full suite?` and runs it only after Chieu's yes; SUITE-3 needs a passing run on the final integration sha (`--tz`).
Reviewers: QA whitebox reads the merge commits and runs AC2; QA blackbox repeats AC3 on its own temp squad. Tech Lead reads the code check at HANDIN.

## Review

AC trace
- AC1 | `git log --oneline --first-parent` | two merge commits a5c2eb3 (tcg-3), 9a67d30 (tcg-5)
- AC2 | the 16 test files in AC2 | `cd tests; python3 -m unittest <file>`; only the 5 known failures
- AC3 | evidence.md `## Behaviour` | temp squad: squad-log-message, squadboard_tasks.read, squad-merge-record
- AC4 | evidence.md | sha256sum equal before and after
- AC5 | `squad-evidence check .scratch/task-claim-gates/issues/11-integration` | ok
