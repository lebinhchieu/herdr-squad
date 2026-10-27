# Evidence: INT3 integration of 07 + 08
base fed0c95 (INT2); merged in order: 07 (0067a5d), 08 (e08bb66, per Team Lead DECISION INT3).

## Behaviour
- 07: conflicts in `skills/squad-process-update/changelog.md` (v9 appends: kept both sides, dropped 07's shorter duplicate TEAM-7 line, kept the fuller `runs squad-team remove` one) and `tests/test_sizes.py` (took 07's team-combination sweep; 06's `team_keyed` skip is superseded there).
- 08: conflicts in changelog (keep both, same TEAM-7 dedupe), `tests/test_dev_rules_size.py` (08's in-process `legacy_scaffold` compose; its home writes `size:`), `tests/test_sizes.py` (07's team sweep; guard `team_keyed(rid) or team_language(rid)`), `tests/test_pod_contact_routes.py` (07's "Tell the plan owner" line), `tests/test_qab_optional.py` (kept both blocks).
- Stale-test fixes (only edits beyond conflict resolution, commit 7a66ae4): `test_pod_contact_routes` asserts `else the Team Lead` (MSG-11b wording now) instead of `the Team Lead (plan or order)`; `test_qab_optional` `who` lines use `qa-black = no: acts: -; aware: -` / `qa-black = yes: acts: -` instead of `M qa-b no/yes`.
- Tests on merged result: test_squad_migrate 20 OK; test_instructions 30 OK; test_sizes 34 OK (1 skip); test_dev_rules_size 9 OK (3 skip); test_process_conversion 14 OK; also test_pod_contact_routes 7, test_qab_optional 11, test_team_lead_role + test_pod_rules_process 23 OK. `squad-process lint`: exit 0, empty.
- Full suite not run by me (Tech Lead owns it, `--if-changed fed0c95`).
