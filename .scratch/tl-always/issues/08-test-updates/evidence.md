# 08 Test updates

## Review
AC1 | tests/test_squad_ledger.py (NoticeTest, 2 tests) | `cd tests && python3 -m unittest test_squad_ledger` → 17 OK
AC2 | tests/test_squad_spawn.py (SpawnTaskPromptTest, SpawnTeamGateTest) | `cd tests && python3 -m unittest test_squad_spawn` → 107 run, 1 known base failure

## Behaviour
- Ledger: the 3rd-return notice always says `to Team Lead [LC-7b]`.
- Spawn: a team-lead spawn is accepted whatever `team:` says (new test). A roster without a team-lead row exits 2 "roster.md has no team-lead row". The tech-lead, qa-blackbox, designer and architect subcases are kept.
- Only failure: `test_a_failed_agent_start_leaves_the_old_overrides_file`, listed in suite-triage line 6 as known; not touched.
- No `bin/` or `templates/` edits, so the SQ-10 whole-repo tests are not required.

## QA whitebox

### 08 QA whitebox, sha 8f7b896 (base 6b604e4)
Verdict: PASS

- Diff: tests/test_squad_ledger.py, tests/test_squad_spawn.py + ticket/evidence files. No bin/ or templates/ edits (git diff --name-only checked).
- Ledger: both NoticeTest tests expect `to Team Lead [LC-7b]` for every team line.
- Spawn: no-QA test now expects exit 2 + "roster.md has no team-lead row" for a roster without a team-lead; team-lead removed from the gate loop (tech-lead, qa-blackbox, designer, architect kept); new test_the_team_lead_is_always_on_the_team (exit 0).
- Run: `cd tests && python3 -m unittest test_squad_ledger test_squad_spawn` -> 124 run, 1 failure = test_a_failed_agent_start_leaves_the_old_overrides_file (known base, suite-triage). test_squad_log_message (grep hit) 24 OK.
- squad-evidence check on the evidence folder: ok.

Follow-ups: test_three_returns_notice_always_names_the_team_lead reuses `route` as loop variable (harmless; all routes equal).

## QA blackbox

### 08 QA blackbox, sha 8f7b896 (base 6b604e4)

| AC (tasks/08.md) | how | saw | result |
|---|---|---|---|
| 1 NoticeTest expects `to Team Lead [LC-7b]` | live: `unittest -v test_squad_ledger.NoticeTest` | 10 tests ok, incl. team-lead-naming tests | pass |
| 2 SpawnTaskPromptTest: team-lead present; roster without team-lead row exits 2 | live: `unittest -v test_squad_spawn.SpawnTaskPromptTest` | 5 ok, incl. `..._and_a_roster_without_one_is_refused` | pass |
| 2 SpawnTeamGateTest: team-lead accepted; tech-lead/qa-blackbox/designer/architect kept | live: `unittest -v test_squad_spawn.SpawnTeamGateTest` | 12 ok, incl. role-not-on-team and `test_the_team_lead_is_always_on_the_team` | pass |
| Test-only, no bin/ or templates/ edits | `git diff --stat 6b604e4 8f7b896 -- bin templates` | empty (4 files: 2 tests, ticket, evidence) | pass |
| Known base failures untouched | full run of both files: 124 tests, 1 failure | only `SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` (known base failure, not judged) | pass |
