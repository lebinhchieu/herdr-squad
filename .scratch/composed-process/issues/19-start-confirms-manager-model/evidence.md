# Evidence: 19 start confirms the Manager's model and effort

**`squad-start --dry-run` (new scope, goal, `--resume`) prints the Manager's model and effort with their source, resolved as `squad-spawn` does; the skill's step 5a asks keep / change model / change effort before the run, for start and resume; a plain resume keeps the recorded override.**

Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_start test_windows_safe` (59 OK). sha: see the HANDIN.

## Behaviour

Real runs in a scratch squad (no herdr call, no folder created by any `--dry-run`):

- **19.1 template, flags** (Tech AC1, "model only shows mixed sources"):
  - `squad-start x --name one --touches z --dry-run` → `manager model: sonnet (from template)` / `manager effort: high (from template)`
  - `… --model opus` → `opus (from flag)` / `high (from template)`
  - `… --model opus --effort low` → `opus (from flag)` / `low (from flag)`
- **19.1 squad settings, as `squad-spawn` reads them** (QAw finding 1): `settings/manager.json` = haiku/low and `settings/manager.local.json` = `{"model":"opus"}` → `opus (from squad settings)` / `high (from template)`: the overlay wins and the full file is ignored, as in `squad-spawn`. Test `test_dry_run_resolves_like_squad_spawn…` also covers the full file alone, and a composed squad whose pinned runtime's template differs from the plugin's (the pinned one is shown).
- **A6 resume, recorded override** (`roles/<mgr>.overrides` = opus/low): `squad-start --resume r --dry-run` → `opus (from recorded override)` / `low (from recorded override)`; with `--effort max` → effort `max (from flag)`. A plain `--resume` (no flags) passes `--model opus --effort low` to `squad-spawn` and the `.overrides` file stays (test).
- **19.3 dry-run spawns nothing**: `scopes/` unchanged, herdr log empty (tests `dry_lines`, `test_dry_run_creates_nothing`).
- **19.2 skill**: `skills/squad-start/SKILL.md` step 5a sits before step 6 "Run:", says "also before `--resume`", lists keep / change model (`opus`, `sonnet`, `haiku`) / change effort (`low` … `max`), and step 3 sends a resume through it (test greps it).
