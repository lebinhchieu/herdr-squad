# TL review 01 (final code sha d5a4b9c, branch squad/plugin/drop-scope-size/plugin-dev-dsz-1)
- Diff read vs AC (design 01a) and architecture.md: no code finding. DUTIES owners match base SIZE-22/22a (checked the hand-copied table in tests/test_team_duties.py).
- Run: `squad-process lint` empty, exit 0 (= base). test_team_duties 39, test_squadrules 58, test_sizes 36, test_qab_optional 13, test_pod_rules_process 10, test_process_conversion, test_process_history, test_squadadopt, test_squadupgrade, test_squadcompose, test_squadprocess(_apply), test_windows_safe, test_crlf_squad_files: all OK.
- Finding F1 (process): d5a4b9c mixes code and evidence; `squad-evidence check --base d5a4b9c` needs an evidence-only commit on top. Dev told.
- Open: svgdraw `M —` sample missing on this machine (QAW to confirm). `qa: none` read_home fix and read_home/choose/who_lines items go to ticket 02.

## Final (after QAW FAIL, test-only fix)
- Final code sha 991cab6 (d5a4b9c + one test-only commit: real `M — signals` sample from plugin-bk261023 report-ui-fix scope.md:7, verified). Evidence sha 1fc8cb7 (evidence-only, `squad-evidence check --base 991cab6` exit 0, ticket .md copied temporarily). lint empty; test_team_duties 39 and test_squadrules OK on 991cab6. Both QAs PASS on 991cab6 per Dev. 01 accepted.
