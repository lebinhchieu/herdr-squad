# TL review 02 (final code sha 08ecf4f, evidence 1f27cc1, branch squad/plugin/drop-scope-size/plugin-dev-dsz-2, base 991cab6)
- Bin diff read (991cab6..08ecf4f). Finding from 32da49a (team: beside old line = ComposeError, no adopt pointer) fixed in 08ecf4f (bin/squadcompose.py +6, test +20; 4 keys, LF+CRLF).
- Run: `squad-process lint` exit 0; test_squadcompose, test_team_duties, test_squadrules, test_squadprocess, test_crlf_squad_files, test_windows_safe all OK.
- `squad-evidence check <folder> --base 08ecf4f` exit 0 (evidence-only commit 1f27cc1).
- Decisions recorded: no size fact for team home (transitional); scaffold branch-internal, removed in ticket 12 with a permanent test.
- No open finding. Final sha 08ecf4f.

## Final (after QAW FAIL F1, test-only fix)
- Final code sha 6ec3a75 (08ecf4f + test-only: two duplicate tests dropped; bin/ identical). Evidence sha a305d47 (evidence-only), `squad-evidence check --base 6ec3a75` exit 0 (run by me). lint exit 0; six touched test files OK. QAW PASS on 6ec3a75; QAB PASS on 08ecf4f, bin unchanged. 02 accepted.
