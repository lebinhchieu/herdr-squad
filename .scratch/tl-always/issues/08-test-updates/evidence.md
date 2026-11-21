# 08 Test updates

## Review
AC1 | tests/test_squad_ledger.py (NoticeTest, 2 tests) | `cd tests && python3 -m unittest test_squad_ledger` → 17 OK
AC2 | tests/test_squad_spawn.py (SpawnTaskPromptTest, SpawnTeamGateTest) | `cd tests && python3 -m unittest test_squad_spawn` → 107 run, 1 known base failure

## Behaviour
- Ledger: the 3rd-return notice always says `to Team Lead [LC-7b]`.
- Spawn: a team-lead spawn is accepted whatever `team:` says (new test). A roster without a team-lead row exits 2 "roster.md has no team-lead row". The tech-lead, qa-blackbox, designer and architect subcases are kept.
- Only failure: `test_a_failed_agent_start_leaves_the_old_overrides_file`, listed in suite-triage line 6 as known; not touched.
- No `bin/` or `templates/` edits, so the SQ-10 whole-repo tests are not required.
