# QA whitebox 07 — on 426706d (HANDIN). Verdict held until the Tech Lead names the final sha (REV-3).
Checked read-only in worktree plugin-dev-dsz-07; base = 6389642 (INT1), tests also run from a git-archive of it.
Passed: `squad-process lint` exit 0 empty (= base). OK: test_qab_optional (11, no skips left), test_team_duties, test_squadrules, test_retro_rules, test_advisor_rules, test_pod_rules_process, test_team_lead_role, test_templates, test_windows_safe, test_crlf_squad_files, test_squad_close, test_processlint.

## F1 (G1: tests touched by the change are red; all green on base 6389642)
Base 6389642 is green on every file below; at 426706d they fail. The ticket says every `grep -rl` hit runs green (CLAUDE.md, G1); Tech ANSWER 07 (b) allowed fixing stale tests outside the list, evidence.md only names two files.
- tests/test_process_conversion.py:101 `test_fix_a_handin_target_by_size`: expects REV-13a `size = S`; now `handin-target = manager`.
- tests/test_instructions.py:197 `test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass`: IndexError, `## REV-14b` no longer exists (merged into REV-14a).
- tests/test_architect_handoff.py: `test_conformance_joins_the_technical_ac_of_the_existing_checker`, `test_the_plan_waits_for_the_architecture`.
- tests/test_pod_contact_routes.py: `test_m_paths_go_to_the_qas_and_done_to_the_manager`, `test_team_lead_routes_in_l`.
- tests/test_manager_m_l.py: `test_s_keeps_the_pod_health_checks`.
- tests/test_sizes.py: `test_dev_rules_stay_within_5_kib` (S, yes, yes) 6121 B; tests/test_dev_rules_size.py: 24 failures (5.8 KB at every shape). The evidence says "same on base (7 KB then)": on base these 2 files are green (the test composed a `size:` home). The Dev changed the helper to a `team:` home, which turns them red. If the 5 KiB cap is ticket 11's, the ticket/Tech DECISION must say so and the test must be marked (skip with reason) rather than left red; otherwise bring Dev rules under 5120.
Pass: each test above fixed to the new IDs/keys (or an explicit Tech DECISION naming it deferred to 11/12 with a reason in evidence.md), rerun green.

## F2 (correctness) templates/squad/process/lifecycle.md:250-255 LC-20a at a team with no checkers
Base LC-20a (S): "Done when the Manager sent `PASS`." New (`plan-owner = manager`): "Done when every checker sent `PASS`. Tell the Manager and wait". An S-shape Developer (handin-target = manager, no QA) now has no PASS source: "every checker" is empty. Pass: split on `handin-target` (manager: "Done when the Manager sent PASS"; qas/team-lead: every checker).

## F3 (correctness) templates/squad/process/lifecycle.md:73-78 LC-7a at a team with no checkers
`when: plan-owner = manager` covers S (no QA): body says "the 3rd failing checker sends you `BLOCKED NN: 3 returns`, and your own 3rd FAIL counts". Base S text: "the Manager steps in; your own 3rd FAIL counts" (no checker sentence). Pass: keep the S-form for `handin-target = manager` or make the checker sentence conditional.

## F4 (lost duty) templates/squad/process/review.md:149-153 REV-14a
Base L/M REV-14b/c: "...diff check...; tell the Team Lead / Manager after both pass it". New REV-14a (no `when`) drops that sentence at every shape. Pass: restore the report-back sentence for checkers on the team (own rule keyed `handin-target in qas`) or state in evidence why it is dropped.

## F5 (style, REV-17) review.md:42-47 REV-3b
The `aware: manager` line of base REV-3b (M) is gone; the M Manager no longer sees the single-verdict rule. Non-blocking if intended; say so in evidence.md.

Method: base-vs-branch composed rule IDs over S/M/L/Mdesign/March/Lgoal x present roles, new side composed from `team:` = legacy_team(shape). Other differences are the intended moves (LC-7a/c, LC-20, REV-14). Lnoqb (qa-b no) not compared by me: Dev's 128-set test covers it.

# Return 1 re-check on c5dd6ce (diff 426706d..c5dd6ce, LC-3b)
Result: all F1-F5 fixed; PASS ready, sent once the Tech Lead names c5dd6ce final (REV-3).
- Lint exit 0 empty. Ran test_process_conversion, test_instructions, test_architect_handoff, test_pod_contact_routes, test_manager_m_l, test_sizes, test_dev_rules_size, test_qab_optional, test_team_duties: 166 tests OK, 4 skipped (all "5 KiB trim is ticket 11", per Tech DECISION 07).
- F1 fixed: tests moved to new IDs/keys, no assertion weakened; evidence.md names the 7 outside-list files.
- F2 fixed: LC-20a `handin-target = manager` (S text), LC-20b `qas`, LC-20e `team-lead`. Composed dev: S -> LC-20a, M/L -> LC-20b.
- F3 fixed: LC-7a `handin-target = manager`, no checker sentence; Manager S only gets it, M gets LC-7c.
- F4 fixed: REV-14a "with QAs on the team, tell the plan owner after every checker passes it" (wording-keyed, not a `when`; accepted per Tech ruling; S text only mentions QAs conditionally).
- F5 fixed: REV-3b `aware: manager`; Manager S and M carry the line, L does not (as base).
- Reminder for 11/12: un-skip test_sizes dev-5KiB and 3 tests in test_dev_rules_size.

# Return 2 re-check on 0f1dc44 (diff c5dd6ce..0f1dc44, LC-3b)
Result: clean; PASS ready once the Tech Lead names 0f1dc44 final (REV-3). My miss on c5dd6ce: I tested the Manager for the QA-side LC-7c sentence, which the Manager never receives; Tech Lead found the lost M Manager rule.
- Lint exit 0 empty. 256 targeted tests OK, 4 skipped (ticket-11 deferral): test_manager_m_l (new per-shape test), test_process_conversion, test_instructions, test_architect_handoff, test_pod_contact_routes, test_sizes, test_dev_rules_size, test_qab_optional, test_team_duties, test_processlint, test_squadrules.
- Invariant over all 128 team sets (own script): Manager composes a three-returns rule in every set (LC-7a with `plan-owner = manager`, conditional QA sentence; LC-7b aware when a Team Lead owns the plan); Dev composes exactly one LC-20 rule in every set. No failures.
- Base-vs-branch Manager (S/M/L shapes, LC/REV/EVID): S same; M base LC-7c -> LC-7a (same duty); L same. REV-3b without `aware: manager`: Manager still receives the verdicts; accepted as covered (evidence.md Return 2).
- Other diffs against base are tickets 08-14 files, not 07.
