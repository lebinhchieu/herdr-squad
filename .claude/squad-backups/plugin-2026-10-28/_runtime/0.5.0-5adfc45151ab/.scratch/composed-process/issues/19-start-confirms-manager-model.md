Status: ready-for-agent
Type: task
Task ID: 19
Touches: `skills/squad-start/SKILL.md`, `bin/squad-start` (`--dry-run` output adds the Manager's default model and effort), `tests/test_squad_start.py`
Does not touch: `bin/squad-spawn`, `agents/*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_start test_windows_safe`
Blocked by: none

# 19: `squad-start` confirms the Manager's model and effort before spawning

**Done when `/squad:squad-start` shows the PO the Manager's model and effort and lets them keep or change both before the Manager starts. Resuming does the same.**

## What
- **`squad-start --dry-run`** also prints the Manager's default model and effort and where each came from (squad settings, else template). With `--model` or `--effort` it prints those instead.
- **Skill step:** before the real run, ask the PO in one question with these options:
  - keep (default shown, e.g. `sonnet / high`);
  - change model (`opus`, `sonnet`, `haiku`);
  - change effort (`low` … `max`).

  Pass the answer as `--model` / `--effort`. With `--resume`, ask the same before running it.
- The choice is recorded the way ADR 0008 already records it (the Manager's `.overrides`), so a respawn keeps it.

## Technical AC
1. Dry-run output includes model, effort and their sources, for the template default, a squad settings value, and flags (tests).
2. The skill text has the confirm step before the run, for both start and `--resume` (test greps the skill).
3. No Manager is spawned by `--dry-run` (existing test).
