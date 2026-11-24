# 01: risky git actions move from `deny` to `ask` in the role settings

Duties: design notes tech-lead; technical AC tech-lead; business AC ticket (+ qa-black); promote.md tech-lead; full suite tech-lead.
Files: templates/squad/settings/*.json (10), tests/test_squadsettings.py, tests/test_team_lead_perms.py, tests/test_templates.py, tests/test_squad_spawn.py

Owner: Tech Lead (design, AC). Depends on: nothing. Base: main 19778ef.
Ticket file the Developer commits: `.scratch/git-confirm-only/issues/01-git-deny-to-ask.md` (copy this design into it).

## Design
Claude Code order is deny, then ask, then allow. An entry in `deny` is a refusal; the same entry in `ask` is a prompt Chieu answers. So each git risk entry moves from `permissions.deny` to `permissions.ask`, in place, and nothing else changes.

### Final risk-action list
| Action | Settings entry | Roles |
|---|---|---|
| push, incl. `--force` | `Bash(git push:*)` | all 10 |
| rebase | `Bash(git rebase:*)` | all 10 |
| reset --hard | `Bash(git reset --hard:*)` | all 10 |
| merge | `Bash(git merge:*)` | the 8 that had it in `deny` (all but dev, manager; token-coach and architect/designer included) |
| checkout main, dev | `Bash(git checkout main:*)`, `Bash(git checkout dev:*)` | the 9 that had them (not token-coach: it had none; keep it so) |
| branch -D (new) | `Bash(git branch -D:*)` | all 10; `Bash(git branch:*)` is in `allow` for 7 roles and ask beats allow |
| deploy | no entry | out of settings: no tool runs a deploy; the rule lines (LC-13, tech-lead card, WHO-5) stay as they are |

- Dev and manager keep `Bash(git merge:*)` in `allow` and get no merge entry in `ask`: a pattern cannot tell a merge into the worktree branch from one into main, and a Developer merges inside its own worktree (GOAL-6b). The Manager's merge into the PO's branch stays gated by MRG-1 (only on the PO's request) and `squad-merge-check`. Flagged to the Manager as an open point for Chieu.
- Non-git denies (Write/Edit of `.claude/squads/...`, Read of `~/.claude*/projects/**`) stay in `deny`, untouched.
- `bin/squadsettings.py` already unions `ask`; it does not change. The squad `settings/*.local.json` files (plugin, accounts, board) hold no git entry and no deny (checked on main): no change there. Name them in `## Behaviour` as checked.
- Compatibility: running scopes keep their generated `roles/*.settings.json` (old deny) until respawn; legacy squads are left alone. A local file that adds a git `deny` would still win after the union; none exists.

## Files
- `templates/squad/settings/{architect,ba,designer,dev,manager,qa-blackbox,qa-whitebox,team-lead,tech-lead,token-coach}.json`
- `tests/test_squadsettings.py` (lines ~106, ~112), `tests/test_team_lead_perms.py` (~32-33), `tests/test_templates.py` (~56-60), `tests/test_squad_spawn.py` (~277)
- Not touched: `bin/squadsettings.py`, `.claude/squads/*/settings/*.local.json`, rule text, README, version (all 02).

## Technical AC
1. No `Bash(git ...)` entry is in `permissions.deny` of any of the 10 templates; `grep -n 'Bash(git' templates/squad/settings/*.json` shows the risk entries on `ask` only (the `allow` lines are unchanged).
2. Per template, the set of git entries in `ask` equals the set that was in `deny` on base, plus `Bash(git branch -D:*)`; nothing is dropped, nothing else added. Quote the per-file diff of the two sets in `## Behaviour`.
3. Non-git deny entries: `git diff` on those lines is empty.
4. All 10 files are valid JSON. `python3 bin/squadsettings.py effective --role qa-whitebox ...` and `--role dev ...` (command and output in `## Behaviour`): git risk entries under `ask`, none under `deny`; dev still has `Bash(git merge:*)` in `allow`.
5. Tests flipped to match: `test_only_developers_and_the_manager_may_merge...` (templates; rename it, it no longer says "nobody may push": assert merge in `allow` for dev/manager and in `ask` for the rest, and the other risk entries in `ask`, none in `deny`), `test_git_writes_stay_denied` (replace by one test over all template files: risk entries in `ask`, no `Bash(git` in `deny`; no matrix), the team-lead settings test, the qa-blackbox effective test and the spawn lean-settings test (`ask`, not `deny`). No test newly skipped, none deleted without its replacement.
6. `bin/squadsettings.py` unchanged unless a test shows it must.
7. Behaviour not verified live: a real prompt in a running pane needs a respawned role. State this in `## Behaviour`; QA blackbox checks the effective settings, not a prompt.

## SQ-1 table (files deleted or moved, and their readers)
No ticket deletes or moves a file, so no reader-before-deleter order applies. Reads across the two tickets, for the relation check (SQ-6):
| Ticket | Writes | Read by | Related to |
|---|---|---|---|
| 01 | `templates/squad/settings/*.json`, 4 test files above | the 4 tests; README (doc only, edited by 02) | none: 02 shares no file and no `grep -rl` test hit |
| 02 | `safety.md`, `merge.md`, `who.md`, README, changelog, `plugin.json`, `tests/test_dev_rules_size.py` | rule tests; none read the settings files | none |
02 starts from 01's passed branch (an ancestor, so no integration task).

## Tests to run (targeted, no full suite)
`python3 -m unittest tests/test_squadsettings.py tests/test_team_lead_perms.py tests/test_templates.py tests/test_squad_spawn.py`, plus every hit of `grep -rl 'git push\|reset --hard\|Bash(git' tests/`. SQ-10 does not apply (no `bin/` or printed text change). The Tech Lead's full run, if Chieu says yes, happens once on the integration sha.

## Manager notes (SQ-15 dry run on 19778ef)
- Run the tests from `tests/` (`cd tests && python3 -m unittest test_squadsettings ...`); from the repo root they fail to import.
- Known failing on base: test_squad_spawn.py::SpawnDryRunTest::test_a_failed_agent_start_leaves_the_old_overrides_file (not a FAIL).
- Manager `git merge` stays in `allow` unless Chieu answers otherwise (inbox); a change then rides 02.
