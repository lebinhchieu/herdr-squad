Status: resolved
State: done
Task ID: BRD-03
Blocked by: 01
Files touched: `bin/squad-board` (only the `tasks` and `needs-you` sections), `tests/test_board_tasks.py` (new)

# BRD-03: task states with return counts, and needs-you items

**Done when `/state` returns `tasks` and `needs_you` per design.md "Needs-you and tasks", checked through fixture tests.**

Read first: design.md "Needs-you and tasks", "State JSON", "Iteration filter"; spec "Derivation rules" (task table, needs-you), stories 2–5, 41–44. Replace the bodies of `derive_tasks` and `derive_needs_you` only. Neither depends on BRD-02.

## Technical AC (BRD-03)

1. **State table:** one test per row: DECISION and STATUS → `building`; BLOCKED → `blocked`; HANDIN → `checking`; FAIL → `returned`, `returns` +1; PASS → `done`.
2. **ASK / ANSWER:** do not change an existing task's state; the first mention creates it as `building`. A message with a null task creates nothing.
3. **Loop:** HANDIN, FAIL, HANDIN, FAIL, HANDIN, PASS → `done` with `returns` 2; after the second FAIL `returns` is 2 and `state` `returned`.
4. **Blocked back to building:** BLOCKED by X, then a `working` event for X → `building`. A `working` event for another agent changes nothing. A HANDIN between the two wins (stays `checking`).
5. **Task order and keys:** first appearance; each task has exactly `id, state, returns, last_ts, last_type`.
6. **Iteration filter:** `?iteration=1` shows task state as of the end of iteration 1 (a PASS tagged 2 does not show); `needs_you` is identical for both queries.
7. **Needs-you, blocked agent:** latest activity event `blocked` → item `kind` `blocked`, `agent`, `since`, `id` `blocked:<agent>:<ts>`; a later `working` removes it.
8. **Needs-you, escalation:** each row of `escalations.md` with an empty Answer cell → `escalation:<#>`; answered rows absent.
9. **Needs-you, Manager idle:** Manager's latest event `idle` or `done`, the current iteration's `## PO check-in` has empty **Done** and **Next** bullets → `manager_idle:<iteration>`. Not raised when: the Manager has no events, Manager is working, Done or Next has text, or there is no iteration file. A filled "Decisions from the PO" bullet alone does not suppress it.
10. **BLOCKED message is not a needs-you item** (explicit test): BLOCKED from dev to tech-lead appears in `tasks` as `blocked` and in no `needs_you` item.
11. **Order of `needs_you`:** blocked agents (roster order), then escalations (row order), then Manager idle.
12. **Baseline AC 1 to 5, 7, 9, 10** from design.md "Technical AC".

### QA whitebox additions (qaw-board)
Q1. **Real escalations table:** a test uses the live `squad/escalations.md` rows verbatim (row 1 answered `2026-10-12: A`, row 2 empty): only row 2 is a needs-you item. Also: `#` cell missing or duplicated → id falls back to the row index, no crash; a row with fewer cells than the header counts as unanswered; placeholder-only Answer cells (`—`, `-`) are stated as answered or unanswered, and tested.
Q2. **`unknown` as latest event:** an `unknown` event after `blocked` neither clears nor sets the blocked item (it is ignored everywhere, matching the timeline). Same for column `status`. State the rule in the ticket comment.
Q3. **Retired agent** (roster Status not `live`) whose last event is `blocked`: stated rule (proposal: still listed? no, skip retired) and tested.
Q4. **Manager lookup** is by roster Role `Manager`; no Manager in the roster → no `manager_idle`, no crash. Check-in section parsing tolerates CRLF, missing `## PO check-in`, and bullets like `- **Done (with evidence):**` followed by indented text on the next line (counts as filled).
Q5. **Task id shape:** `task` values come from the log as-is; a non-string or empty `task` creates nothing.
Q6. **Blocked→building** uses event order by `ts`, not log order, and ignores `working` events earlier than the BLOCKED message.

## Comments
- 2026-10-12 tech-board: PASS by qaw-board at fe5eda2 (squad/dev-board-4), after round 1 FAIL 31aad06. Decisions added: blank escalation rows skipped, heading ends check-in bullet.
