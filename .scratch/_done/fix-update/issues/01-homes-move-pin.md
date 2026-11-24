# 01 `squad-process homes`: list the open homes with their pins and move chosen ones to the squad's pin
Duties: Developer builds and writes design notes (this file is the design) and the evidence; technical AC are in this file (Tech Lead, agreed with QA whitebox); business AC = this ticket as written; QA whitebox code check; QA blackbox behaviour check; hand in to both QAs
Files: bin/squadhomes.py (new), bin/squad-process, bin/squadruntime.py, tests/test_squadupgrade.py, README.md
Evidence: .scratch/fix-update/issues/01-homes-move-pin/evidence.md
Status: ready
After: none

Ticket path: `.scratch/fix-update/issues/01-homes-move-pin.md` (the Developer commits this text there on its branch, FILE-11; it also commits `02`, `03`, `04` from `$SCOPE_DIR/tasks/` as their tickets, and `.scratch/fix-update/spec.md` is not needed: the scope brief and `iterations/1.md` are the spec).
Touched files are an estimate (LC-9b); a change re-issues this file. Base: main (5aadae0).
Harness: `tests/squadtest.py` `PluginCopy` (two plugin copies at two versions) + `tests/test_squadupgrade.py` `Base` fixture (a scratch squad with `process.local.md`, `plugin.pin`, `_runtime/`). No herdr here (respawn is ticket 02).

## Problem
`squad-process upgrade --apply --yes` moves the squad's overlay and `plugin.pin`; every open home (`scopes/*/scope.md`, `goals/*/goal.md`) keeps its own `plugin:` line and stays on the old runtime ([ADR 0016]). Chieu works in one home and wants to be offered its move. There is no tool that lists a home's pin or moves it.

## Verified facts (Tech Lead, 2026-11-21; read these before coding)
- Compose of an old-pinned home against the squad's already-upgraded `process.local.md` fails whenever an overlay `replace`/`remove` op was re-hashed (`keep`, `file:`, retarget) or retargeted to a new ID: `squad-process compose ... --plugin-root <old runtime>` exits 2 with `CORE-4: overlay written for @deadbeef, plugin now @220ee2af` or `NEW-99: replace of an ID the plugin does not have` (reproduced in a scratch squad against `_runtime/0.10.0-432b8ea8144f`). `add` ops never go stale (this squad's overlay is 20 `add` ops, so nothing breaks today). Spawn and respawn of every old-pinned home then refuse (exit 2). So the move is close to required after such an upgrade; this ticket's `check` shows it.
- `read_home` (`bin/squadcompose.py:117`) reads the pin from `goal.md` for a goal home and from `scope.md` only for a scope home. A scope inside a goal has its own `plugin:` line (`squad-start` writes it, `add_pin_line`, bin/squad-start:314); there is no fallback to `goal.md`. The move edits each home's own file.
- A goal's open scopes = `scopes/*/scope.md` (not `_done`) with a `goal: <name>` line, found the way `bin/squad-close:85` does. `_holders()` in `bin/squadruntime.py` only returns labels; extract the glob into `iter_homes(squad)` -> (kind, name, path) and let `_holders` use it (same results; its tests stay green).
- The target pin is the squad's `plugin.pin` (written by `upgrade --apply --yes`), never "the running plugin": from a pinned runtime `running_pin` exits 2 (`cannot pin the running plugin`). So this tool runs from any plugin version that has it, and moves a home only to a pin the squad already adopted.

## Design
`squad-process homes --check | --apply [--yes] [--only NAME ...] --squad-dir D [--home H]` in the new `bin/squadhomes.py`; `bin/squad-process` dispatches `homes` to it (like `upgrade`). `H` defaults to `$SCOPE_DIR`, else `$GOAL_DIR`; neither: exit 2 `no home: run inside a scope or goal session or pass --home`.
1. **List.** Offered homes = `H`, plus, when `H` is a goal home (has `goal.md`), its open scopes. Per home: kind, name, path, pin now, target = `plugin.pin`, state `at-target` | `moves` | `no-pin` (no `plugin:` line in its file: listed, never touched) | `old-format` (`read_home` refuses it: listed with its error, never touched). A goal home and a scope home are moved independently.
2. **Target runtime.** Build it with `rt.materialise(squad, *target)` (a cache under `_runtime/`; `--check` may create it, nothing else is written). Materialise failure (exit 1 text) -> exit 2 with the message, nothing written.
3. **Compose gate.** For each offered home in state `moves`, for each role of the home (`manager` for a goal home or a lone scope; `team-lead`, `dev` and every token `squad-process team --home H` prints), run `<target runtime>/bin/squad-process compose <role> --home <home> --squad-dir D --plugin-root <target runtime>` (stdout discarded, nothing written; `sys.executable` + script path, never a shebang: ADR 0011). That is the engine and rule set a spawn at the new pin will use. Any non-zero exit: the home is `refused`, its first output line shown. With `--apply`, one refused home among the chosen ones exits 2 and writes nothing for any home (the PO deselects it with `--only`).
4. **Stranded warning (read-only).** `check` also composes the `manager` role of every other open home of the squad (`iter_homes`, not offered) at its own pin with the current overlay, and prints `will refuse spawn and respawn: <kind> <name>: <first error line>` for each that fails. A warning only; never an offer (Q1 (a)).
5. **Apply.** Without `--yes`: print the table and `NOT APPLIED (add --yes after Chieu confirms)`, exit 3, nothing written. With `--yes`: write the first `plugin:` line of each chosen home's file to `<version> <sha>` (value only; the rest of the file byte-identical, LF or CRLF kept, atomic temp file + `os.replace`); then one row per home in `process-log.md` (`| date | Home <kind> <name> plugin <old> -> <new> | squad-process homes --apply |`, via the same insert helper the upgrade uses) so the rollback is one edit. `plugin.pin` and `process.local.md` are not touched. Nothing is pruned (the old runtime is released at the next close). Exit 0; `homes` with nothing in state `moves`: print `nothing to move` and exit 0 (also under `--apply`, no log row).
6. Output ends with one line per moved home: `moved <kind> <name>: <old> -> <new>`. Ticket 02 adds the respawn stage after it.

## AC
- AC1 `homes --check` lists, for a lone scope, its one home; for a goal home, the goal plus every open scope with `goal: <name>` and no scope of another goal or `_done`; each row shows kind, name, pin now, target, state. Exit 0 when no row is `moves`, 3 when one is, 2 when refused. Read-only except the `_runtime/<target>` cache.
- AC2 Target = `plugin.pin`; a squad without one, or an unparseable one, exits 2 and names the file.
- AC3 A scope whose `scope.md` has no `plugin:` line is `no-pin`; an old-format (`size:`) home is `old-format`; neither is ever written, in `check` or `apply`.
- AC4 Compose gate: with the squad's overlay holding a `replace` op whose hash matches the target plugin but not the home's old plugin, `check` shows the home as `moves` (it composes at the target) AND shows the stranded warning for an un-offered open home pinned at the old plugin. With an overlay that fails at the target (an op on an ID the target plugin lacks), the offered home is `refused`, `--apply --yes` exits 2 and no file changed (cmp before/after, including `process-log.md`).
- AC5 `--apply` without `--yes` exits 3, prints `NOT APPLIED`, writes nothing; `--apply --yes` rewrites only the `plugin:` line of each chosen home (a diff of the file shows one changed line; a CRLF file stays CRLF; a goal home edits `goal.md`, a scope edits its `scope.md`), adds one log row per home, leaves `plugin.pin` and `process.local.md` unchanged, and a second run prints `nothing to move`.
- AC6 `--only NAME` limits the move to the named offered homes; a name not offered exits 2.
- AC7 Technical: `iter_homes` is the only home glob (`_holders` uses it; `tests/test_squadruntime.py` and `tests/test_squadupgrade.py` pass unchanged); stdlib only; no `bash`/`tar`/`grep` calls (native Windows, ADR 0011); `bin/squad-process` docstring and `README.md:57` list `homes`; every refusal is exit 2 with the reason on stderr.
- AC8 [SQ-10] The diff edits `bin/` and printed text, so `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` are run and their result quoted in `## Behaviour`. Also run `grep -rl 'squadruntime\|_holders\|squad-process' tests/` hits that the diff can reach.
- AC10 `evidence.md` `## Behaviour` holds a command-only recipe (shell commands, no code) that QA blackbox runs in a scratch squad: two plugin copies at two versions (`PluginCopy`, or `git archive` of two shas into `_runtime/`), a `process.local.md` with a `replace` op hashed for the new plugin only, a lone scope and a goal with two scopes, each pinned old; then `homes --check`, `--apply`, `--apply --yes`, and the refused case. The recipe states the expected exit code and the key output line per command.
- AC9 Tests (one per risk, extend `tests/test_squadupgrade.py`): list for lone scope vs goal; compose-gate refusal writes nothing; CRLF + one-line diff; `--only`. No matrix.

## Not in this ticket
Respawn of live agents (02). The skill dialog (03). Pruning. A home outside Q1 (a) is never offered, only warned about.

## SQ-1 (deletes and moves)
Deletes or moves no file. Readers of `_holders` (`bin/squadruntime.py:prune`) keep their behaviour. Nothing else reads the new module.

## Comments
