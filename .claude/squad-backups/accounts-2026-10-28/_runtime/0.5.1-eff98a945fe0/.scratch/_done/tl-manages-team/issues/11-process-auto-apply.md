# T11 · process.md auto-apply at squad-start (and the Manager's notice)
Status: ready-for-agent
Type: task
Blocked by: none
Repo: /home/chieule/workspace/squad
Spec: PO E3/E4 rule 1 · Design: ../design.md decision 20 · Technical AC: AC-12 below (QA-W to confirm)

## Files this task touches (and no others)
`bin/squadprocess.py`, `bin/squad-process`, `bin/squad-start`, `agents/manager.md` (one bullet), `tests/test_squadprocess_auto.py` (new), `tests/test_squad_start.py`. **Not** `bin/squad-spawn`: T12 adds the one call there.

## Do
1. **`squadprocess.auto_apply(squad_dir, plugin_root, source) -> dict`** with `state` one of `current|applied|blocked|skipped`, `message` (one line), `changed` (headings), `kept_local` (headings), `backup`, `conflicts` (headings). Rules exactly as design decision 20: `flock(LOCK_EX)` on a file descriptor of the squad folder, re-plan inside the lock; no `conflict` section means compose with no resolutions then `apply(..., yes=True)` with the compose file in a temp dir outside the squad (removed after); a `conflict` writes nothing; `ProcessError` (ahead, flat layout, unreadable file or template) is `skipped`. Add one `process-log.md` row `auto-applied by <source>: no section conflicted; kept local: <headings|none>` next to the rows `apply` writes (extend `_log_rows` by an optional argument; the manual path keeps its rows byte for byte).
2. **`squad-process auto [--source squad-start|squad-spawn] [--quiet]`**: prints `message`; with `--quiet` prints nothing for `current` and `skipped`; exit 0 always (never blocks the caller). Add to the module docstring and help.
3. **`bin/squad-start`**: replace the `process_update` check by `auto_apply(..., "squad-start")` for every form (new scope, goal, `--resume`); stderr line `process update: <message>` for applied and blocked (blocked keeps today's wording style plus the headings); the returned `process_update` JSON field carries the message as today. A failure inside it prints the existing "not checked" line and continues.
4. **`agents/manager.md`**: one bullet where the Manager's first prompt is described (find the existing `Process update` mention; if the file has none, put it under the scope Manager's start): an `applied` notice means tell the PO in the first message and tell any running role to re-read the changed sections; a `blocked` notice means write it to the PO inbox (question, options: resolve with `/squad:squad-process-update`, or leave; your recommendation) and carry on. Keep the writing rule (`processlint.py` clean on any file you touch, if applicable). No `process.md` template change: no version bump.
5. **Tests.** Against a temp squad built from the real template snapshots (`skills/squad-process-update/history/process-v1..v4.md`): clean squad at v3 gets v4 and a backup and the log rows; squad with a `local` edit in a section the update does not change is applied and the edit survives byte for byte; squad with a edit in a section the update changes is `blocked`, nothing written (file hash unchanged, no backup, no log row), message names the headings; current is `current`; ahead and flat layout are `skipped`; two processes calling `auto` at once on the same squad (use `multiprocessing` or two subprocesses) leave one backup, one set of log rows and a valid file; `squad-process auto --quiet` is silent on current; `squad-start --dry-run`/real run prints the notice and still starts; a broken template prints the "not checked" line and starts.
6. **Run only the test files you touched**; never the full suite. `PYTHONDONTWRITEBYTECODE=1`.

## Technical AC (AC-12)
- AC-12.1 A blocked update changes no file in the squad folder or `squad-backups/` (hash before and after in `dev-evidence.md`).
- AC-12.2 The result of an applied update passes `squad-process check` (current) and the `apply` validation; the manual `compose`/`apply --yes` path still produces the same bytes and log rows as before (existing tests green and unchanged).
- AC-12.3 Concurrency test above passes 20 repeats (whole test, as CLAUDE.md says for flake checks).
- AC-12.4 Applied on the real live squad **copy** (copy `.claude/squads/plugin/process.md` and `process-log.md` to a temp squad, plugin root = this worktree): output and result saved. The live squad itself is not touched.
- AC-12.5 `manager.md` bullet names both notices; `grep` shows the rule once.

## Business AC
PO E4 rule 1: a local edit in a section the update changes: warn, and the Manager puts it in the PO inbox. Nothing extra at `squad-start` beyond the existing warning. Otherwise the update applies by itself.

## Amendments (Tech Lead, 2026-10-17, from QA-W v6)
- **A13 (one path to the Manager, decided):** `squad-start` runs `auto_apply(..., "squad-start")`, prints the stderr line once, and hands the result to the spawn it makes through the environment variable `SQUAD_PROCESS_NOTICE` (value `<message>`; empty for `current`/`skipped`). T12 makes `squad-spawn manager` use that variable when set and run `squad-process auto --source squad-spawn --quiet` itself only when it is unset. So `squad-process auto` prints `applied: <message>` or `blocked: <message>` (state word first, for `current`/`skipped` nothing under `--quiet`); the Manager's rule text is chosen by that first word. Applies to every `squad-start` form including `--resume`. Test: `squad-start` on a v3 temp squad; the fake-herdr Manager prompt contains the applied notice; the PO sees the stderr line once; resume form too. You change `squad-start` only; T12 changes `squad-spawn`.
- **A14** A blocked update leaves no `.lock` file in the squad folder (take the `flock` on a descriptor of the folder itself) and `process-log.md` is unchanged. Hash the folder listing as well as the files.
- **A15** On the real live copy `auto` is expected to say `blocked`, naming the `## Task lifecycle` conflict, and write nothing: save that. Add a second sample: the same copy with that section's local edit reverted to its v3 text gets `applied`, `local` sections byte-identical, and `squad-process check` says current.
- **A10** `bin/squad-process` sets `sys.dont_write_bytecode = True` before importing `squadprocess` if it does not already; no `__pycache__` in `bin/` after your tests.
