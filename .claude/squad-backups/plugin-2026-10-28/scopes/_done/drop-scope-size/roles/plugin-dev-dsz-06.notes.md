# Notes plugin-dev-dsz-06 (ticket 06)
## Now
- Re-HANDIN sent at bd361cf (INT1 merged) to qaw, qab, tech. F1 (ITER-3b when = `team-lead = no and qa-black = yes`) and F2 (team-lead card) fixed; changed-rule equivalence test added; test_sizes adapted (34 green); lint empty.
- Waiting for PASS/FAIL. On FAIL: fix, re-verify, new sha, HANDIN again (LC-3a). On PASS from both QAs: tell Team Lead, evidence per EVID-2b if asked, then stop.
- Evidence: .scratch/drop-scope-size/issues/06-rules-small-files/evidence.md (sha line still `pending`).
## For a successor
- Branch squad/plugin/drop-scope-size/plugin-dev-dsz-06, sha bd361cf (INT1 6389642 merged). Team Lead told (STATUS 06).
- Design deviations to keep stating: ITER-3b `team-lead = no and qa-black = yes` (lint allows one duty/role key + qa-black only); ITER-3b/FILE-8/ITER-6a/6b use handin-target; WHO-1b unconditional, WHO-2b not Manager's at S (named in ChangedRulesEquivalence).
- test_sizes size-line checks skip rules with no size/qa-b `when` (team_keyed helper); 128-set sweep + tests/test_small_files_equivalence.py cover them.
- test_squadinbox.test_no_pyc: delete bin/__pycache__ (stale), not code.
- Evidence sha line in evidence.md still `pending`; EVID-2b assembly only after both QA PASS.
# plugin-dev-dsz-06 notes
- Ticket 06 code final bd361cf (QAW+QAB PASS). Evidence-only follow-up 9620c7e: evidence.md names test_sizes `team_keyed` skip. HANDIN sent to plugin-qaw-drop-scope-size (doc-only, no new verdict).
- Nothing open. No processes/servers started.
