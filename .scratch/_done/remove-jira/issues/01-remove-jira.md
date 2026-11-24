# Task 01: remove Jira and Confluence from process and settings

Status: ready
Ticket path (Developer commits this file there first): `.scratch/remove-jira/issues/01-remove-jira.md`
Duties: design notes Developer; technical AC QA whitebox with the Developer; business AC the ticket as written; code check QA whitebox; behaviour check QA blackbox; hand in to both QAs; full suite and `promote.md` QA whitebox (targeted tests by default, [SUITE-1b]). Risk flag, user-visible change or business doubt found while building: `BLOCKED 01`. Nothing to promote: `promote.md` says so, no promotion task. Cite [SQ-2] (AC trace in `## Review`), [SQ-10] (bin/ or printed text changes: also run the three whole-repo files).

Files: templates/squad/process/safety.md, templates/squad/settings/*.json, README.md, bin/squad-spawn, templates/squad/project.md, tests/test_squadsettings.py, tests/test_team_lead_perms.py, tests/test_dev_rules_size.py, .claude-plugin/plugin.json

## Brief (Chieu)
Remove the Jira rules from the squad, both process and settings. Mention nothing: no "removed" note, no comment.

## Files (this task owns them all; no parallel task)
- `templates/squad/process/safety.md`: delete rule SAFE-2 (whole section).
- `templates/squad/settings/{architect,ba,designer,dev,manager,qa-blackbox,qa-whitebox,team-lead,tech-lead}.json` (and `token-coach.json` if it carries entries): delete every `mcp__atlassian__*` and `mcp__claude_ai_Atlassian_Rovo__*` entry from `ask`. Keep JSON valid; keep the git `deny` entries and everything else unchanged. If `ask` is left empty, drop the key only if other settings files without entries do.
- `README.md:77`: drop "and every Jira/Confluence write tool" from the denied sentence; keep the rest.
- `bin/squad-spawn:46`: usage example `"mcp": ["atlassian"]` -> a neutral server name.
- `templates/squad/project.md:8`: "<spec / ticket / Confluence export paths>" -> "<spec / ticket / export paths>".
- `tests/test_squadsettings.py` (`test_atlassian_writes_ask_not_deny_and_git_stays_denied`): drop the Atlassian assertions, keep the git-stays-denied assertions (rename the test). `tests/test_team_lead_perms.py:34-35`: drop the Atlassian assertions.
- `tests/test_dev_rules_size.py:95`: SAFE-2 is in a list of rule ids; re-point or drop it. `tests/test_squadrules.py` uses SAFE-2 only as a fixture name in a synthetic rules file: leave unless it reads the real file.
- Plugin version bump 0.9.2 -> 0.9.3 in `.claude-plugin/plugin.json` ([SQ-5]); `grep -rn 0.9.2` over the repo (excluding `.git`, `.scratch`, `_runtime`, `_done`, changelogs) lists every spot to change.
- Leave alone: `.scratch/*` history, `skills/squad-process-update/changelog.md`, `hooks/squads/fixtures/real.json`, `.claude/squads/**`.

## AC
1. `grep -rIil -e jira -e atlassian -e confluence templates bin agents hooks tests skills README.md CONTEXT.md docs` lists only `hooks/squads/fixtures/real.json` and `skills/squad-process-update/changelog.md` (history, stays).
2. Rule SAFE-2 is in no composed rule file; `squad-process lint` passes; nothing cites `[SAFE-2]` (`grep -rn 'SAFE-2' templates bin agents hooks`, and `skills/*/SKILL.md`; synthetic fixtures in `tests/` and the changelog stay).
3. Every `templates/squad/settings/*.json` is valid JSON; each `deny` list is byte-identical to before (`git diff` shows only `ask` lines removed).
4. Targeted tests pass: touched test files plus `grep -rl` hits (at least `test_squadsettings`, `test_team_lead_perms`, `test_dev_rules_size`, `test_squadrules`, `test_instructions`, `test_windows_safe`, `test_utf8_helpers`, `test_squad_spawn` if present). Suite receipt in `$SCOPE_DIR/evidence/`.
5. Plugin version reads 0.9.3 everywhere 0.9.2 was; the `grep` for 0.9.2 finds only history.

## Evidence
`.scratch/remove-jira/issues/01-remove-jira/evidence.md` with `## Behaviour`, `## Review` (starts with the AC trace, [SQ-2]).

## Technical AC (QA whitebox; Developer: reply `ANSWER 01` with any objection before building)
Base: main 02c5b42. These sharpen the business AC; where they differ, they win.
T1. `ask` handling: after the edit no settings file contains `atlassian`/`Atlassian` (case-insensitive). If a file's `ask` would be empty, drop the key; check first with `grep -c '"ask"'` on `token-coach.json` (it has no `ask` today, so an empty `ask` is not the norm). Nothing else in a settings file changes: `git diff` on `templates/squad/settings` shows only removed `ask` lines (plus the `"ask": [` / `],` lines when the list empties and the trailing comma after `allow` stays valid JSON).
T2. `deny` and `allow` lists byte-identical: `git diff -U0 templates/squad/settings | grep '^[+-]' | grep -v -e '^---' -e '^+++' | grep -v -i atlassian` shows no `deny` or `allow` line.
T3. SAFE-2: delete the whole `## SAFE-2` section from `templates/squad/process/safety.md`. Do NOT renumber SAFE-3..SAFE-11 (other rules cite them). `squad-process lint` passes, and `squad-process rule SAFE-2` exits non-zero.
T4. SAFE-2 grep scope, correcting business AC 2: `grep -rn 'SAFE-2' templates bin agents hooks skills/*/SKILL.md` finds nothing. Leave `tests/fixtures/rules/errors/.../safety.md` and `tests/test_squadrules.py` (synthetic SAFE-2 fixtures) unchanged; do not edit `skills/squad-process-update/changelog.md`. `tests/test_dev_rules_size.py:95`: drop `"SAFE-2"` from the tuple (SAFE-5 stays in the list, so the test keeps its meaning); change nothing else in that file.
T5. Tests: `test_atlassian_writes_ask_not_deny_and_git_stays_denied` is renamed (e.g. `test_git_writes_stay_denied`) and keeps its three git `deny` assertions for every settings file; the `sets`/`full`/`18` logic goes. `test_team_lead_perms.py` lines 34-35 go and the `deny` git assertions stay. No test is skipped, loosened or deleted otherwise. No new test files; no new tests (the removal needs none).
T6. Text edits are verbatim as the ticket says: README.md:77, `templates/squad/project.md:8`, `bin/squad-spawn:46` (neutral name, e.g. `"mcp": ["playwright"]`; check no test greps that usage line, `grep -rn 'mcp.*\[' tests/test_squad_spawn*`). No "removed" note, comment or changelog line anywhere.
T7. Version: `.claude-plugin/plugin.json` reads 0.9.3; any other 0.9.2 hit is history or `tests/test_squadruntime.py:120` (a version-compare fixture, leave). Check `marketplace.json`/other manifests with `grep -rn '"version"' .claude-plugin`.
T8. Leftover check: `grep -rIil -e jira -e atlassian -e confluence templates bin agents hooks tests README.md CONTEXT.md docs skills` lists only `hooks/squads/fixtures/real.json` and `skills/squad-process-update/changelog.md` (history, left alone).
T9. Run before HANDIN and quote in `## Behaviour`: `python3 -m unittest` (or the runner) on `tests/test_squadsettings.py tests/test_team_lead_perms.py tests/test_dev_rules_size.py tests/test_squadrules.py tests/test_instructions.py tests/test_windows_safe.py tests/test_utf8_helpers.py` plus `tests/test_squad_spawn.py`, `tests/test_rules_contract.py`, `tests/test_old_language_inventory.py`, `tests/test_model_effort_settings.py` and every `grep -rl` hit of `safety.md`, `ask` settings and `squad-spawn` usage text in `tests/`. Plus `squad-process lint` and `for f in templates/squad/settings/*.json; do python3 -m json.tool "$f" >/dev/null || echo BAD $f; done`.
T10. Diff stays inside the `Files:` line. Anything else touched (including composed rule files under `.claude/squads/**`) is a finding.
Full suite: not planned; I ask the Manager only if the targeted run shows a gap.
