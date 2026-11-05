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
