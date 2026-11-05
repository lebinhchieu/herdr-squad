# Evidence 01 Jira and Confluence write tools: deny to ask

## Behaviour
Command (scratch squad dir with an empty `dev.local.json`, template root = this repo):
`python3 bin/squadsettings.py effective --role dev --squad-dir $T/sq --template-root . --out $T/o.json`, rc=0. Output read back:
- `permissions.deny` = `Bash(git push:*)`, `Bash(git rebase:*)`, `Bash(git reset --hard:*)`, `Bash(git checkout main:*)`, `Bash(git checkout dev:*)`. No Atlassian entry.
- `permissions.ask`: 18 `mcp__atlassian__*` / `mcp__claude_ai_Atlassian_Rovo__*` entries (e.g. `mcp__atlassian__createJiraIssue`, `mcp__atlassian__editJiraIssue`).
- token-coach had no Atlassian entry; unchanged.
- SAFE-2 now: "Jira, Confluence writes ask" / "A write needs PO approval; read is free." Composed size does not grow (`test_dev_rules_size` OK).

## Tests
New `test_atlassian_writes_ask_not_deny_and_git_stays_denied` (all 10 role files). `test_team_lead_perms` now expects the Atlassian entries in `ask`, none in `deny`.
Run: test_squadsettings, test_team_lead_perms, test_squadrules, test_sizes, test_dev_rules_size, test_ca_launchers. All OK except `test_ca_launchers.test_scripts_are_syntactically_valid_bash` (ERROR reading a bin file; this ticket does not touch `bin/`). `squad-process lint` rc=0.

## Review
AC trace:
AC1 | tests/test_squadsettings.py::test_atlassian_writes_ask_not_deny_and_git_stays_denied | `cd tests; python3 -m unittest test_squadsettings`
AC2 | same test (18 entries in `dev`, every role equal) + reviewer script vs `HEAD~1` | same
AC3 | same test (push, rebase, reset --hard in every file's deny) | same
AC4 | templates/process/safety.md SAFE-2; test_dev_rules_size, test_squadrules | `bin/squad-process lint` rc=0; unittest files
AC5 | same single test; test_team_lead_perms updated | unittest

Fresh-context reviewer (sonnet, high): AC1-AC5 pass, no defects. Findings fixed: AC2 count check (18) and AC3 now checks push, rebase, reset --hard, no token-coach exemption. Not fixed: test reads template files, not `effective` (effective proof is in Behaviour above).
`test_ca_launchers.test_scripts_are_syntactically_valid_bash` errors on a file read in `bin/`, which this diff does not touch; to confirm against main at the final suite.
