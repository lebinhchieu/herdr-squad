# QA whitebox 01 — PASS on 3ffabe7
Checked: diff vs technical AC T1-T8 (tasks/01.md), `bash -n` ok, `python3 -m unittest tests.test_squad_close` 70 OK in the Developer worktree.
Red first re-run by me: new test file on 5adfc45's bin/squad-close → 14 failures.
AC: T1-T7 met (managers retired only in squad mode, `${managers[@]+...}` safe under set -u, pin protected only when a Manager is kept and no other holder, shared pin keeps `held by`, header comment updated, ordering agents<branches<runtimes<folder<manager, tests a-g present). T8: scope/goal dry-runs pasted; squad dry-run abbreviated by hand (accepted: test_squad_close_retires_the_managers_last_and_prunes_everything covers it on the real script).
Notes (not blocking 01):
- bin/squad-migrate:13 says "(squad-close --scope would otherwise retire the Manager)" — now false. Fix the comment in task 02 (add bin/squad-migrate to its touched files; Manager OK needed).
- bin/squad-close pin lookup calls private `squadruntime._holders`; works, same repo. 
Full suite: once on the final sha after task 02 (SUITE-3b).
