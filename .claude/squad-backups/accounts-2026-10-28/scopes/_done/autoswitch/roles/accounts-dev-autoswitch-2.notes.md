# Notes accounts-dev-autoswitch-2
- 02 handed in at 0f80fe5 (branch squad/accounts/autoswitch/accounts-dev-autoswitch-2) to QA-w, QA-b, Mgr. Awaiting PASS/FAIL.
- Evidence draft: $SCOPE_DIR/tasks/02/evidence.md. After both PASS: squad-evidence add per review file in $SCOPE_DIR/evidence/02/, check, commit, HANDIN 02 evidence sha to Mgr.
- Code: bin/cwake (python; --mark clauses 1,3 from cswitch, clause 2 from cautoswitch.wake_step; wake mode), cautoswitch wake_step/markers/batch_start, cswitch --until idle --until done + mark.
- Known: test_cache_younger_than_900s_is_used flaky (899 s boundary), pre-existing.
- Run tests: foreground unittest from tests/ >100 s: use run_in_background without a subshell &.
- 02 FAIL (qa-w F1,F2) fixed; re-handed in
- 02: qa-w PASS at 3ce1fba; waiting qa-b
- RETIRED: 02 done, both QAs PASS at 3ce1fba, evidence assembled (tasks/02/evidence.md, check ok), Mgr told. QA-w runs full suite once on scope final sha. Untested live: real herdr/claude, bare --resume cost, real failed SendMessage. Nothing open.
