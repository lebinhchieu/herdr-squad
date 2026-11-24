# 01 Jira and Confluence write tools: deny to ask

Status: ready-for-agent
Feature: update-not-deny (draft here; commit it to `.scratch/update-not-deny/issues/01-jira-deny-to-ask.md` with your first commit)
Repo: /home/chieule/workspace/squad. Base: main. Touches: `templates/squad/settings/*.json`, `templates/squad/process/safety.md`, `tests/test_squadsettings.py`, any test the grep below finds.
Duties: no Tech Lead, BA or QA on the team. Developer owns design notes, technical AC, `promote.md` (nothing to promote unless a rule text moves into CONTEXT.md/ADR; then say so) and the full suite. Business AC = this ticket as written. Hand in to the Manager (`HANDIN NN: ...`), who confirms `evidence.md` + `## Review` (starts with an AC trace table, one line per AC: `AC<n> | test or capture file | how run`). A risk flag, user-visible change or business doubt: `BLOCKED NN`.

## Why
PO: Jira MCP writes are blocked outright (`deny`); the PO wants a prompt instead so he can approve a write.

## What
In every role template under `templates/squad/settings/` (9 roles + token-coach if it has a deny list), move the Jira/Confluence write entries (every `mcp__atlassian__*` and `mcp__claude_ai_Atlassian_Rovo__*` entry now in `permissions.deny`) into `permissions.ask`. Keep the git entries (`git push`, `rebase`, `reset --hard`, `checkout main|dev`) in `deny`. Update the SAFE-2 text in `templates/squad/process/safety.md` so it no longer says "no writes": a write needs the PO's approval at the prompt; read stays free. Keep the rule short, one statement, no history.
The merge in `bin/squadsettings.py` unions `ask`, so squad overlays need no change; do not touch it unless a test shows it must.
Note: Claude Code evaluates `deny` before `ask`; an entry left in both stays denied. Check no entry is left in `deny`.

## AC
- AC1: No `mcp__atlassian__*` or `mcp__claude_ai_Atlassian_Rovo__*` entry is in any template's `deny`.
- AC2: Each of those entries is in `ask` in every template that had it in `deny` (same set, no loss).
- AC3: The git entries stay in `deny` in every template that had them.
- AC4: SAFE-2 in `safety.md` matches the new behaviour; `squad-process lint` passes (run `grep -rl 'SAFE-2\|createJiraIssue\|Atlassian' tests/ templates/ bin/` and run every test hit).
- AC5: One test in `tests/test_squadsettings.py` covers AC1-AC3 over all role files (not a matrix per tool). Existing tests still pass; none newly skipped.

## Evidence
`evidence.md` for this ticket: `squad-evidence` folder rules. Behaviour: the effective settings for one role built through `squadsettings.py effective` (command + output) show the Jira entries under `ask`, none under `deny`.

## Comments
