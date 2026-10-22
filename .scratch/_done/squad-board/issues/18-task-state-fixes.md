Status: resolved
State: done (PASS; in the iteration-2 line merged at 7f0b436)
Task ID: BRD-18
Blocked by: 09 (branch from BRD-09's passed sha 5e005ec)
Files touched: `bin/squad-board` (only `derive_tasks`), `tests/test_board_tasks.py`, `tests/test_board_state.py` (rename one stale test name)

# BRD-18: task-state refinements found on real data: returns count HANDIN→FAIL rounds, done is sticky

**Done when a FAIL fanned out to several recipients counts as one return, a PASS stays `done` when a later STATUS, DECISION, ASK or ANSWER mentions the task, and a fixture copying the real fan-out pattern replays to the right states and counts.**

Found by qaw-board on BRD-09 by running the merged server on the real message log: BRD-01, 03, 04 showed `returns` 3 after one FAIL (three records), and BRD-01, 04, 05, 06 showed `building` after a PASS. Binding rules (Manager's decision 2026-10-12, no time window): design.md "Needs-you and tasks": Return count, Done is sticky.

## Technical AC (BRD-18)
1. **Fan-out:** three FAIL records for one task from one sender within 0.5 s to three recipients → `returns` 1, state `returned`. Two records 2.2 s apart to two recipients → 1.
2. **Two QAs, one HANDIN:** FAIL from qaw-board then FAIL from qab-board → `returns` 1.
3. **Count rule (HANDIN→FAIL rounds):** a FAIL counts a return only if a HANDIN came after the last counted FAIL, or none was counted yet. FAIL, HANDIN, FAIL → 2. FAIL, STATUS, FAIL → 1. FAIL, BLOCKED, FAIL → 1. A fan-out interrupted by another agent's STATUS on the task (FAIL to dev, STATUS, FAIL to manager) → 1. A first FAIL with no HANDIN before it counts 1; a second FAIL with no HANDIN in between does not. The state after any FAIL is `returned`.
4. **Loop still counts:** HANDIN, FAIL, HANDIN, FAIL, HANDIN, PASS → `returns` 2, `done` (BRD-03's tests stay green).
5. **Done is sticky:** PASS, then each of `STATUS BRD-01: PASS from qaw-board`, `DECISION BRD-01: PASS by qaw`, ASK and ANSWER naming the task, one test per type, → state stays `done`; `last_ts` and `last_type` still follow the latest message. A repeated PASS stays `done`.
6. **Reopen:** HANDIN (→ `checking`), FAIL (→ `returned`, counted by rule 3) and BLOCKED (→ `blocked`) reopen a done task: PASS, then HANDIN → `checking`; PASS, then FAIL → `returned` and the return counted; PASS, then BLOCKED → `blocked`. **HANDIN→FAIL→HANDIN→FAIL one second apart** (BRD-03's loop spacing) → `returns` 2.
6b. **Not-done tasks keep the spec table:** FAIL then `STATUS BRD-xx: fixing` from the Developer → `building` (returns unchanged); BLOCKED then another agent's STATUS → `building` (accepted, pinned).
7. **Ordering by `ts`**, not file order, for all of the above (shuffle the records in one test).
8. **Real-pattern fixture (synthetic):** a small log that copies the shapes found in the real `squad/messages.jsonl` with fake names and IDs: a FAIL fanned out to dev, manager and tech lead; a FAIL fanned out to two recipients 2.2 s apart; a PASS fanned out to three, then a second PASS 8 minutes later; `STATUS … PASS from …` and `DECISION … PASS by …` after a PASS. Expected `returns` and `state` per task written out by hand in the test, not copied from server output.
9. **Rename** `test_stub_sections_give_empty_lists` in `tests/test_board_state.py` to what it now tests (it no longer tests stubs); nothing else in that file.
10. **Baseline AC 1 to 5, 7, 9, 10** from design.md; touch only `derive_tasks` and the listed test files.

### QA whitebox additions (qaw-board)

Final rules (Manager's binding decision, ticket AC 1 to 10 and design.md): `returns` = HANDIN→FAIL rounds (a FAIL counts only if a HANDIN came after the last counted FAIL, or none was counted yet); done is sticky against STATUS, DECISION, ASK and ANSWER; HANDIN, FAIL and BLOCKED reopen it; for a task that is not done, STATUS and DECISION set `building` (AC 6b). I add only what I verify:

Q1. **Each AC sequence is its own test** (AC 1 to 6b), not one loop, so a failure names the rule. Exact sequences: FAIL×3 → 1; HANDIN FAIL HANDIN FAIL (1 s apart) → 2; FAIL STATUS FAIL → 1; FAIL BLOCKED FAIL → 1; a fan-out interrupted by another agent's STATUS → 1; FAIL HANDIN FAIL FAIL → 2; two QAs after one HANDIN → 1; a first FAIL with no HANDIN → 1.
Q2. **Done sticky, one test per type alone:** after PASS, each of STATUS, DECISION, ASK, ANSWER leaves `done` and `last_ts`/`last_type` follow the message; HANDIN → `checking`; FAIL → `returned` (counted); BLOCKED → `blocked`. Then PASS, BLOCKED by X, `working` event for X → `building` (BRD-03's unblock rule); a `working` event of another agent changes nothing.
Q3. **AC 6b pinned both ways:** FAIL then a Developer STATUS → `building`; BLOCKED then another agent's STATUS → `building` (accepted); a later FAIL after that STATUS still counts only if a HANDIN came in between.
Q4. **Iteration filter:** HANDIN, FAIL×3, HANDIN, PASS tagged 1 and HANDIN, FAIL tagged 2: `?iteration=1` → `done`, `returns` 1; `?iteration=2` → `returned`, `returns` 2. `needs_you` identical in both queries.
Q5. **Real-log replay (my acceptance check):** I replay a copy of the live `squad/messages.jsonl` and compare every task's `returns` and `state` with my own script written from the binding rules. A mismatch is a FAIL whichever side is wrong.
Q6. **Mutants I will run:** FAIL always counts; a non-HANDIN message re-arming the count; HANDIN not re-arming; counter shared across tasks; done sticky missing for each of STATUS, DECISION, ASK, ANSWER in turn; sticky also blocking HANDIN, FAIL or BLOCKED; `last_type`/`last_ts` frozen while done; ordering by file index instead of `ts`. All must be killed by tests in `tests/test_board_tasks.py`.
Q7. **Scope:** diff touches `derive_tasks` (and constants of the tasks section) only; `derive_needs_you` untouched; existing BRD-03 tests unchanged unless a rule truly changed (listed in dev-evidence); the rename in `test_board_state.py` is the only edit there.
Q8. **Fixture hygiene (AC 8):** grep the added test data for `/home/`, `lebinh`, `chieule` and real message text.

## Comments
- 2026-10-12 tech-board: BINDING by the Manager (supersedes every earlier BRD-18 message): a FAIL counts a return only if a HANDIN came after the last counted FAIL, or none was counted yet (FAIL, STATUS, FAIL = 1; two QAs on one HANDIN = 1; no accepted limitation). Done is sticky against STATUS, DECISION, ASK and ANSWER; HANDIN → checking, FAIL → returned (counted by that rule), BLOCKED → blocked. The QA whitebox section was left as qaw-board wrote it; where it still says BLOCKED is sticky or that the limitation is pinned, the AC above win.
