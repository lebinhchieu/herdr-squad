# 05 Merge main into the scope branch: evidence

## Review

AC trace (details in `## Checks`):
- AC1 | `git merge-base --is-ancestor main HEAD` | exit 0
- AC2 | `grep -n "watchdog\|team-lead" bin/squad-spawn` | watchdog `ensure` block (line ~578) and Team Lead guard (lines 91-97, 139, 153) both present; auto-merged, no conflict markers
- AC3 | `grep -c '^## v23' skills/squad-process-update/changelog.md` | prints 1; `## v24` says Plugin 0.10.5, deploy 0.10.5, rollback back to 0.10.4
- AC4 | `grep -rn '0\.10\.4' .claude-plugin/plugin.json` | no hit; version 0.10.5
- AC5 | `git grep -n '0\.10\.4' -- docs/adr/0032* agents templates` | no hit (ADR 0032 now says 0.10.5)
- AC6 | `cd tests; python3 -m unittest <file>` | 9 files OK, see Behaviour

## Behaviour

Merge of main (723a71d) into 4b356d7; only conflict was changelog.md, resolved by keeping main's v23 as is and renaming this scope's entry to v24 (0.10.5). plugin.json, bin/squad-spawn and starting.md merged cleanly.

Targeted tests on the merge result (pytest is not installed; unittest used):
- test_team_lead_perms 14 OK; test_squadsettings 25 OK; test_rules_contract 18 OK
- test_squad_spawn 111 OK; test_squad_start 49 OK; test_squad_watchdog 89 OK (the three test files main touched)
- SQ-10 trio: test_windows_safe 14 OK; test_utf8_helpers 14 OK; test_instructions 16 OK

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | exit 0 | - | - |
| AC2 | both blocks present | - | - |
| AC3 | count 1, v24 0.10.5 | - | - |
| AC4 | no hit | - | - |
| AC5 | no hit | - | - |
| AC6 | 9 files OK | - | - |
