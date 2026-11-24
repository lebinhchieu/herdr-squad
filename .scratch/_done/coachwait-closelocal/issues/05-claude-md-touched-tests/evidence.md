## Behaviour

One bullet added to CLAUDE.md > Running tests (after first bullet). Tests reading CLAUDE.md pass: test_suite_rules_process (11 OK), test_ca_launchers (62 OK, 1 skipped), test_run_suite (12 OK).

```diff
CLAUDE.md | 1 +
 1 file changed, 1 insertion(+)

--- Changes ---

CLAUDE.md
  @@ -44,6 +44,7 @@ Single-context: one `CONTEXT.md` and `docs/adr/` at the repo root.
  +- A Developer whose diff touches `templates/` or text a `bin/` tool prints must, before HANDIN, run `grep -rl '<touched path or changed string>' tests/` and run every hit (goldens included), even test files it did not edit.
   - Runner: `python3 tests/run_suite.py --receipt <dir> --if-changed <task base>`. Integration and promotion tasks and the sha the PO merges use `--tz` instead: nothing skipped.
   - Start it in the background and wait as in `process.md` → Safety → Suites. Never `pgrep -f` or `pkill -f run_suite`: it kills other agents' runs.
   - Commit every fix before a run; never kill and restart one.
  +1 -0
```
