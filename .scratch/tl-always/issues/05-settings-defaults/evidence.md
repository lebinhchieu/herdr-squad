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
