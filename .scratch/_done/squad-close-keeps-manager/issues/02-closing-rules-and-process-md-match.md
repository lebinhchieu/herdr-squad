# 02 closing rules and process.md match
Status: ready-for-agent
Type: task
Blocked by: 01

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; QA whitebox runs the full suite once on the final sha (`python3 tests/run_suite.py --receipt <dir> --if-changed <base>`). Ticket + evidence path: `.scratch/squad-close-keeps-manager/issues/NN-<slug>.md` and `.../NN-<slug>/evidence.md` (commit this task file there as the ticket). Design: `.scratch/squad-close-keeps-manager/grill.md`; decisions in `$SCOPE_DIR/iterations/1.md`.

Touched files: `bin/squad-migrate` (line ~13 comment, now false; comment only), `templates/squad/process/closing.md` (CLOSE-1, CLOSE-2, CLOSE-4; also check CLOSE-3b wording stays true), `templates/squad/process.md` (Closing lines ~156-159; START-5 lifetime row if it says the Manager ends with the scope). After editing run `squad-process lint` (before and after). Rule text per FILE rules: name who acts, when, limit; no history.

## Business AC
1. CLOSE-1: after `squad-close` the Manager is not retired; its last action is still the command, it says everything first because its `$SCOPE_DIR` has moved and it is chat-only after; PO ends the session with `squad-retire <mgr>` when wanted.
2. CLOSE-2: no "its Manager last", no "closes the Manager's pane"; mention the closing scope's pin is kept while its Manager lives.
3. CLOSE-4: goal close does not retire the goal Manager.
4. CLOSE-5 unchanged (squad close retires all).
5. `process.md` Closing section and lifetime table match; `squad-process lint` clean; all `tests/` lint/rule-count tests touching these files still pass.

## Technical AC (QA whitebox; agree or counter in this file)
T1. Text matches 01's final behaviour exactly: scope/goal close keep the Manager (chat-only after: its `$SCOPE_DIR`/`$GOAL_DIR` has moved; PO ends it with `squad-retire <mgr>`); squad close retires all (CLOSE-5, unchanged). Check against 01's final sha, not its draft.
T2. Every place that says the Manager ends with the close is found and fixed: grep `templates/`, `README.md`, `CONTEXT.md`, `docs/`, `skills/`, `agents/`, `hooks/` for "Manager last", "closes the Manager's pane", "Lives and ends with the scope", "Manager is gone", "retires the goal Manager". Hits left alone are listed in evidence with a reason. START-5 lifetime row and any `squad-process`/Manager role text (`agents/manager*`, `templates/squad/process/*.md` citing CLOSE-1) checked.
T3. CLOSE-3b stays true (goal Manager respawns after `--scope`; it was never retired by it). CLOSE-3c/3a untouched unless wrong.
T4. Rule form: each rule keeps its header block (`roles:`, `when:`, `topic:`), names who acts, when, limit; no history ("no longer", "now"); no new rule IDs or citations that break `squad-process lint`. `squad-process lint` clean before and after (both outputs in evidence). `process.md` Closing section stays consistent with `closing.md` (same words for the same fact).
T5. Tests: `tests/test_process_writing.py`, `test_process_citations.py`, `test_pod_rules_process.py`, `test_sizes.py` and any test that greps closing.md/process.md text run green (list in evidence); if a test pinned the old wording, update it in this task and say so.
T6. Diff touches only the files in the ticket (plus tests that pinned wording); no ADR/CONTEXT edits unless T2 finds a hit (then Manager is told first). `promote.md` for the scope: none expected; QA whitebox checks that claim at the end.
