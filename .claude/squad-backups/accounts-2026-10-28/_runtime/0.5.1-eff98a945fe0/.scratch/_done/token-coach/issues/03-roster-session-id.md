# 03 Session id in roster.md

Status: resolved
Blocked by: none

`squad-spawn` creates a uuid, passes it with `--session-id`, and writes it into a new `roster.md` column. Check first that the flag exists.

## AC
- After a spawn, `roster.md` has the session id, and it matches the transcript file name.

## Comments

- Checked first: `claude --session-id <uuid>` exists. Confirmed with a real `claude -p --model haiku --session-id X` run: the transcript landed at `<config dir>/projects/<cwd-slug>/X.jsonl`.
- `bin/squad-spawn` now makes a uuid (python3), passes `--session-id`, and after the agent is ready writes it to `roster.md` via `squad-usage --set-session` (before the first prompt). The JSON it prints also has `session`. `--dry-run` shows the id and the planned roster write.
- `templates/squad/roster.md` gets a `Session` column. `--set-session` adds the column to older rosters and appends a row if the agent has none (role/scope filled from the spawn args; the Manager may still refine "Owns").
- Files: `bin/squad-spawn`, `templates/squad/roster.md`, `tests/test_squad_spawn.py` (uses a stub `herdr` on PATH).
- Test: `python3 -B -m unittest tests.test_squad_spawn` → 4 tests OK (roster id equals the `--session-id` passed).
- Assumption: the row's Role cell is the role slug (`dev`), not the capitalised name used in the template's manager row.
