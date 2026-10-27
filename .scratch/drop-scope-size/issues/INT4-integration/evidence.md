# Evidence: INT4 integration of 11 + 14
base 90be196 (INT3); merged in order: 11 (d8b4738, code ca53ba7), 14 (7c8af4a, code b2ee4e5).

## Behaviour
- 11: merged clean (no conflicts).
- 14: one conflict, `skills/squad-process-update/changelog.md` (v9 appends): kept both sides (11's rows, then 14's SAFE-10, SAFE-11 rows). No other conflicts.
- Stale-test fix (e265fd7, after Tech FAIL): `tests/test_team_lead_perms.py` TL_ALLOW gains 14's 4 entries (`Bash(rm /tmp/tmp.*)`, `rm -r`, `rm -rf`, `rmdir`) because team-lead.json carries them. Only edit beyond conflict resolution. Re-run: that file 9 OK, plus every `templates/squad/settings` grep hit (squadsettings, team_lead_role, instructions, architect_handoff, model_effort_settings, squad_respawn, squadadopt, squad_spawn) OK, and test_templates, ca_launchers, squad_start, team_models, squad_log_message OK.
- Tests on merged result: test_dev_rules_size 11 OK; test_sizes 34 OK; test_squadsettings 24 OK; test_instructions 30 OK; test_process_conversion 14 OK; also test_squadadopt 30, test_model_effort_settings 4 (1 skip), test_squadrules 59, test_squadcompose 85, test_squadruntime 64, test_pod_contact_routes 7, test_qab_optional 11 OK. `squad-process lint`: exit 0, empty.
- Full suite not run by me (Tech Lead owns it, `--if-changed 90be196`).
