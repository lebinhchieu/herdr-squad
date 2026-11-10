# 11: Integration of the lanes (SQ-6/SQ-6b, GOAL-6b)
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=tech-lead, promote-owner=tech-lead. Test economy: targeted tests only; full suite only after Chieu's yes via the Manager. Cite [GOAL-6b].
Lane: Developer plugin-dev-fable-w (own branch, tip 136f92f = 01-03 + 09)
Files: merge commits only; conflict fixes in `tests/test_rules_wording.py`, `tests/test_dev_rules_size.py`, `templates/squad/process/*.md` if they conflict
Related siblings (SQ-6): 09 and 10 both change `tests/test_rules_wording.py` and `tests/test_dev_rules_size.py` (QA whitebox). 07/08 (dev-b b54f582) and 04-06/10 (dev-c b35c5d0, contains dev-a d0a112f) are on other branches.

## Business AC
1. Your branch contains passed ticket shas: merge `squad/plugin/fable-advisor/plugin-dev-fable-c` (b35c5d0) and `squad/plugin/fable-advisor/plugin-dev-fable-b` (b54f582). `git merge-base --is-ancestor <sha> HEAD` is true for 136f92f, b35c5d0, b54f582, d0a112f, 52da3ef, 07a7be3, ea90150.
2. Conflicts are resolved keeping both sides' intent; `LIMIT` in test_dev_rules_size.py is the measured max after the merge rounded up to 20 B, never above 5480 (ask the Tech Lead above that).
3. Targeted tests pass on the merged tip: every test file touched by 01-10 plus `grep -rl` hits, `squad-process lint`. Name the command and result in evidence.md. No full suite.
4. HANDIN 11 to both QAs and the Tech Lead with the merged sha. Evidence in `.scratch/fable-advisor/issues/11-integration/evidence.md`.

## Technical AC (Tech Lead; review the merge shape and targeted tests only)
- T1. Merge shape: two separate `git merge --no-ff` commits (dev-c b35c5d0, then dev-b b54f582), no octopus, no rebase, no `--force`, no squash. `git log --first-parent --oneline 136f92f..HEAD` shows exactly the two merge commits plus at most one `11:` fix commit. For each merge, `git diff <merge>^1 <merge> --stat` equals the merged branch's own change set (conflict hunks only differ).
- T2. Every sha listed in business AC1 is an ancestor of the merged tip (`git merge-base --is-ancestor`, quote the seven results).
- T3. No change outside the sibling diffs except conflict resolution: `git diff --stat` of the 11 fix commit, if any, touches only `tests/test_rules_wording.py`, `tests/test_dev_rules_size.py`, `templates/squad/process/*.md`. Anything else: ASK the Tech Lead.
- T4. Targeted tests on the merged tip (quote command and last lines): `cd tests && PYTHONPATH=. python3 -m unittest` for `test_rules_wording`, `test_dev_rules_size`, `test_rules_contract`, `test_squadcompose`, `test_squadrules`, `test_squad_evidence`, `test_architect_handoff`, `test_small_files_equivalence`, `test_squad_merge_check`, `test_squad_spawn`, `test_squad_report_*`, `test_squad_watchdog`; plus `grep -rl "Index of other rules\|EVID-9\|phase:" tests/` hits. `squad-process lint` exit 0; `squad-process upgrade --check` exit 0.
- T5. Cross-ticket checks that only the merged tip can show (the reason 11 exists): (a) 10's live contract test passes with 09's new rules attached (no snapshot breaks); (b) the Developer sweep in `test_dev_rules_size` is at or under `LIMIT`; (c) the Manager and Tech Lead index is at most 40 lines on the merged tip (compose both, count).
- T6. `LIMIT` is the measured sweep max after the merge, rounded up to 20 B, never above 5480; above that, ASK me with the numbers.
- T7. Known failing test `test_a_failed_agent_start_leaves_the_old_overrides_file` also fails on main (dev-a notes): name it as pre-existing in the evidence; it is not a finding.
Evidence: `## Behaviour` (the commands and results above), `## Review` (the merge-shape output); `HANDIN 11` names the merged sha.
