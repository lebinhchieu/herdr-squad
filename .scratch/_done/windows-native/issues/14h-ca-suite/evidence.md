# Evidence: 14h run_suite path map (mapping only)

## Behaviour

**Status: UNRUN.** A PO order forbids every test run. All checks below are static (read, `git diff`, `grep`, a no-write parse). Code sha: `c93445c` (base `73dba68`). Only `tests/run_suite.py` changed.

Scope of this hand-in: only the path-map part of 14h. The `test_ca_autoswitch` sleep-to-wait part is **held** and not touched (it needs a run).

| AC | Result |
|---|---|
| Static: the `run_suite.py` diff is a mapping and nothing else | `git diff 73dba68..c93445c --stat`: 1 file, `tests/run_suite.py`. Added: constants `CA_PREFIX`, `CA_WATCH`; a `skip_ca` filter in `execute()` (default `False`); in `main()` the `skip_ca` decision inside the `--if-changed` branch; one note line. No other logic changed. |
| Change outside `tools/claude-accounts` and `ca_*` does not schedule the `ca` files | With `--if-changed BASE`, `skip_ca = bool(ca_tests) and not touches(changed, ca_tests, CA_WATCH)`. `ca_tests` = every `tests/test_ca_*.py`. `CA_WATCH` = `tools/claude-accounts/`, `tests/ca_stubs.py`, `tests/ca_win_cases.ps1`, `tests/fixtures/ca/`, `tests/winlaunch.py`, `bin/squadio.py`, `tests/run_suite.py`. A squad-only diff (e.g. `.claude/squads/...`, `.scratch/...`) matches none, so `test_ca_*` are dropped from the pool and the receipt says `skipped claude-accounts files (test_ca_*): ...`. |
| `--tz` keeps everything | `skip_ca` is set only in the `--if-changed` branch, and `--if-changed` excludes `--tz` (argparse check, unchanged). So `--tz` and a plain run keep `skip_ca=False`. |
| Linux behaviour unchanged | A run without `--if-changed` never sets `skip_ca`. `execute()` has the new parameter with default `False`. If `git diff` fails (`changed is None`) nothing is skipped, as for the browser skip. |
| Zero new skips | `git diff 73dba68..c93445c \| grep -E "unittest.skip\|skipIf\|skipUnless\|@skip"` adds nothing. (`skip_ca` is a variable name, not a test skip.) |
| `def test_` counts | No test file touched. |
| Syntax | `ast.parse` of `tests/run_suite.py`: ok (no `.pyc` written, nothing run). |
| Existing `test_run_suite` | Read, not run. `IfChangedTest` uses a repo with no `test_ca_*` file, so `skip_ca` is `False` and no new line is printed. Its asserted lines are unchanged. |
| Run AC | **Unrun** (PO order). Still to do after the freeze: `run_suite.py --if-changed <squad-only sha>` must not list the `ca` files; `--tz` must list them. |

Why the watch list is wider than "`tools/claude-accounts` and `ca_*`": `ca_stubs.py` imports `winlaunch`, `winlaunch` imports `bin/squadio.py`, and `test_ca_win` loads `tests/fixtures/ca`. A change in those can break a `ca` file, so it must schedule them. Edit the tuple if the Team Lead wants the narrow rule.

## Review

Fresh-context review (sonnet, high, read-only, no run) of `73dba68..19589c0`.
- Finding: `bin/squadio.py` missing from `CA_WATCH` (`winlaunch` imports it). Fixed in `c93445c`.
- Optional, not done: a root `.gitignore` edit is not watched (`test_ca_install` runs `git check-ignore`); the folder's own `.gitignore` is covered.
- Checked, no defect: path format of `git diff --name-only` against `CA_WATCH`; `changed is None`; no `test_ca_*` in the dir; `--tz` and plain runs; `test_run_suite` assertions; nothing beyond a mapping.
