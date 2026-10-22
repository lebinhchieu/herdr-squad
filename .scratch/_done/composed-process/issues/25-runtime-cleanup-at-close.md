Status: ready-for-agent
Type: task
Task ID: 25
Touches: `bin/squadruntime.py` (`prune`), `bin/squad-process` (new `prune` subcommand and its usage line), `bin/squad-close` (call it), `templates/squad/process/closing.md` (CLOSE-2, CLOSE-5), `skills/squad-init/SKILL.md` (gitignore line `*/_runtime/`), `tests/test_squadruntime.py`, `tests/test_squad_close.py`, `tests/test_squadprocess.py` (CLI), `tests/test_instructions.py` only if it pins the CLOSE texts
Ticket file: lives in `$SCOPE_DIR/tasks/`; the Developer's first commit copies it to `.scratch/composed-process/issues/25-runtime-cleanup-at-close.md`.
Does not touch: `bin/squad-spawn`, `bin/squad-respawn`, `bin/squad-start` (they only materialise), `bin/squad-usage*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadruntime test_squad_close test_squadprocess test_instructions test_windows_safe`; `python3 bin/squad-process lint`
Blocked by: 13 (13 and 10 also edit `bin/squad-close` and `tests/test_squad_close.py`; branch from the merged 10+13)

# 25: `squad-close` removes the runtimes nobody pins any more

**Done when closing a scope, a goal or the squad deletes every `$SQUAD_DIR/_runtime/<version>-<sha12>/` that no open scope, no open goal and no `plugin.pin` names, never the one the running `squad-close` itself runs from, and lists what it freed.**

## Why
Scope A materialises a pinned runtime per pin (`git archive`, about 4.6 MB each) and shares it per pin. Nothing deletes it. Decision (goal, scope A): code finds pins only via `scopes/*`, `goals/*`, `plugin.pin`, never by recursive glob of the squad folder. Open item from scope B's summary.

## What
- **`squadruntime.prune(squad_dir, home, dry_run, protect=())`** and CLI `squad-process prune --squad-dir D --home H [--dry-run] [--protect PATH ...]` / `squad-process prune --squad-dir D --all [--dry-run] [--protect PATH ...]` (BA ruling, `business-ac.md` last sections):
  - **candidates** (BA revision 2026-10-22) = every child of `_runtime/` whose name matches `^<version>-<12 hex>$`, orphans included (an `update --apply` leaves one behind and only this cleanup frees it); a non-matching name (`notes/`, `.tmp-*`) is kept and printed `kept (not a runtime)`;
  - **holders** = pins (`plugin: <version> <sha>` via the existing pin readers) of `scopes/*/scope.md` and `goals/*/goal.md` (the `_done` folders are not matched) **excluding `H` itself** (its folder has not moved yet), plus `plugin.pin`, plus every `--protect` path; a candidate with a holder is kept and the line names the holder (`kept X (held by scope s2)`); a scope closing inside a goal keeps its runtime while `goal.md` pins the same one;
  - `--all` (whole-squad close, nothing remains afterwards): every matching child except `--protect`, holders ignored, then `_runtime/` if empty;
  - a child that is a symlink is unlinked, never followed; a child whose realpath is not directly under `_runtime/` is refused;
  - prints one line per folder (`removed <name> (<MB>)`, `kept <name> (pinned by <home>)`, `kept <name> (running)`) and a total; exit 0 even when a delete fails (prints `could not remove`), so a close never stops on it.
- **`squad-close` order:** retire the agents → branches/worktrees → **prune** → move the folder → retire the Manager last (the Manager's `squad-close` runs inside its own pane, which `retire` closes: prune must precede it). Scope/goal close: `prune --home <src>`; whole-squad close: `prune --all`, so `_done/<squad>/` carries none. Always `--protect <the runtime holding this script, if any>` (`$0` resolves into `<squad>/_runtime/…`; deleting it works on Linux and fails on Windows); that runtime is printed `kept (running)` and, in a whole-squad close, goes into `_done/` with the squad. `--dry-run` passes `--dry-run`. A prune failure only warns and the close completes. A squad with no `_runtime/` prints nothing new.
- **Rules:** CLOSE-2 and CLOSE-5 say it (one sentence each). **squad-init** SKILL gitignore list gains `*/_runtime/` (a runtime is rebuilt from the pin, never committed).
- Recovery: a removed runtime is rebuilt on the next spawn from the pin (`git archive`), so a wrong delete costs a rebuild, not data.

## Technical AC
1. Decision table on a fixture squad: closing scope S pins X and another open scope pins Y → X removed, Y stays; two open scopes pin the same X, one closes → X stays and the output names the holder; `plugin.pin` names X → kept; `goal.md` pins X and the closing scope also pins X → kept until the goal closes, then removed; S's own pin is not a holder even though `scopes/S` has not moved yet; the runtime holding the running script (`--protect`) → `kept (running)`; an orphan runtime (nothing names it) → removed and listed; a stray `notes/` and a `.tmp-1-abc` child → kept, never an error; a legacy squad with no `_runtime/` → output unchanged.
2. `squad-close --scope S --dry-run` removes nothing and prints `would remove` lines; the real run prints each removed runtime (name, size) and the freed total.
3. `squad-close <squad>` (whole squad): prune ran before the archive; `_done/<squad>/_runtime` holds at most the running runtime; other output unchanged.
4. A symlinked child is unlinked and its target survives; a child resolving outside `_runtime/` is refused (test with a symlink to a temp dir).
5. A read-only file inside a runtime (git archive keeps modes) does not make prune fail on Linux; the Windows path uses `shutil.rmtree` with an `onerror` that clears the read-only bit (test the handler by unit).
6. No recursive glob of the squad folder: the code lists `scopes/*`, `goals/*` and `_runtime/*` only (a test with a decoy `scopes/s1/evidence/x/plugin.pin` proves it is not read).
7. A removal that fails (a stubbed delete error, and a read-only dir) prints `could not remove <name>` and the close still completes (exit 0); `--dry-run` removes nothing. After prune the next `squad-process runtime --home <open scope>` still prints a path and re-materialises a removed runtime.
8. `squad-process lint` passes; all opens use `encoding="utf-8"`, `newline="\n"`.
