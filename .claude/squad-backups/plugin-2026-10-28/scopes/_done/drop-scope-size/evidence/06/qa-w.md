# QA whitebox 06 — FAIL on ebe85ec (all style/correctness findings of this sha, REV-17)
Checked read-only in worktree plugin-dev-dsz-06. Passed: lint exit 0 (= base, empty); tests OK: test_small_files_equivalence, test_pod_rules_process, test_process_conversion, test_team_duties, test_squadcompose, test_squadrules, test_instructions, test_manager_m_l, test_architect_handoff, test_process_citations, test_templates, test_dev_rules_size, test_squad_close, test_windows_safe, test_crlf_squad_files; no `size` word in the 8 files (`\bsize\b(?!-\d)`); changelog v9 entries with reasons.
(test_sizes red on this branch is 05/04a territory, not judged here.)

## F1 (correctness) templates/squad/process/iterations.md ITER-3b: acts for the L Manager
My own check: compose of the 8 files' rule IDs, base 2949573 vs this branch, 7 legacy shapes x 9 roles (script over `tests/rulesview.composed`, present roles). Only real difference: `L/manager` and `Lgoal/manager` gain **ITER-3b** (base: M only). `when: handin-target = qas` is also true when a Team Lead is on the team (chain: QAs, then Team Lead, then Manager), so the Manager at L now gets "write the pod summary" while ITER-3 gives it to the Team Lead. Ticket AC: `who` for changed rules = same acting roles as before for the 7 shapes. The equivalence test misses it because it only covers unchanged-body rules (ITER-3b is rewritten).
Pass: `when: plan-owner = manager and handin-target = qas` (the engine accepts two duty keys, checked with `sr.matches`), and add ITER-3b (or a who/compose check over the changed IDs, all 7 shapes) to the equivalence test so the changed rules are covered too; the body's "(the Team Lead is not on the team)" can then go.
Other present-role differences are fine: WHO-1c/1e/1b/1d/2f are the split of old WHO-1a/1b/2b (new IDs only for the split halves); PROMO-3a/PROMO-8/ITER-3/NOTE-3/WHO-1b on absent roles are not acted on.

## F2 (stale text) agents/team-lead.md:6
"You exist in **M and L** scopes; in S the Tech Lead holds your duties." Ticket 06 files: `agents/*.md naming a size`. Untouched by the branch; it is also wrong now (the Team Lead exists when on the team; with none the Manager holds the plan). Pass: reword without S/M/L (`grep -nE '\b[SML]\b' agents/*.md` empty), no new size word.

# Re-check on final code sha bd361cf — PASS
Changed files only (LC-3b): iterations.md, agents/team-lead.md, test_small_files_equivalence.py, test_sizes.py, test_team_lead_role.py, + INT1 merge.
- F1 closed: ITER-3b `when: team-lead = no and qa-black = yes`. Own base(2949573)-vs-branch compose of rule IDs, 7 legacy shapes x 9 roles: ITER-3b set identical to base (M/Mdesign/March manager only; L manager no longer gets it). Only differences are the new split IDs (WHO-1b/1c/1d/1e/2f) and absent roles; same as before.
- F2 closed: agents/team-lead.md:6 no S/M/L; `grep -nE '\b[SML]\b' agents/*.md` empty.
- `squad-process lint` exit 0 empty. Tests OK: test_small_files_equivalence (2), test_team_lead_role, test_sizes (34), test_pod_rules_process, test_process_conversion, test_squadrules, test_instructions, test_team_duties.
- Note (non-blocking, TL accepted): test_sizes skips rules with no size/qa-b `when` (`team_keyed`); evidence.md should name it (fresh Dev, evidence-only).
