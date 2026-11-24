# 01 evidence

## Behaviour
- Settings: all 9 role files lost the whole `ask` key (it held only Atlassian entries); `token-coach.json` had none. Every file parses (`json.tool`), no `BAD`. Diff of `templates/squad/settings` shows only removed lines, none a `deny`/`allow` line.
- SAFE-2 section deleted, SAFE-3.. not renumbered. `./bin/squad-process lint` rc=0; `./bin/squad-process rule SAFE-2` -> "no such rule", rc=2. (The PATH `squad-process` is the pinned 0.8.1 runtime copy and still shows SAFE-2; the worktree's `bin/` was used.)
- Leftover grep (T8) lists only `hooks/squads/fixtures/real.json`; `grep -rn SAFE-2 templates bin agents hooks skills/*/SKILL.md` empty.
- Version: `.claude-plugin/plugin.json` 0.9.3 (only manifest with a version); remaining 0.9.2 hits: `tests/test_squadruntime.py:120` fixture.
- Tests (from `tests/`): test_squadsettings test_team_lead_perms test_dev_rules_size test_squadrules test_instructions test_windows_safe test_utf8_helpers test_squad_spawn test_rules_contract test_old_language_inventory test_model_effort_settings test_templates test_team_models test_crlf_squad_files: 288 run, 1 failure: `test_squad_spawn...test_a_failed_agent_start_leaves_the_old_overrides_file`. Same failure on main 02c5b42 (checked with `git archive`), so not caused by this change.

## Review
| AC | test or capture | how run |
|---|---|---|
| AC1/T8 | leftover grep: only real.json | `grep -rIil -e jira -e atlassian -e confluence templates bin agents hooks tests skills README.md CONTEXT.md docs` |
| AC2/T3/T4 | lint rc=0, rule SAFE-2 rc=2, no SAFE-2 hits | `./bin/squad-process lint`, `./bin/squad-process rule SAFE-2`, `grep -rn SAFE-2 templates bin agents hooks skills/*/SKILL.md` |
| AC3/T1/T2 | json.tool OK, diff only removed `ask` lines | `git diff -U0 templates/squad/settings` |
| AC4/T5/T9 | 288 tests, 1 failure also on main | `cd tests && python3 -m unittest <files above>` |
| AC5/T7 | plugin.json 0.9.3 | `grep -rn 0.9.2 . --exclude-dir=.git ...` |
| T6 | README:77, project.md:8, squad-spawn:46 edited | `git diff README.md bin templates/squad/project.md` |
| T10 | diff inside Files line | `git diff --stat main` |
