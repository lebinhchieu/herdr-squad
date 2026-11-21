# 05 Settings defaults

## Review
AC1 | jq + git diff | `jq -r '.model,.effortLevel' templates/squad/settings/{manager,team-lead}.json`: manager `opus medium`, team-lead `sonnet low`
AC2 | tests/test_model_effort_settings.py::test_manager_and_team_lead_defaults | `cd tests && python3 -m unittest test_model_effort_settings`
AC3 | tests/test_squad_start.py::test_dry_run_shows_the_managers_model_and_effort_with_their_source | squad-start --dry-run lines `manager model: opus (from template)`, `manager effort: medium (from template)`
AC4 | six named test files | `cd tests && python3 -m unittest test_model_effort_settings test_squadsettings test_team_models test_squad_start test_templates test_team_lead_perms`: 113 tests OK

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | jq prints opus medium / sonnet low; diff 2 lines per file | - | - |
| AC2 | test_model_effort_settings.py::test_manager_and_team_lead_defaults OK | - | - |
| AC3 | squad-start dry-run opus/medium (test_squad_start); spawn dry-run sonnet/low | - | - |
| AC4 | 6 files, 113 tests OK | - | - |

## Behaviour
Diff of the two template files (only these lines changed):

```
-  "model": "sonnet",
-  "effortLevel": "high",
+  "model": "opus",
+  "effortLevel": "medium",
-  "effortLevel": "medium",
+  "effortLevel": "low",
```

Old manager defaults pinned in tests/test_squad_start.py (sonnet/high) updated to opus/medium; dev rows untouched. SQ-10 n/a (no bin/ edit).

Spawn dry-run (scratch squad, `squad-spawn team-lead x --scope s --dry-run --prompt hi`) prints `... --model sonnet --effort low ...`.

## QA blackbox

# QA blackbox 05 Settings defaults (sha 2966dad)

Live on a scratch squad (`mktemp -d`, no `plugin.pin`, so the branch's own templates apply), stub herdr, `--dry-run` only.

| AC | how | what I saw | result |
|---|---|---|---|
| AC1 | live | `jq -r '.model,.effortLevel'`: manager.json `opus` `medium`; team-lead.json `sonnet` `low`. `git diff a3a44d8 2966dad -- templates`: only those lines (manager model + effort, team-lead effort) | pass |
| AC3 | live | `squad-start --dry-run "build x"`: `manager model: opus (from template)`, `manager effort: medium (from template)`. `squad-spawn team-lead ... --dry-run` (team decided): `--model sonnet --effort low` | pass |
| Overrides still win | live | flag `--model sonnet --effort high` -> `(from flag)`; squad `settings/team-lead.json` opus/high -> `--model opus --effort high`; `scope.md` line `model team-lead: opus high` -> same | pass |
| AC2, AC4 | Developer's run, not mine | the tests belong to QA whitebox | n/a |

Note: in this repo's own squad the Manager dry-run still prints `sonnet`/`high` because `plugin.pin` pins 0.9.5 and the squad's overlay; that is the old-squads-keep-old-defaults case in the ticket's compatibility note, for the Manager to tell Chieu.

Follow-up (not a FAIL): I did not fill my column of `checks.md` (it sits in the Developer's worktree, SAFE-4); this file is my record.

## QA whitebox

# QA whitebox 05, sha 2966dad
Diff read: manager.json opus/medium, team-lead.json sonnet/low (only those lines), one new test row, manager pins in test_squad_start.py updated. `jq` prints opus/medium and sonnet/low (AC1).
Ran Dev's 6 files + grep hits test_squad_spawn, test_squad_respawn: 252 tests, 1 failure: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file`. It fails the same way on main a3a44d8 (not caused by 05). `grep -rl` of the test name over scopes/_done: 10+ hits (repeat base failure, SQ-17).
PASS.
## Follow-ups
- SQ-17: the test above is a repeat base failure with no fix ticket: Chieu to decide (fix ticket or keep).
- AC3 spawn dry-run output is the Dev's claim (evidence.md:32); test_squad_start covers the manager side.
