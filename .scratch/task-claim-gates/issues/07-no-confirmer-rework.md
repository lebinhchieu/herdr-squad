# 07 Rework task 01: no confirmer, no-QA evidence path

Status: ready-for-agent
Blocked by: 01 (stacked on branch squad/plugin/task-claim-gates/plugin-dev-tcg-1 at 0c7ef66)

Chieu E3/E4 removed the confirmer. In `bin/squadtask.py` and its tests: slots (M) = QA agents on the roster; a roster with no QA has one slot `evidence`, filled by `from_message` on HANDIN when `squad-evidence check` exits 0 (D9: no `--base`, worktree found from the branch, `HEAD` must equal the handed-in sha). Failure gives W9 on the handin event and in `additionalContext`, no pass. A PASS from manager, team-lead or tech-lead gives W4, no event. W6 = manual `passed` override with checks missing; W7 text "merged before it passed". Verbs: `pass` = a QA's PASS, `passed` = manual override. With a QA on the roster `squad-evidence` is never started. Remove the confirmer code and tests; do not break what QA already passed.

Also fix (Tech Lead review of 64b0785): (1) `parse_blocked_by` reads only the leading ticket numbers, so `02 (needs 3 tests)` gives one blocker (T21). (2) `squad_dir_of` for `scopes/_done/<scope>` returns the squad folder (T22). (3) A FAIL from any sender is recorded, also a Tech Lead's (D7). (4) Tests and hand checks never write the real `$SQUAD_DIR/task-events/`: use a temp squad folder or `--scope-home <temp>` (T23). Retired QA rows still count when no QA is live (design.md s4). Passes by override: `passed NN` = slot `override`, W6.

Files: bin/squadtask.py, bin/squad-task (only if verbs change), tests/test_squadtask.py
AC: states.md W4, W6, W7, W9, AC3-AC5, AC20, s4. Technical AC: T8, T19-T24 (design.md s8); T1, T6 still hold.
Spec: tasks/states.md (BA, final, E3/E4 applied), tasks/design.md (D7, D9). Gates warn, never block. Targeted tests only (repo CLAUDE.md). Store: events in `$SQUAD_DIR/task-events/<slug>.jsonl`.
