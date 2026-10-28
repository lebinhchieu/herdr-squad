Status: ready-for-agent
Type: task
Task ID: 08
Touches: `bin/squadsettings.py` (new), `bin/squad-spawn` (settings section only), `tests/test_squadsettings.py` (new), `tests/test_squad_spawn.py`, `tests/test_team_lead_perms.py`, `tests/test_model_effort_settings.py`
Does not touch: `templates/squad/settings/*.json` contents, `agents/*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadsettings test_squad_spawn test_team_lead_perms test_model_effort_settings test_windows_safe`
Blocked by: 05

# 08: Settings are template plus a squad overlay, merged at spawn

**Done when `squad-spawn` builds each agent's settings from the pinned template plus `settings/<role>.local.json`, so a plugin settings change reaches a squad without hand-written migration notes.**

## What
- **Effective settings, per key:**
  - scalars: the local file wins;
  - `permissions.allow` and `permissions.deny`: union, order kept, duplicates dropped;
  - objects: recursive merge.
- The result is written to `<home>/roles/<agent>.settings.json` and passed with `--settings`. The `model` and `effortLevel` defaults and the flags keep ADR 0008 and ADR 0010 behaviour.
- **Old layout:** a squad with a full `settings/<role>.json` and no `.local.json` keeps working, using that file as before, with one stderr warning pointing at 09.
- The placeholder `CODE_PATHS_SET_BY_SQUAD_INIT` in the template is replaced from the local file's `codePaths` list; it is never written into the effective file.

## Technical AC
1. Merge truth table tests: scalar override; allow union; deny union; nested object; the local file missing; the template missing (exit 1).
2. Team Lead effective settings from template + empty local contain `Bash(squad-spawn dev:*)` and the herdr entries. This is the v4 gap in SETTINGS-NOTES.md, closed by construction (test).
3. QA blackbox effective settings deny the local `codePaths` (test).
4. The old-layout squad gives the same `--settings` argv as before (existing spawn tests pass).
