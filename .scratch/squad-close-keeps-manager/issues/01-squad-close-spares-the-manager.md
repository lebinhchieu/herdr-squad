# 01 squad-close spares the Manager
Status: ready-for-agent
Type: task

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; QA whitebox runs the full suite once on the final sha (`python3 tests/run_suite.py --receipt <dir> --if-changed <base>`). Ticket + evidence path: `.scratch/squad-close-keeps-manager/issues/NN-<slug>.md` and `.../NN-<slug>/evidence.md` (commit this task file there as the ticket). Design: `.scratch/squad-close-keeps-manager/grill.md`; decisions in `$SCOPE_DIR/iterations/1.md`.

Touched files: `bin/squad-close`, `tests/test_squad_close.py` (and `bin/squad-process` only if prune needs a way to keep one pin; prefer `--protect`).

## Business AC (from the PO's grill)
1. `squad-close <squad> --scope S` and `--goal G` do not retire the Manager (no pane close for it); output says it is kept (`kept <mgr> (Manager stays; squad-retire <mgr> ends it)`). Other agents still retire, worktrees/branches/folder move/report/inbox + retro checks unchanged.
2. Whole-squad `squad-close <squad>` still retires every agent including Managers, last.
3. No new flag. `--dry-run` shows the kept line.
4. The folder still moves to `_done`.
5. Prune keeps the closing scope's (goal's) own pinned runtime in scope and goal close, and says so (`kept <pin> (Manager still runs from it)` or similar); the next scope/squad close prunes it as an orphan. Whole-squad close prunes all as today.
6. Header comment in `bin/squad-close` and usage text match.
7. Tests: rewrite `test_prune_runs_after_the_agents_and_before_the_managers_pane_is_closed` (no Manager pane close, runtime kept), the goal-close test (~L271, no longer retires goal Manager), add: squad close still retires Managers; kept pin pruned by a later scope close.

## Design notes / proposed technical AC (dev, for QA whitebox)
Design: `managers` retired only when `mode == squad`; scope/goal print under `== manager`: `kept <mgr> (Manager stays; squad-retire <mgr> ends it)` (dry-run same). Prune in scope/goal mode adds `--protect $squad_dir/_runtime/<ver>-<sha12>` of the closing home's pin (via `squadruntime.home_pin`, no new parser); a line `kept <name> (Manager <mgr> still runs from it; the next scope or squad close prunes it)` precedes prune output; prune's own line reads `kept <name> (running)`. No change to `bin/squad-process`/`squadruntime.py`. Header comment + usage updated.
Proposed technical AC:
T1 scope close (lone task): no `pane close` for the Manager; other agents retired; output has the kept line; exit 0.
T2 goal close: same for goal Manager.
T3 squad close: all Managers still closed, last, after folder move; no kept line; all runtimes pruned.
T4 `--dry-run` prints kept line, no `would retire <mgr>`.
T5 scope/goal close with pin: pin dir survives, "Manager ... still runs from it" printed; a later scope close (other scope) / squad close removes it as orphan. No pin in home → no extra line, prune unchanged.
T6 folder still moves to `_done`; ordering agents < branches < runtimes < folder < manager.
T7 flat/label mode unchanged (no managers there).
T8 existing prune tests still pass (X "removed" assertions adapted: sc1's own pin kept).

## Technical AC (QA whitebox; agree or counter in this file)
T1. Only the per-mode `managers` list changes: `mode=squad` still collects and retires managers last (flat and scoped layouts); `mode=scope`/`goal` collect them into a `kept` list, never call `squad-retire` on them. `label` mode (flat squad) unchanged. No new flag, no new exit code; `--dry-run` prints the same `kept` line and calls nothing.
T2. `== manager` section stays (squad mode: `retired`/`skipped`; scope/goal: one `kept <mgr> (Manager stays; squad-retire <mgr> ends it)` line per manager). A scope inside a goal has no Manager in its roster: no `kept` line, no pin protection.
T3. Pin protection only when a Manager is kept: pass the closing home's pinned runtime (`<squad>/_runtime/<version>-<sha12>` from `home_pin($src)`) to prune as an extra `--protect` (prefer; no change to `squadruntime.prune` semantics). Output says it is kept and why. Pin not present on disk, no pin in scope.md/goal.md, or pin also held by another open scope/goal/plugin.pin: no error, no duplicate/misleading line (shared pin keeps its `held by` line). Squad close: `--all` prunes everything, no extra protect; `--protect "$bin"` unchanged. If `squadruntime.py`/`squad-process` changes, its own tests change too (`tests/test_squadruntime*.py`).
T4. No ordering regression: agents -> branches -> runtimes -> folder -> manager section; prune failure still only warns; `set -euo pipefail` safe (empty arrays under `set -u`: `"${kept[@]}"` on bash 4.3 and older; check with `bash -n` and an empty-array path run).
T5. Header comment L5-21 and any `usage`/help text say the same as the code (scope/goal: Manager kept; squad: all retired, Managers last). No stale "Manager last" for scope/goal.
T6. Tests (`tests/test_squad_close.py`), each fails on the old script and passes on the new (Dev shows red first, receipt in evidence): (a) scope close: no `pane close` for the Manager, no retire, `kept` line, runtime of the scope's pin still on disk, other orphan pruned; (b) goal close (L271): goal Manager not retired, goal pin kept; (c) whole-squad close: every Manager retired last (order in herdr log), all runtimes pruned; (d) a later `--scope` close prunes the previously kept pin (orphan); (e) `--dry-run` shows `kept` and calls no herdr close; (f) scope in a goal (no Manager in roster): own pin pruned as before; (g) squad-retire of a kept Manager afterwards still works (smoke, if cheap). Assert on pane-close/herdr log, filesystem and exact `kept` line, not only on stdout length.
T7. Run: `python3 -m unittest tests.test_squad_close` (plus any squadruntime test touched) green; `bash -n bin/squad-close`; no unrelated diff (`git diff --stat` only the touched files). No new untracked files in the project root.
T8. Real run (REV-5b): one `--dry-run` of the built script in a scratch squad (like the test fixture), pasted into evidence.md: scope, goal, squad modes.
