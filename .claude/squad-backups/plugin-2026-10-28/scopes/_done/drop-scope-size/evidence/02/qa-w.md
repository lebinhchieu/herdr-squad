# QA whitebox 02 (code sha 08ecf4f, evidence 1f27cc1, branch squad/plugin/drop-scope-size/plugin-dev-dsz-2)

## Passed (run by me)
- Diff 991cab6..08ecf4f read vs ticket AC (design 01b) and architecture.md: read_home team parse/scaffold, qa-none tolerance, load_rules/choose split, header team:/duties:, who duty lines: no code finding.
- Tests OK: test_squadcompose 87, test_team_duties 39, test_squadrules 58, test_sizes 36, test_qab_optional 13, test_crlf_squad_files 8, test_windows_safe 11. `squad-process lint` empty, exit 0 (= base).
- Real samples (refine-process:7, extractor-role:8-9, svgdraw:7, report-ui-fix:7, grillui:7-10) compared byte for byte with the source files: all equal.
- Byte-equal proof vs base compose (60 size-home x role pairs) present; CLI never sets legacy_scaffold (test scans bin/ + hooks/).
- Live (REV-5b-style, read-only) on a copy of this scope: size home composes as before; same home with `team: ba, team-lead, tech-lead, qa-white, qa-black, architect` gives `team:` header, `duties:` line (13 owners), exit 0.
- Evidence file: `squad-evidence check --base 08ecf4f` ok.

## Finding (style, one return, REV-17)
- F1 `tests/test_squadcompose.py:631-634, 657-659, 661-662` (class LegacyScaffoldTest): three tests for one behaviour. `test_design_yes_qa_b_no_shape_reads_old_and_maps_to_a_valid_team` already asserts both the old-path ComposeError and `legacy_team("M","no","yes")`; `test_design_yes_qa_b_no_still_raises_on_the_old_path` and `test_design_yes_qa_b_no_is_a_valid_team_through_the_scaffold_mapping` repeat each half verbatim. Dead duplicate tests inflate the suite and drift apart later. Pass: keep one test (the first), delete the other two, re-run test_squadcompose.

## Forward notes (not findings)
- Transitional: a decided-team home has no `size` fact, so the rules line carries alternatives of both sides (e.g. FILE-5a and FILE-5b, SIZE-5a...) until 04a-06; TL accepted, nothing ships on it. Check it is gone at 05/06.
- I8 (design yes + qa-b no): old path still raises; 03 ticket must state the converter answer.
- Goal Manager header prints `team: undecided` (golden updated); confirm with the BA spec at 09.

## Re-check (LC-3b) on 6ec3a75
- F1 closed: only `test_design_yes_qa_b_no_shape_reads_old_and_maps_to_a_valid_team` remains; the two duplicates are deleted. Diff 08ecf4f..6ec3a75 = those 7 test lines + evidence.
- test_squadcompose 85 OK; `squad-process lint` empty, exit 0.
- Verdict: PASS.
