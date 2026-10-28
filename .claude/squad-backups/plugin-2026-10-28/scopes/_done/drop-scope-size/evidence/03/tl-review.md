# TL review 03 (code sha 61fff86, branch squad/plugin/drop-scope-size/plugin-dev-dsz-3, base 6ec3a75)
- Bin diff read. Run: test_team_cli, test_squad_migrate, test_squadadopt, test_squadcompose, test_squadrules, test_crlf_squad_files, test_windows_safe OK; lint exit 0.
- Dry run on copy of plugin-bk261023 with 3 _done scopes copied into scopes/: S -> none (commentary kept), M -> qa-white, qa-black. plan_scopes skips scopes/_done/* by design.
- F1 (FAIL): blank size + design/architecture yes or qa-b no: lines dropped, no trace in file (check only printed). Fix: comment lists every dropped old line when check non-empty or team blank; test.
- Also 09: F1 template lost `qa: full` (arch.md:48); returned to dsz-9, 09 final sha moves again.
- Re-check 13ed665 (evidence b7a512e, check --base 13ed665 exit 0): F1 closed (comment lists every dropped old line when team blank or check non-empty; test added); 4 test files OK. Final sha: 13ed665 code / b7a512e evidence.
- 03 re-check 64871b4 (evidence a0ec659, check exit 0): F1 closed, tests OK, live missing home rc 2, empty home undecided. Final sha named: 64871b4 / a0ec659.
- DONE: code 64871b4, final evidence 0f4305d (evidence-only, check exit 0).
