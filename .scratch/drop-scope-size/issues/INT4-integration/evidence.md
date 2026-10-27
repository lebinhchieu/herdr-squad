# Evidence: INT4 integration of 11 + 14
base 90be196 (INT3); merged in order: 11 (d8b4738, code ca53ba7), 14 (7c8af4a, code b2ee4e5).

## Behaviour
- 11: merged clean (no conflicts).
- 14: one conflict, `skills/squad-process-update/changelog.md` (v9 appends): kept both sides (11's rows, then 14's SAFE-10, SAFE-11 rows). No other conflicts.
- Stale-test fixes: none needed. No code changes beyond the conflict resolution.
- Tests on merged result: test_dev_rules_size 11 OK; test_sizes 34 OK; test_squadsettings 24 OK; test_instructions 30 OK; test_process_conversion 14 OK; also test_squadadopt 30, test_model_effort_settings 4 (1 skip), test_squadrules 59, test_squadcompose 85, test_squadruntime 64, test_pod_contact_routes 7, test_qab_optional 11 OK. `squad-process lint`: exit 0, empty.
- Full suite not run by me (Tech Lead owns it, `--if-changed 90be196`).
