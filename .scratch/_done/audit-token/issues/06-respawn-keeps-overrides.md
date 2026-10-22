# 06 A respawned agent keeps its `--model` / `--effort` override

Status: done
Blocked by: none
Files: `bin/squad-spawn`, `bin/squad-respawn`, `tests/test_squad_spawn.py`, `tests/test_squad_respawn.py`. Not `bin/squad-usage` (ticket 05).
Parallel with: 05 (disjoint files).

`squad-respawn` starts the new session on the role's default model and effort (its header says so; `tests/test_squad_respawn.py:73` asserts it). A trial role started with `--model sonnet` or `--effort medium` would silently go back to the default after its first respawn, and the trial would measure the wrong thing. Cost rules respawn long-running roles, so this will happen.

## Business AC
An agent started with an override keeps it for its whole scope, however often it is respawned. This includes a Manager the PO starts with `squad-start --model sonnet` (the driver-5 trial) and a Manager started by `squad-start --resume`. Agents started without an override behave exactly as today.

## Technical AC
- **R1 Record.** `squad-start` starts the Manager through `squad-spawn --model/--effort` (bin/squad-start lines 146-149, 225-228), so recording in `squad-spawn` covers it. When `squad-spawn` gets `--model` or `--effort`, it writes them to `$home/roles/<name>.overrides` (`model=<M>` and/or `effort=<E>`, one per line). `home` is computed by the same rule in both scripts, so they agree for every role: `$SCOPE_DIR`, else `$GOAL_DIR`, else `$SQUAD_DIR` as `squad-respawn` does. For a Manager started by `squad-start` (no agent env yet) `squad-spawn` derives the scope or goal folder from its own `--scope` / `--goal` arguments. A Manager's file is in its scope (lone scope) or its goal folder (goal Manager). Without an override no file is written, and a stale file for that name is removed.
- **R2 Replay.** `squad-respawn` reads the file and passes `--model` / `--effort` to `squad-spawn`; with no file its command line is byte-for-byte today's (`--dry-run` shows it). Read the file line by line, split on the first `=`, never `source` or `eval` it. Unknown keys are ignored. **A value must match `^[A-Za-z0-9][A-Za-z0-9._\[\]-]*$`** (a leading alphanumeric: no value can become its own flag, e.g. `--dangerously-skip-permissions`). The same check applies in `squad-spawn` to the CLI `--model` / `--effort`, not only in the replay. A refused value exits with a message **before** `herdr agent rename` or any pane close, in the live run too.
- **R3 Tests (fixtures, fake herdr as the existing tests do):** (a) spawn with `--effort medium` writes the file and a respawn `--dry-run` shows `--effort medium` and the role's default model; (b) spawn with both writes both; (c) spawn with none writes none, and respawn is unchanged (the existing `--model sonnet --effort medium` assertion stays); (d) a second spawn of the same name without overrides removes the file; (e) a bad value is refused; (f) `squad-start --model sonnet` (the `roles/` folder does not exist yet: the write does `mkdir -p`) then a Manager respawn replays `--model sonnet`, for a lone scope, for `--goal`, and in the legacy flat layout (Manager row with empty Owns, as the existing manager respawn test does); (g) a value starting with `-` is refused in `squad-spawn` and in a hand-edited file, and the live respawn does no rename or pane close; (h) both `--dry-run`s leave the file as it was; (i) a failed `herdr agent start` leaves the old file in place.
- **R4 Live check.** `dev-evidence.md` shows, for two cases, a real `--dry-run` pair (no session started) in which the respawn line carries the override: (a) a role spawned with `--effort medium`; (b) a Manager started the way the trial starts it, `squad-start ... --model sonnet --dry-run`, then `squad-respawn <manager> --dry-run`. If `squad-start --dry-run` does not write the file, a test (R3) covers it with a fake herdr.
- **R1b Order and dry run.** The file is written or removed only after `herdr agent start` succeeds (a failed spawn is rolled back by respawn's rename-back; an early delete would lose the override). `squad-spawn --dry-run` and `squad-respawn --dry-run` never write or remove it.
- **R2b Header.** The `squad-respawn` header comment ("the role's default model") is updated: it is false when a file exists.
- **R5 Compatibility.** No change to `roster.md` columns or `roles/*.notes.md`; the `overrides` file is in the agent's own `roles/` folder (process.md: each agent's files live there). No migration: existing agents have no file and keep today's behaviour.
- **R6 Suite** as in ticket 05 U7. **R7** `dev-evidence.md` lists the changed files for the remove-board overlap, as 05 U8.

## Comments

- 2026-10-16 Dev AT-04: merged into the integration branch; passed both QAs.
