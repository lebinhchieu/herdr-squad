# Evidence 01: board shows every ticket

## Behaviour

`squadtickets.scope_tasks` now merges tickets by number from main's `.scratch/<folder>/issues/`, the scope's unmerged Dev branches (read with `for-each-ref`, `merge-base`, `ls-tree`, `show` only, 2 s budget (below the reader's 3 s)) and drafts `tasks/NN-ticket.md`. Each row gets `origin` (main|branch|draft), `origin_ref`, `on_main`; the Tasks panel shows a tag in the Task cell (`main` grey, `branch -NN` amber, `draft` amber dashed).

Run with `SQUAD_*` unset, `PYTHONDONTWRITEBYTECODE=1`, from `tests/`: `python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadboard_list test_squadboard_git test_squadboard_files test_squad_review_pack test_squadtask test_squadreport_tasks test_squad_report_cli test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions test_squadboard_panels` -> Ran 353 tests, OK (includes the SQ-10 trio).

Tests added: `test_squadtickets.TicketMerge` (real `git init` repo: AC1, AC2 and pick order, equal-to-main and merged branch, no git / spent budget, 40-hex refusal, cache, AC3 report=picker=panel, git=False grep) and `test_squadboard_panels.Panels30.test_T01_tasks_source_tag...` (tag DOM, textContent only, no tag without origin).

Deviations from the design notes (sent to the Tech Lead):
- A branch copy counts only if the branch changed that ticket since its merge-base with main. Otherwise a branch cut from an older main shows main's old copy of every other ticket as "newer". The "not merged into main" rule falls out of the same check (a merged branch changes nothing).
- Two `for-each-ref` reads (squad branches + main) are one call, shared 2 s by every scope of the squad, so a picker of 30 scopes asks once. The picker's git-call bound in `test_squadboard_list` went from 2 to 3 (not in the Files line); `test_squadboard_tasks` T26 now counts only `merge-base`/`diff` calls as the evidence check.
- A draft alone does not make a folder: the old `tasks/issues` scope source still reads it.
