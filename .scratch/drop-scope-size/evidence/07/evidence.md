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
