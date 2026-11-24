# Evidence: 14a-squadtest 14a squadtest.md helpers

## Behaviour

Code sha: `fefa180` (base `4a8ed47`). Tests only; no change in `bin/ templates/ agents/ skills/ docs/`.

| AC | Result |
|---|---|
| Static 1 | `tests/squadtest.py` defines `ROOT BIN load_cli clean_env fake_herdr squad_home git GIT_ENV plugin_copy plugin_clone` once. `grep -c "FAKE_HERDR\s*=" tests/test_squad_label.py` = 0. |
| Static 2 | `test_squadruntime` `Base.setUpClass` calls `plugin_copy()` (one per process), no `copytree`. `test_squadsettings` and `test_squadscaffold` have no `copytree(ROOT, ...)`; they use `plugin_clone`. |
| Static 3 | `def test_` counts equal in the 4 files (`equivalence.md`). |
| Static 4 | `fake-herdr.md`. |
| Zero new skips | `git diff 4a8ed47 \| grep -c "^+.*skip"` = 0. `test_no_bare_bash` passes (6 tests). |
| Run: windows | `test_squadruntime` 68 tests OK (2 skips, same as base); `test_squadsettings` 24 OK; `test_squadscaffold` 5 OK. |
| Run: wall time | `test_squadruntime`, same machine, one run each: base **222 s**, after **134 s**. |
| Run: label | `test_squad_label` on Windows fails 5 tests **on the base too** (`squad-label` starts `["herdr", ...]` with no extension, so the fake script cannot run natively). Same 5 before and after. On Linux (WSL Debian) all 14 pass. |
| Linux | WSL Debian: `test_squad_label`, `test_squadscaffold` 19 OK; `test_squadsettings` + `test_squadruntime` 92 OK. |

## Fake herdr variants

The 11 copies of the fake `herdr`, and the one script in `tests/squadtest.py` (`fake_herdr(dir, mode)`).

| File | What its own copy did | Behaviour the tests need | In the union |
|---|---|---|---|
| test_squadruntime | log; `agent get`: gone after `agent rename`, found if in LIVE else gone; `tab create` p-new/t-new | LIVE, renamed = gone, tab create | mode `dead` (default) |
| test_squadsettings | no log; `agent get` always gone; any `tab *` prints p1/t1 | agent gone, tab create | mode `dead`; no HERDR_LOG set, so nothing is logged |
| test_squad_label | log; `agent list` from LIVE; `agent get` always found with name and tab_id `tab-<n>`; `tab rename` fails if FAIL_RENAME | list, get, rename | mode `live`; `agent list` and FAIL_RENAME are in the union |
| test_squad_close (14b) | log; found unless in DEAD, pane_id `p-<n>` | DEAD | mode `live` + DEAD; pane_id is `p-<n>` |
| test_squad_respawn (14b) | like runtime, but found unless renamed; pane_id p-old | rename check | mode `live` (rename check is in the union) |
| test_squad_retire (14b) | PANES table: `agent get`, `tab close`, `pane close` | PANES | PANES branch in the union |
| test_team_lead_perms (14b) | PANES table: `agent get`, `pane close` | PANES | PANES branch |
| test_squad_spawn (14b) | LIVE found with tab_id t0, else gone; any `tab *` prints p1/t1 | LIVE, tab create | mode `dead` |
| test_squad_start (14b), test_team_models (14b) | agent gone; any `tab *` prints p1/t1 | agent gone | mode `dead` |
| test_utf8_helpers (14e) | adds `workspace get`, `tab get`, empty `agent list`, emoji label | own cases | not in the union: stays in 14e |
| test_crlf_squad_files (14b) | imports close's copy | as close | as close |

Differences the union settles (a 14b Dev must check these against its asserts):
- `tab create` prints `p-new` / `t-new` (runtime, respawn); spawn, start, models and settings printed `p1` / `t1`. No test in the four 14a files asserts either value.
- `agent get` gives `pane_id` `p-<n>` and `tab_id` `tab-<n>`. Runtime printed `p-old` and spawn printed `t0`. Not asserted in the 14a files.
- The fake writes the log only when `HERDR_LOG` is set (settings' copy never logged).
- It is written with LF only (`newline="\n"`); the old copies used the platform newline.

## Old test to new place

Old test -> where it lives now. No test was merged or removed: `def test_` counts are equal.

| File | `def test_` before | after |
|---|---|---|
| tests/test_squadruntime.py | 68 | 68 |
| tests/test_squadsettings.py | 24 | 24 |
| tests/test_squadscaffold.py | 5 | 5 |
| tests/test_squad_label.py | 14 | 14 |

What moved (set-up only; assertions untouched):
- `make_plugin`, `GIT_ENV`, `git`, `FAKE_HERDR`, `FIX` of test_squadruntime -> `squadtest.plugin_copy/plugin_clone`, `GIT_ENV`, `git`, `fake_herdr`, `FIXTURES`.
- `Base.setUpClass` of test_squadruntime: one `plugin_copy()` per process instead of one `copytree` + `git init` per class. Tests that changed the copy (5 `copytree(self.plugin, ...)`) use `plugin_clone(dest)`; the two "no repo" ones use `plugin_clone(dest, git_dir=False)`.
- test_squadsettings: `FAKE_HERDR`, 2 env scrubs, the plugin copy + version stamp, the `.claude/squads/t` tree -> `fake_herdr`, `clean_env`, `plugin_clone(rt, fixtures=False, git_dir=False)`, `squad_home`.
- test_squadscaffold: env scrub and the plugin copy -> `clean_env`, `plugin_clone(..., git_dir=False)`.
- test_squad_label: `FAKE_HERDR`, env scrub, path constant -> `fake_herdr(fake, "live")`, `clean_env`, `BIN`.
- test_squadruntime `test_scanners_read_fixed_paths_only`: two `SourceFileLoader` blocks -> `load_cli("squad-label")`, `load_cli("squad-start")`.
Helper callers: `clean_env` 4 files, `fake_herdr` 3, `plugin_clone/plugin_copy` 3, `squad_home` 2, `git` 1 (+ 14b), `load_cli` 1 file (2 calls; 14c converts the rest). `squad_home` and `git` get their third caller in 14b.

## Review

Fresh-context review (sonnet, high) of the diff `4a8ed47..3f4a9ea`.
- Finding: unused `import os` in `tests/test_squadscaffold.py`. Fixed in `fefa180`.
- Checked, no defect: union fake herdr vs the old variants for every case the converted tests use; env scrub now also drops `HERDR*` (hermetic); no test writes into the shared `plugin_copy()`; atexit cleanup.
