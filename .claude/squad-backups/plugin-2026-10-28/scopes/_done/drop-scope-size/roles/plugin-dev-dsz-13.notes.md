# Notes plugin-dev-dsz-13 (ticket 13 promotion, 0.6.0)
Branch squad/plugin/drop-scope-size/plugin-dev-dsz-13. Code sha 4dde33e (suite started on the commit before; evidence-only commits since).
Done: merged 17b88b9; F1 spawn refusal text + test; F3 in promote.md open items; qa-b needle was already raw (c768b94); ADR 0018 (+ "Amended by" in 0016/0017); CONTEXT, README; changelog v9 header; snapshot history/process-v9/; plugin.json 0.6.0; tests/test_promotion_0_6_0.py (10 green); /home/chieule/workspace/squad/.claude/squads/plugin/scopes/drop-scope-size/promote.md + copy .scratch/drop-scope-size/promote.md; evidence .scratch/drop-scope-size/issues/13-promotion/evidence.md; lint baseline clean (59e2741 and branch). 598 grep-hit tests green.
Running: python3 tests/run_suite.py --receipt $(cat /tmp/dsz13-receipt) --tz > /tmp/dsz13-suite.log (ends with line exit=N). Do NOT restart it.
Todo: when log shows exit=0, add the receipt result to evidence.md Behaviour (line "Final --tz"), commit, then HANDIN 13 to plugin-tech-drop-scope-size, plugin-qaw-drop-scope-size, plugin-qab-drop-scope-size (branch, sha, how to run: python3 tests/test_promotion_0_6_0.py; note: process-version: 6 left unchanged, ADR 0016 retired the integer; 4-way version = plugin.json/changelog/README/snapshot line). On failure: fix, commit, rerun --tz.

## Retired
Ticket 13 done: both QAs PASS on cf3b5c0, TL accepted; evidence assembled e52d366, sent to TL. Nothing open. Team Lead not yet told "done" by me (TL/QAs may have).
