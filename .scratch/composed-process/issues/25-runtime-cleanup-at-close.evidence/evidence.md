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

## QA whitebox review

### QA whitebox 25 (runtime cleanup at close): PASS @ 8a4ab9e (code 9905c0c, 8a4ab9e adds evidence only)

Ran (detached worktree): `test_squadruntime test_squad_close test_squadprocess test_instructions test_windows_safe` = 198 OK; `squad-process lint` clean. Reviewed afdc264..9905c0c: `prune` in `bin/squadruntime.py`, `bin/squad-close` call, `bin/squad-process` dispatch+usage, CLOSE-2/CLOSE-5, squad-init gitignore line.

#### AC check
1. Decision table: holders from `scopes/*`, `goals/*` (marker file required, `_done` skipped), `plugin.pin`; closing home excluded; protect -> `kept (running)`; stray/`.tmp-*` kept; no `_runtime/` prints nothing. Tests 668-740.
2. `--dry-run` -> `would remove`/`would free`; real run prints name, MB, total.
3. Whole squad: `--all` before the folder move; test keeps only the running runtime in `_done/<squad>/_runtime`.
4. Symlink child unlinked, target survives (test 757, plus my fixture run: `ln -s tgt _runtime/1.0-c…` -> `removed … (link only, target kept)`, `tgt/keep` intact). Non-symlink child resolving outside: refused (test via mocked `_under`).
5. Read-only file: handler clears bit and retries (unit test 782); my fixture with a 444 dir removed fine as non-root.
6. No recursive glob: decoy `scopes/s1/evidence/x/plugin.pin` not read; code-grep test 840.
7. Failed delete -> `could not remove`, exit 0; failed prune in squad-close warns with the exit code and the close completes (stub `squad-process` exit 7).
8. Lint ok; opens carry encoding.
- **Inside the candidate runtime (decision AC):** `test_runtime_the_script_runs_from_is_kept_and_archived_with_a_whole_squad` copies `bin/` into `_runtime/<Z>/bin` and runs that `squad-close` for a scope close (X freed, Z `kept (running)`, script still there) and a whole-squad close (`_done/t/_runtime` == [Z]). Order vs `retire`: stub-herdr logs `rt=yes/no` per pane close, asserted. Both read and pass.

#### Notes (not blocking)
1. Open point from Dev (symlink to a temp dir): unlink is right, it removes only the link; AC 4 is satisfied by that. The "refused" branch is reachable only when a real directory child resolves elsewhere (bind mount), covered by the mock.
2. Accepted leak per decision (lone scope close from its own pin keeps that runtime until a later close): confirm the evidence states it.
3. Evidence is old-form `25-….evidence/`; integration re-runs `git mv`.

## QA blackbox review

### QA-b 25 (commit 9905c0c, evidence 8a4ab9e, branch squad/plugin/process-fixes/plugin-dev-pf-7)
Method: scratch git project with `.claude/squads/t`, fake runtime folders named `0.4.1-<12 hex>`, plus a real runtime built with `squad-process runtime` and `squad-close` run from it. Real tools, no code read. Scratch dir /tmp/qab25.ia6H left in /tmp (removal blocked by a safety check).

| AC | What I did | Saw | Result |
| --- | --- | --- | --- |
| 1 | s1 pins a, s2 pins b; close s1 | b stays (`kept ... (held by scope s2)`); a kept only because s3 pins it (see 2); orphans c, f `removed` | pass |
| 2 | s1 and s3 both pin a; close s1, then s3 | `kept 0.4.1-aaaaaaaaaaaa (held by scope s3)`; after s3 closes, a `removed` | pass |
| 3 | `plugin.pin` names e | `kept ... (held by plugin.pin)` in every scope/goal close; removed only in whole-squad close | pass |
| 4 | goal g pins X, scope s5 also pins X | close s5: `kept (held by goal g)`; close goal g: X `removed` | pass |
| 5 | orphans c, f; `notes/`, `.tmp-1-abc` | orphans `removed`; `kept notes (not a runtime)`, `kept .tmp-1-abc (not a runtime)`, exit 0 | pass |
| 6 | closing scope's own pin unheld (real runtime of sha 96d9104, scopes q+r) | kept while r holds it; `removed 0.4.1-96d9104fd181 (3.9 MB)` when the last holder closes; next `squad-process runtime --home <scope>` rebuilds it | pass |
| 7 | read-only subdir with file inside a runtime; read-only file; symlink child to an outside dir | `could not remove 0.4.1-333333333333 (Directory not empty)`, exit 0, scope still archived; read-only-file runtime removed; symlink `removed ... (link only, target kept)`, target file survives | pass |
| 8 | legacy squad with no `_runtime/`, my build vs 4901cab baseline, `--dry-run` | outputs identical | pass |
| dry-run | `--scope s1 --dry-run`, whole-squad `--dry-run` | `would remove` lines + `would free`, nothing removed | pass |
| running | `squad-close` called from the built runtime | `kept 0.4.1-9905c0c3d379 (running)`, never removed, also kept in whole-squad close | pass |
| whole squad | `squad-close t` from the runtime | all runtimes removed except the running one and non-runtime children; `_done/t/_runtime` = running runtime, `notes/`, `.tmp-1-abc`; exit 0 | pass |
| rules | CLOSE text mentions `_runtime`; squad-init skill gitignore lists `*/_runtime/` | present | pass |

Note: closing from the plugin checkout (not a runtime) protects nothing, as the Developer's Behaviour says; accepted by the AC (a removed runtime is rebuilt on the next spawn).

Verdict: PASS 25 on 9905c0c.
