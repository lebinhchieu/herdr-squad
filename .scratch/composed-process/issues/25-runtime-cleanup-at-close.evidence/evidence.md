# Evidence 25: squad-close removes the runtimes nobody pins any more

Branch `squad/plugin/process-fixes/plugin-dev-pf-7`, base afdc264, code 9905c0c. Old-form folder (ticket 21 is not in this branch; moved at integration). Draft commit 96d9104 copied tickets 25 and 26 to `.scratch/composed-process/issues/`.

## Technical AC
1. **Decision table** (`tests/test_squadruntime.py::PruneTest`): X of the closing scope removed, Y of another open scope kept; two scopes on one X: kept and `(held by scope s2)`, removed once the holder is gone; `plugin.pin` and `goal.md` pins hold (`held by plugin.pin`, `held by goal g1`), the closing home's own pin does not; `--protect` path inside a runtime: `kept … (running)`; orphan removed; `notes/`, `.tmp-1-abc`, `1.0-short`: `kept … (not a runtime)`; no `_runtime/`: prints nothing.
2. **Dry run / output** (`test_squad_close.py::RuntimePruneCloseTest`): `--dry-run` prints `would remove … (1.0 MB)` and `would free 2.0 MB in 2 runtimes`, removes nothing; the real run prints `removed <name> (1.0 MB)` per runtime and `freed … MB in N runtimes`.
3. **Whole squad**: `prune --all` runs before the archive; `_done/t/_runtime` is absent (or holds only the running runtime, tested from inside a copied runtime).
4. **Symlinks**: a symlink child is unlinked, target survives (`removed … (link only, target kept)`). A non-link child whose realpath is not directly under `_runtime/` prints `refused` and stays (unit-tested through `_under`, patched; there is no portable way to build one on Linux). Decision: a symlink is never refused, only unlinked; QA: say if a symlink to a temp dir should be refused instead.
5. **Read-only**: a 0444 file inside a runtime deletes fine on Linux; the `onerror`/`onexc` handler `_clear_readonly` clears the bit and retries (unit test).
6. **No recursive glob**: decoy `scopes/s2/evidence/x/{plugin.pin,scope.md}` and `scopes/_done/old/scope.md` are never read (test); a source check forbids `**`/`rglob` in `_holders`.
7. **Failures**: patched `_rmtree` error and a read-only `_runtime/` print `could not remove <name> (…)`, exit 0, close completes; a broken `squad-process prune` (exit 7) only warns `runtime cleanup failed (exit 7)`; an unreadable holder pin removes nothing (`no runtime removed`). After a prune, `squad-process runtime` re-materialises the runtime (test builds, prunes, rebuilds).
8. `squad-process lint` rc 0; all opens `encoding="utf-8"`, `newline="\n"`.

## Decision (TL, option b + a)
Prune runs with `--protect <dir of the running script>`: `kept (running)`; the next close sweeps it once the Manager runs from another runtime. Tests: `$0` inside the candidate is kept (scope and whole-squad close); in the herdr stub log, the Developer pane closes with the runtime still present and the Manager pane closes after it is gone (prune before the Manager's `retire`).
**Accepted leak:** a lone scope close whose Manager runs from its own pin keeps that runtime until a later close (or the final whole-squad close, which archives it into `_done/`).

## Behaviour
**How to see which runtime `squad-close` runs from:** `squad-close` resolves `$0` with `readlink -f`; the runtime is the `_runtime/<version>-<sha12>/` in that path (`readlink -f $(command -v squad-close)`, or the path you typed). In a scratch squad: build the runtime with `squad-process runtime --squad-dir D --home D/scopes/run` (scope pinned to this branch's sha), put a fake `herdr` on `PATH` with `HERDR_ENV=1`, and call `D/_runtime/<name>/bin/squad-close t --scope run`. Calling `<plugin checkout>/bin/squad-close` runs from the checkout instead (nothing is protected). Ran with a stray orphan `0.4.1-cccccccccccc` and a `notes/` child; scope `other` pins another sha:
```
$ readlink -f $RT/bin/squad-close
<scratch>/.claude/squads/t/_runtime/0.4.1-9905c0c3d379/bin/squad-close
$ $RT/bin/squad-close t --scope run --dry-run
== runtimes
kept 0.4.1-9905c0c3d379 (running)
would remove 0.4.1-cccccccccccc (0.0 MB)
kept notes (not a runtime)
would free 0.0 MB in 1 runtime
== folder
$ $RT/bin/squad-close t --scope run
== runtimes
kept 0.4.1-9905c0c3d379 (running)
removed 0.4.1-cccccccccccc (0.0 MB)
kept notes (not a runtime)
freed 0.0 MB in 1 runtime
== folder
archived to <scratch>/.claude/squads/t/scopes/_done/run
== manager
$ ls _runtime
0.4.1-9905c0c3d379/
notes/
$ <plugin checkout>/bin/squad-close t --scope other
== runtimes
removed 0.4.1-9905c0c3d379 (4.1 MB)
kept notes (not a runtime)
freed 4.1 MB in 1 runtime
== folder
$ ls _runtime
notes/
```
Read: from the pinned runtime the running one is `kept (running)`, the orphan goes, `notes` stays; a later close from the checkout sweeps the former running runtime (4.1 MB; a full runtime is about 4 MB). Exit 0 throughout; `ls _runtime` shows the result.

## Developer-rules byte delta
Composed `dev` (M, design no, goal no): 4901 B before and after, **+0 B** (CLOSE-2 and CLOSE-5 are `roles: manager`; limit 5120).

## Commands
`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadruntime test_squad_close test_squadprocess test_instructions test_windows_safe test_dev_rules_size test_suite_rules_process` → 213 OK. `python3 bin/squad-process lint` rc 0.
