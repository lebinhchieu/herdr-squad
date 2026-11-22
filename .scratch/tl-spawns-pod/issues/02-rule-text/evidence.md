# 02 Rule text: evidence

Note (D9): contradicts ADR 0010 and the "spawns and retires Developers" sentence of ADR 0030; ADR 0032 (ticket 04) amends both. Not merged yet.

## Review

AC trace (details in `## Checks`):
- AC1 | `grep -rn "spawns and retires Developers\|retire only Developers\|spawns Developers; you do not" templates/squad/process/` | no hit
- AC2-AC8 | `tests/test_rules_contract.py`, `tests/test_rules_wording.py`, `tests/test_qab_optional.py` | `cd tests; python3 -m unittest <file>`
- AC9 | awk loop over SPAWN-3/4/4a | `roles: manager, team-lead` x3
- AC10 | `git diff main --stat -- _removed.md` empty; rule-ID diff per edited file empty | run
- AC11 | `skills/squad-process-update/changelog.md` top entry v23 | read
- AC12-AC15 | unittest list below | run

## Behaviour

Run from `tests/`: `python3 -m unittest test_rules_contract test_rules_wording test_dev_rules_size test_sizes test_small_files_equivalence test_qab_optional test_old_language_inventory test_processlint test_windows_safe test_utf8_helpers test_instructions test_promotion_0_6_0` -> Ran 158 tests, OK.
SQ-10 files (test_windows_safe, test_utf8_helpers, test_instructions) are in that run: OK.
Tests updated: `test_rules_contract.py` (renamed `test_team_lead_spawns_and_retires_the_pod`, new SPAWN-9 content assertion, new `roles:` retarget and no-ID-removed test, SPAWN-2b assertion), `test_qab_optional.py` (SIZE-21a phrase). None skipped.
AC10: `_removed.md` diff empty; rule-ID diff empty for spawning, cost, starting, sizes, files, messages, who, goal.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | grep command above: no hit |  |  |
| AC2 | test_rules_contract test_spawning_cost_and_safety_follow_the_team: ok |  |  |
| AC3 | test_team_lead_spawns_and_retires_the_pod: ok |  |  |
| AC4 | test_rules_wording: ok |  |  |
| AC5 | read spawning/starting/messages: phrase present |  |  |
| AC6 | test_qab_optional SIZE-21a: ok |  |  |
| AC7 | read files/goal/who: ok |  |  |
| AC8 | read SPAWN-10b: ok |  |  |
| AC9 | awk loop: team-lead on all three |  |  |
| AC10 | diff checks: empty |  |  |
| AC11 | changelog v23 read |  |  |
| AC12 | 158 tests ok |  |  |
| AC13 | 158 tests ok |  |  |
| AC14 | included in 158: ok |  |  |
| AC15 | test_rules_contract no-size-word test: ok |  |  |
