# 19 integration of 05 + 07, ready-for-review wiring, ticket folder rule
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Integration task: GOAL-6b. Hand in to BOTH QAs; never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 05, 07 (both passed)

## What the PO gets
- The banner's ready-for-review count (T05.AC8) is real, not `unknown:ready_for_review`.
- A scope with no `tickets:` line and no `.scratch/<scope>/issues` folder shows no tasks and `unknown:tickets`, never another scope's tasks (QA blackbox note on 07: questions, parked, alpha-ui showed checkout's 9).

## Rules
- Base: branch `squad/board/dashboard/board-dev-inbox-10` (05, 08, 06, 04, 03, 17, 02). Merge `squad/board/dashboard/board-dev-tasks-9` (07, 188e9a5). Run the targeted tests of both.
- Wire `squadboard_inbox` to call `squadboard_tasks.ready_by_scope(sel)`; one wiring test (a ready-for-review branch of S3 with the choice S1, as T05.AC8).
- `squadboard_tasks` resolves a scope's ticket folder with the same rule as `squadboard_list` (a `tickets:` line, else `.scratch/<scope>/issues`, else unknown). Never use the `squadtickets.find_tickets` guess. One test: a scope with no match returns no tasks and `unknown:tickets`.
- Business AC: T05.AC8; T07 AC on tasks of the chosen scope only. QA blackbox re-checks both.

## Touched files
- Edit: `bin/squadboard_inbox.py`, `bin/squadboard_tasks.py`, their two test files.
- No other file.

## Comments
