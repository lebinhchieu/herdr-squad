# 01 git risk actions: deny to ask

## Review
AC trace
| AC | Test or capture | How run |
|---|---|---|
| AC1 no `Bash(git` in deny | `test_git_risk_actions_ask_and_are_never_denied` (test_squadsettings) | `cd tests && python3 -m unittest test_squadsettings` |
| AC2 ask = old git deny + `git branch -D` | per-file set diff below | python snippet in Behaviour |
| AC3 non-git deny unchanged | same snippet (`nongit deny same= True`) | same |
| AC4 valid JSON, effective dev / qa-whitebox | `test_every_role_has_settings_that_parse...`; effective output below | `bin/squadsettings.py effective` |
| AC5 tests flipped | test_templates `test_git_merge_is_allowed_for_dev_and_manager_and_every_git_risk_asks_never_denied`, test_team_lead_perms, test_squadsettings (2), test_squad_spawn lean settings | `cd tests && python3 -m unittest test_squadsettings test_team_lead_perms test_templates test_squad_spawn` |
| AC6 `bin/squadsettings.py` unchanged | `git diff --stat` shows no bin/ file | `git diff main --stat` |
| AC7 not live | stated below | - |

## Behaviour
Set diff per template (new `ask` minus old git `deny`; old git `deny` minus new `ask`; non-git deny identical):
every one of the 10 files: added `['Bash(git branch -D:*)']`, dropped `[]`, non-git deny same `True`.
Merge: dev and manager keep it in `allow` and have none in `ask`; the other 8 have it in `ask` (token-coach too). token-coach has no checkout entries, as on base.

Effective settings (`squadsettings.py effective --role R --squad-dir <tmp with settings/R.local.json = {}> --template-root .`):
- qa-whitebox: ask = push, merge, rebase, reset --hard, checkout main, checkout dev, branch -D; deny = []; merge not in allow.
- dev: ask = push, rebase, reset --hard, checkout main, checkout dev, branch -D; deny = []; `Bash(git merge:*)` in allow: True.

Checked, no change: squad `settings/*.local.json` (plugin, accounts, board) hold no git entry and no deny. `bin/squadsettings.py` unchanged.

Tests: `cd tests && python3 -m unittest test_squadsettings test_team_lead_perms test_templates test_squad_spawn`: 148 run, 1 failure = the known failing on base `SpawnDryRunTest::test_a_failed_agent_start_leaves_the_old_overrides_file`. `grep -rl 'git push\|reset --hard\|Bash(git' tests/` hits: the 4 files above plus two fixtures (inbox golden, escalations.md), which are data, not settings.

Not verified live: a real prompt in a running pane needs a respawned role; running scopes keep their old generated `roles/*.settings.json` until respawn.
