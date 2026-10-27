# 07 Rules: lifecycle, review, evidence

## Behaviour
- `lifecycle.md`, `review.md`, `evidence.md`: every `when:` is in team language (no `size`, no `qa-b`); changelog v9 lists every changed ID.
- Return 1 fixes (QA whitebox F1-F5):
  - F2 LC-20a: `handin-target = manager`, "Done when the Manager sent PASS" (the S text). LC-20b: `handin-target = qas`, every checker, tell the plan owner. New LC-20e: `handin-target = team-lead`.
  - F3 LC-7a: `handin-target = manager`, S text, no checker sentence.
  - F4 REV-14a: restores "tell the plan owner after every checker passes it" (with QAs on the team).
  - F5 REV-3b: `aware: manager` restored, as in the M text.
  - A `when:` holds one duty/role key (lint), so L and M share LC-20b with "the plan owner" instead of naming Manager or Team Lead.
- Stale tests fixed to new IDs/keys, no weakening. Outside the ticket's list (Tech ANSWER 07 (b), DECISION 07): `tests/test_dev_rules_size.py`, `tests/test_sizes.py`, `tests/test_process_conversion.py`, `tests/test_instructions.py`, `tests/test_architect_handoff.py`, `tests/test_pod_contact_routes.py`, `tests/test_manager_m_l.py`.
- Deferred by Tech Lead DECISION 07: the 5 KiB dev-rules budget tests, skipped with reason "5 KiB trim is ticket 11" (`test_sizes` 1, `test_dev_rules_size` 3 tests). Nothing else skipped.
- Ran green (386 tests, 4 skipped): the 7 files above plus test_qab_optional, test_team_duties, test_squadrules, test_retro_rules, test_advisor_rules, test_pod_rules_process, test_processlint, test_templates, test_windows_safe, test_crlf_squad_files, test_squad_close.
- G2b: `squad-process lint` on base 6389642 and on the branch: both empty, rc 0.
- `test_qab_optional`: 11 tests, none skipped.

## Return 2: Manager rule sets vs base 6389642 (LC-, REV-, EVID- IDs only)
Composed per shape (S = no team, M = `qa-white, qa-black`, L = `ba, team-lead, tech-lead, qa-white, qa-black`); script compared base `size:` homes with branch `team:` homes.
- S Manager: no difference (LC-7a kept). S Dev: none.
- M Manager: base LC-7c -> LC-7a. LC-7a is now `plan-owner = manager` with "with QAs on the team the 3rd failing QA sends you `BLOCKED NN: 3 returns`", so the Manager keeps the base LC-7c duty (a `when:` allows one duty/role key, so a separate "no Team Lead" rule is not expressible). Test `test_manager_three_returns_rule_per_team_shape` pins S, M and L.
- L Manager: no difference (LC-7b aware, no LC-7a).
- Dev: LC-20c -> LC-20b (M), REV-14c/14b -> REV-14a (M, L); text carries the Manager/Team Lead report-back as "plan owner".
- QAs: new LC-7c at M and L (3rd failing QA sends the plan owner BLOCKED); base had it only as the Manager's M rule.
- REV-3b is now `handin-target = qas`, no `aware: manager` (a QA-less S Manager would otherwise carry a QA rule). Difference vs base: the M Manager no longer sees the single-verdict line; it receives the verdicts, so nothing is lost.
- Not a difference of mine: base-only SIZE-/TEAM- and new-only COST-/SUITE-/MSG- IDs are other tickets' files.
