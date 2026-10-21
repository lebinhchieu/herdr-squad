Status: ready-for-agent
Type: task
Task ID: 05
Touches: `bin/squad-spawn`, `bin/squad-respawn`, `bin/squad-start`, `tests/test_squad_spawn.py`, `tests/test_squad_respawn.py`, `tests/test_squad_start.py`
Does not touch: `agents/*` (06), settings merging (08), `bin/squadcompose.py` beyond calling it
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_spawn test_squad_respawn test_squad_start test_windows_safe`
Blocked by: 01, 04

# 05: Spawn and respawn attach the composed rules; scopes run on a pinned plugin

**Done when a spawn in a composed-mode squad writes `roles/<agent>.rules.md`, passes it with `--append-system-prompt-file`, and runs on the scope's pinned runtime as ticket 01 recommends.**

## What
- **Composed mode:** the squad folder has `process.local.md`, or has no `process.md`. Otherwise every command keeps today's behaviour (spec → Rollback).
- **`squad-start`:**
  - writes `plugin: <version> <sha>` into the new `scope.md`, from `$SQUAD_DIR/plugin.pin`, else the running plugin's version and `git rev-parse HEAD`;
  - materialises the runtime as 01 recommends;
  - warns, never stops, when `plugin.pin` is older than the installed plugin.
- **`squad-spawn`:**
  - composes for the agent's role and home, writes `roles/<agent>.rules.md` and passes `--append-system-prompt-file`;
  - uses the pinned runtime with the flags and `PATH` from 01;
  - refuses with a fix-it message when the pinned runtime is missing;
  - writes a first prompt that no longer says "read process.md".
- **`squad-respawn`:** recomposes, because the size may have changed, and its RESPAWN prompt points at the notes only.

## Technical AC
1. Stub `claude` (the existing spawn test pattern): the argv has `--append-system-prompt-file <home>/roles/<agent>.rules.md` and the pinned plugin flags; the file exists and starts with `# Your process rules`.
2. A non-composed squad (today's layout) gives the same argv as before: the existing tests pass unchanged.
3. Respawn after a fixture `size: S` → `size: M` edit produces a rules file with the M variants.
4. A missing runtime gives exit 1 and a message naming the pin and how to restore it. An unparseable pin gives exit 2.
5. A live probe, recorded in the evidence, uses a temp composed squad and Haiku: a spawned `dev` answers YES to a marker phrase placed in its composed rules, and YES to a phrase only the pinned card has.
