# 04 Promotion: ADR 0031 and CONTEXT.md terms: evidence
sha: 722b549 (docs by Dev 6; evidence by Dev 7)
## Review
AC trace:
- AC1 | `head -8 docs/adr/0031-home-upgrade-mid-scope.md` (title, Status, Amends, Decision) | read
- AC2 | `git diff e728bb8..722b549 -- docs/adr/0016*` adds only the header line and a blank line | git diff
- AC3 | `git diff e728bb8..722b549 -- docs/adr/0030*` one line, ", until Chieu moves one (ADR 0031)" | git diff
- AC4 | `grep -n 'Pin move\|Plugin pin\|Process update' CONTEXT.md` (lines 123, 143, 151) | grep
- AC5 | claims match `bin/squadhomes.py`; QA whitebox checks each | read
- AC6 | `grep -rn 'between scopes only' CONTEXT.md docs/adr/0016* skills/` | grep
- AC7 | `git diff --stat e728bb8..722b549`: CONTEXT.md, two ADRs, one new ADR, 03's evidence; no code or test | git diff

## Behaviour
AC6 output: only `docs/adr/0016-...md:7` (the header exception, which quotes the sentence) and `:11` (the Decision line, kept).
`grep -rl 'between scopes only\|keep their runtime\|Plugin pin\|Process update' tests/` prints nothing, so no test reads the edited text.
`git diff --stat e728bb8..722b549`: CONTEXT.md 8, 0016 2, 0030 2, 0031 new 23 lines, plus 03's evidence.md.
Tests on the final tree (docs unchanged since; run with 06): `cd tests; python3 -m unittest test_windows_safe test_utf8_helpers test_instructions test_squadupgrade test_promotion_0_6_0 test_squad_spawn`: 200 tests, OK.
