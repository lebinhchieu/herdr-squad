# 07 Rules: lifecycle, review, evidence

## Behaviour
- `lifecycle.md`, `review.md`, `evidence.md`: every `when:` is in team language (no `size`, no `qa-b`); retargets listed in changelog v9 (added / changed / removed / retargeted).
- Removed duplicates by size: LC-20c, REV-14b, REV-14c, REV-19 (replaced by LC-20a/b, REV-14a, REV-19b).
- Tests: `test_sizes` orphan check now walks all 128 teams; `test_dev_rules_size`, `test_sizes` use the new IDs (LC-20a, REV-14a) and `team:` scope.md (outside the ticket's list, per Tech ANSWER 07 (b)).
- Ran green: test_qab_optional, test_team_duties, test_squadrules, test_retro_rules, test_advisor_rules, test_pod_rules_process, test_sizes (orphans), test_dev_rules_size (duties).
- Still red, same on base (7 KB then, 6 KB now): the 5 KiB dev-rules budget tests (`test_every_combination_fits_5_kib`, `test_architecture_flag_on_fits_except_s`, `test_s_architecture_exception_is_pinned`, `test_dev_rules_stay_within_5_kib`); depend on the other rule files migrating.
- G2b: `squad-process lint` on base 6389642 and on branch: both empty, rc 0, identical.
- No skipped tests found in `test_qab_optional.py`.
