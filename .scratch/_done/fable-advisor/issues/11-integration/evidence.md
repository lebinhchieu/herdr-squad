## Behaviour
Merged `plugin-dev-fable-c` (b35c5d0) then `plugin-dev-fable-b` (b54f582) into the 09 branch (tip 136f92f). Both merges ran clean, no conflicts. Merged tip: 2da9234 (the HANDIN sha ec5ebc0 is 2da9234 plus this evidence file).

- AC1: `git merge-base --is-ancestor <sha> HEAD` is true for 136f92f, b35c5d0, b54f582, d0a112f, 52da3ef, 07a7be3, ea90150.
- AC2: no conflicts. Measured max composed Developer rules after merge is 5433 B, rounded up to 20 B = 5440, so `LIMIT` stays 5440 (cap 5480).
- AC3: `PYTHONPATH=tests python3 tests/<file>.py` (watchdog: `python3 -m unittest test_squad_watchdog`) for every test file touched by 01-10: architect_handoff, dev_rules_size, rules_contract, rules_wording, small_files_equivalence, squad_close, squad_evidence, squad_merge_check, squad_report_cli, squad_report_query, squad_review_pack, squad_spawn, squad_watchdog, squadcompose, squadreport_digest, squadreport_tasks, squadrules: all OK except one in squad_spawn. `squad-process lint --plugin-root .`: 0 problems. No full suite.
- Known failure: `test_squad_spawn.test_a_failed_agent_start_leaves_the_old_overrides_file` (returncode 0, expected nonzero). It fails the same on 136f92f and on b35c5d0 before this merge, so it is not caused by the merge.

## QA whitebox

### QA whitebox: 11 integration, sha ec5ebc0 (merged tip 2da9234 + evidence commit)
Verdict: PASS. Checked in a detached worktree, read-only.

- T1 merge shape: `git log --first-parent 136f92f..HEAD` = ec5ebc0 (evidence only), 2da9234 (merge dev-b), e361c18 (merge dev-c), 9db43a2. Two separate --no-ff merges, no octopus. `git diff <merge>^1 <merge> --stat` = own change set of each branch (dev-c: 30 files +1374/-30 vs own 30 files; dev-b: 14 files +453/-9 vs own 14 files +453/-9).
- T2 ancestors: 136f92f b35c5d0 b54f582 d0a112f 52da3ef 07a7be3 ea90150 all yes (`merge-base --is-ancestor`).
- T3: the 11 commit touches only `.scratch/fable-advisor/issues/11-integration/evidence.md` (the evidence the ticket names).
- T4 tests (`cd tests && PYTHONPATH=. python3 -m unittest <m>`): rules_wording 29, dev_rules_size 9, rules_contract 14, squadcompose 44, squadrules 44, squad_evidence 49, architect_handoff 11, small_files_equivalence 2, squad_merge_check 9, squad_report_cli 19, squad_report_query 15, squad_watchdog 46, squad_review_pack 6, squad_close 79, squadreport_digest 11, squadreport_tasks 15, squadruntime 68: all OK. test_squad_spawn 106: 1 failure, `test_a_failed_agent_start_leaves_the_old_overrides_file` (T7: also fails on main 9b05952, pre-existing, not a finding). `squad-process lint --plugin-root .` exit 0; `squad-process upgrade --check`: "nothing needs a decision".
- T5a test_rules_contract OK with 09's rules. T5b dev sweep max measured 5433 B (`DevRulesSize().sweep()`), LIMIT 5440 = rounded up to 20, under 5480 (T6). T5c test_squadcompose index test (<= 40 lines for manager and tech-lead) OK; Manager index is 15 lines.
- Note: in a worktree whose path holds a UUID, `test_lean_without_a_lean_json_defaults_to_no_mcp_servers` fails (the test's UUID regex also rewrites the path). Path artifact, passes in a plain path. Not a finding.

Follow-ups (not blocking)
- Dev evidence lacks T1/T5 lines and `upgrade --check`; the Tech Lead's AC asked for `## Review` with merge-shape output. Add it with the doc-only commit in task 12 if the Tech Lead wants it.

## QA blackbox

### QA blackbox 11 (sha ec5ebc0, dev-fable-w)
Run from the dev-w worktree (read-only), scratch home in the scratchpad.

| AC | live/shot | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 ancestors | live | `git merge-base --is-ancestor <sha> HEAD` for the 7 shas; `git log --first-parent 136f92f..HEAD` | all 7 yes; first-parent: merge dev-c (e361c18), merge dev-b (2da9234), plus 9db43a2 `09: evidence assembled` (evidence-only, from 09) and ec5ebc0 evidence | pass |
| AC2 conflicts / LIMIT | live | `git diff --stat <merge>^1 <merge>`; `LIMIT` in test_dev_rules_size.py | 30 and 14 files, no conflict commit; LIMIT = 5440 (<= 5480) | pass |
| AC3 targeted tests, lint | live | `lint --plugin-root .`; `upgrade --check`; `unittest test_dev_rules_size test_rules_contract test_rules_wording` (52 OK) | lint rc 0; upgrade --check rc 0 "nothing needs a decision"; 52 OK. Whitebox owns the rest of the test list. Known failure test_squad_spawn (failed-agent-start) is named as pre-existing by the Developer | pass |
| AC4 HANDIN + evidence | live | read evidence.md | merged sha named, commands and results given | pass |

Behaviour on the merged tip: `squad-evidence check` on 01, 02, 03, 09 evidence rc 0; `checks --template` works (09); `squad-merge-check`, `squad-review-pack`, `squad-report`, `squad-watchdog`, `squad-spawn --help` rc 0; compose manager 16-line index, tech-lead 24-line index (<= 40, T5c).
Note: evidence says tip 2da9234, HANDIN says ec5ebc0; ec5ebc0 differs by the evidence file only (`git diff --stat 2da9234 HEAD`).
