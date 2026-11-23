## Behaviour
- `status_of("State: ready (no Developer yet)")` -> `ready`; `State: handed in (5bc3126); QA next` -> `handed in`; both lines -> the `Status:` value.
- Run from `tests/`: `python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask test_windows_safe test_utf8_helpers test_instructions` -> Ran 98 tests, OK. [SQ-10] included.

## Review
AC trace (checks table: see `checks.md`)
- AC1 | tests/test_squadtickets.py::test_watchdog_blind_state_line_is_read_when_no_status | `cd tests; python3 -m unittest -q test_squadtickets`
- AC2 | same test, both-line cases | same
- AC3 | test_squadtickets, test_squadboard_tasks, test_squadtask | `python3 -m unittest -q <module>` from tests/
- AC4 | none needed, CONTEXT.md has no `Status:` definition | `grep -n 'Status:' CONTEXT.md`

## QA blackbox

### QA blackbox, task 02 (State: line), sha da9c43a

Run: scratch Python call of the shipped `squadtickets.status_of(text)` on branch da9c43a vs base 205432a (fixture ticket texts in /tmp, scripts /tmp/qab_st.py, /tmp/qab_real.py). Nothing run against wpw (only read guardian task files as text input).

| AC | shot/live | What I did | What I saw | Result |
|---|---|---|---|---|
| 1 | live | `State: ready (no Developer yet)`; `State: handed in (5bc3126); QA pending`; `State: In Progress`; `State: READY` | `ready`; `handed in`; `in progress`; `ready` (base: all ''). `State:` on line 12 read, on line 13 -> '' | PASS |
| 1 | live | Same values written as `Status:` vs `State:` (`ready.`, `**done**`, `waits for 02`, `Ready (x)`) | Identical output for both lines every time (same normaliser) | PASS |
| 2 | live | State-then-Status and Status-then-State (`done` / `ready`); State line 2 + Status line 13 | `done` both orders; Status past line 12 not seen, State used -> `ready` (consistent with first-12-lines rule) | PASS |
| 3 | live | `cd tests; python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask test_windows_safe test_utf8_helpers test_instructions` | Ran 98, OK | PASS |
| 4 | live | no `CONTEXT.md` edit in diff list (Dev's grep: only 2 `Status:` hits, no ticket-line definition) | none needed | PASS |
| real data | live | 229 real guardian scope task files through `status_of` | base: 198 '' ; da9c43a: 108 ''. 90 more read (ready 48, ready. 33, handed in 2, building 2, returned 1, waiting 1, waits 1, **done 2) | PASS |

Unhappy paths: empty `State:` -> ''; `The State: of things` in prose -> ''; no lines -> ''.

Follow-ups (not AC, no FAIL, SQ-4):
- 91 guardian tickets still read '' : they write lowercase `state: ready · repo: ...` or `**State:** ready`. `Status:` has the same limits (lowercase and bold forms also read ''), so this matches "normalised exactly like Status:". If the watchdog should see those, a later ticket must widen both.
- Existing normaliser leaves `ready.` and `**done` as values (same for `Status:`); not new.

## QA whitebox

### QA whitebox, task 02, sha da9c43a: PASS

Checked: diff of bin/squadtickets.py (status_of) and tests/test_squadtickets.py against base 205432a; ran in a detached worktree at da9c43a, from tests/: `python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask test_windows_safe test_utf8_helpers test_instructions` -> Ran 98, OK.

Code: one shared normaliser; Status found first then State over the same 12 lines; `^State:` anchored; an empty `Status:` line still wins (returns ''). Callers read: bin/squadtask.py:358 (claim warning ticket_status) and :518 (word()), bin/squadtickets.py:95 (rows, used by the board `_tickets` and the watchdog). None writes the status. squadboard_list._ticket_status is dead code (no caller), left alone. CONTEXT.md 54/220 do not define the ticket line: no edit needed.

#### Follow-ups (not blocking, backlog)
- T2/T3/T5 had no test of their own (false friend `Statement:`, empty `Status:` beating `State:`, one folder-level mixed fixture); code verified by reading. T4 callers not listed in Design notes (listed above).
- A ticket whose `State:` reads `claimed`, `done` or `wontfix` now also feeds squadtask.word()/claim warnings, same as `Status:`. Intended; watch in 03 blind test.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | tests/test_squadtickets.py test_watchdog_blind_state_line_is_read_when_no_status (State: ready -> ready; State: handed in (..) -> handed in; State past line 12 -> ''); `cd tests; python3 -m unittest -q test_squadtickets` OK | cd tests; python3 -m unittest -q test_squadtickets (ran on da9c43a in a detached worktree: OK); read bin/squadtickets.py status_of diff | live: status_of on State: fixtures -> ready / handed in / in progress; 90 more of 229 real guardian tickets read (evidence/02/qa-b.md) PASS |
| AC2 | same test: "State: ready\nStatus: done" and "Status: done\nState: ready" -> done | same test file; code reads Status first then State over the same 12 lines | live: both orders -> done PASS |
| AC3 | `cd tests; python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask` OK (grep -rl squadtickets tests/ hits) | cd tests; python3 -m unittest -q test_squadtickets test_squadboard_tasks test_squadtask test_windows_safe test_utf8_helpers test_instructions -> Ran 98 OK | live: 98 OK (same six modules) PASS |
| AC4 | `grep -n 'Status:' CONTEXT.md` hits only line 54 and 220, no definition of the ticket line; no edit | grep -n "Status:" CONTEXT.md (lines 54, 220: no definition of the ticket line) | live: no CONTEXT.md edit needed PASS |
