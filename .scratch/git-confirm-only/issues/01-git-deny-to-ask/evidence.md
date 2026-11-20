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

## QA blackbox review

### QA blackbox 01 (sha ce78580)

Business ask: risky git actions ask Chieu instead of being refused; the squad can do them when Chieu confirms.
Method: live run of `bin/squadsettings.py effective --role R` (settings/R.local.json = {}) for all 10 roles on ce78580, compared with the same run on base 19778ef. No source or diff read.

| AC | live/shot | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 no git in deny | live | effective for 10 roles | `deny` has no `Bash(git` entry in any role | pass |
| AC2 ask = old git deny + branch -D | live | set compare vs base, per role | old git deny ⊆ new ask in all 10; only extra entry is `Bash(git branch -D:*)`; allow lists identical | pass |
| AC3 non-git deny unchanged | live | compare non-git deny vs base | identical in all 10 (architect, designer, token-coach keep their Write/Edit/Read denies) | pass |
| AC4 valid JSON, dev/qa-whitebox effective | live | json.load all 10 templates; effective dev, qa-whitebox | all parse. dev: ask = push, rebase, reset --hard, checkout main, checkout dev, branch -D; merge in allow. qa-whitebox: same plus merge in ask | pass |
| Risk list complete | live | read ask per role | push, rebase, reset --hard, branch -D in all 10; merge in 8 (not dev, manager); checkout main/dev in 9 (not token-coach) | pass |
| AC7 prompt in a running pane | not tested | needs a respawned role | stated by Developer, not a pass or fail of the change | n/a |

Verdict: PASS. Tests (AC5, AC6) are QA whitebox's.

Follow-ups (not FAIL):
- Dev and manager have no merge prompt (merge stays in `allow`): a merge into main by them is not asked. Open point for Chieu, already flagged by the Tech Lead.
- Running scopes keep the old deny until a role is respawned; a real prompt was not seen live.
- Deploy has no settings entry (rule text only).

## QA whitebox review

### QA whitebox 01 — sha ce785800e5a30f719ac33c3e93ab23fabb00abfa: PASS

Checked from `git archive` of the sha in a scratch dir (nothing edited, scratch dir removed).

| Tech AC | Result | How |
|---|---|---|
| 1 no `Bash(git` in deny (10 templates) | pass | own python diff main vs sha, all 10 files |
| 2 ask = old git deny + `git branch -D`, nothing dropped | pass | per file: added `['Bash(git branch -D:*)']`, dropped `[]`; allow lists unchanged |
| 3 non-git deny unchanged | pass | per file `nongit same True` |
| 4 valid JSON; effective qa-whitebox | pass | `squadsettings.py effective --role qa-whitebox`: ask = 7 git entries, deny = [] |
| 5 tests flipped, none skipped | pass | `cd tests && python3 -m unittest test_squadsettings test_team_lead_perms test_templates test_squad_spawn`: 148 run, 1 failure, 1 skipped (skip is on base, not new) |
| 6 `bin/squadsettings.py` unchanged | pass | diff stat has no bin/ file |
| 7 not live-verified | stated in evidence.md | |

Known failing on base, confirmed by running it on main: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` (not a FAIL).
Also ran `test_squadscaffold test_architect_handoff test_rules_wording`: 46 OK. The other `grep -rl` hits are fixtures (data).

#### Follow-ups (not FAIL)
- `git switch main` / `git checkout -B main` are not matched by the checkout entries (same hole as before).
- Empty `"deny": []` left in 7 templates: valid and the merge accepts it.
