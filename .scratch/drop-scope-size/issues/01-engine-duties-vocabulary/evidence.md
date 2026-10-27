# Evidence: 01 Engine vocabulary (squadrules)
sha: see HANDIN (branch squad/plugin/drop-scope-size/plugin-dev-dsz-1)

## Behaviour
- `bin/squadrules.py`: `TEAM_KEYS` (7), `ROLE_KEY` (2), `PRESENCE_KEY`, `DUTIES` (13 chains), `resolve_duties`, `team_facts`, `legacy_team`, `parse_team`, `role_key`, `check_when_combination`; `WHEN_KEYS` gains `ba team-lead tech-lead qa-white qa-black` and the 13 duty keys (`size`, `qa-b` stay); `FILE_ORDER` gains `TEAM` after `SIZE`.
- `resolve_duties(legacy_team("L","no"))` = plan team-lead, behaviour-check qa-white, ui-check manager, handin qas, choice tech-lead (run in python; table in `tests/test_team_duties.py` is hand-copied from base `sizes.md` SIZE-22 269-282, SIZE-22a 291-295, SIZE-20 249).
- Lint: `business-ac = ba and qa-black = yes` passes; `business-ac = ba and code-check = qa-white` fails as `...: SAFE-1: when uses 2 duty/role keys (...)`; old-only `size = L and qa-b = yes` still passes.
- Lint baseline (`python3 bin/squad-process lint`, base 2949573): empty, exit 0. On the branch: empty, exit 0.
- Tests run green: test_team_duties (39), test_squadrules, test_sizes, test_qab_optional, test_pod_rules_process, test_process_conversion, test_process_history, test_squadadopt, test_squadprocess, test_squadprocess_apply, test_squadupgrade, test_squadcompose, test_windows_safe, test_crlf_squad_files.
- Not in this ticket (ticket 02 per its file list): `read_home`/`choose` split/header/`who_lines`, `qa: none` in read_home.
