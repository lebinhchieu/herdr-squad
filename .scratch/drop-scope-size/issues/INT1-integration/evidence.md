# Evidence: INT1 integration of 03 + 05 + 09
base 6ec3a75 (02 PASS); merged in order: 03 (0f4305d), 05 (8b350e8), 09 (e7a7910).

## Behaviour
- Three merges, no textual conflicts; changelog v9 (`skills/squad-process-update/changelog.md`) is one block with the 05 appends kept, no conflict markers.
- `tests/test_squad_migrate.py` + `tests/test_instructions.py` against the merged `templates/scope/scope.md`: 50 tests OK (the 2 ToPerScopeTest reds from 09 alone are green).
- One seam fixed: `tests/test_process_conversion.py` `test_every_target_is_a_rule_or_a_closed_drop_form` failed because the historic conversion mapping row `process.md:103 -> SIZE-3` names a rule 05 tombstoned. The test now accepts IDs tombstoned in `_removed.md` (`## ID (removed in vN)`). No other file touched.
- Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed 991cab6`: 1677 tests, OK, exit 0 (receipt `evidence/INT1/suite-default.txt`). First two runs failed only on test_process_conversion (the seam) and test_squadinbox `test_no_pyc` (stale `bin/__pycache__` from my own direct unittest runs, removed; not a code defect).

## QA whitebox

### QA whitebox INT1 — PASS on e3cc702 (code 8546384)
- Merges 03 (64871b4), 05 (9ffa44f), 09: only new code is tests/test_process_conversion.py (+4/-1): accepts IDs tombstoned in `_removed.md` for the historic v6 mapping row. Narrow, correct reason (SIZE-3 tombstoned by 05); e3cc702 adds evidence only.
- Suite receipt covers 8546384 (clean=yes, 1677 OK): read, not re-run (SUITE-6). I re-ran test_process_conversion, test_squad_migrate, test_instructions: 64 OK. Lint exit 0, empty.

## QA blackbox

### QA blackbox, INT1 integration (code 8546384, handin e3cc702 / 8fa0aa0, merges 03, 05, 09)

Smoke on the merged branch with scratch homes (`team: none`; `qa-white, qa-black`; `ba, team-lead, tech-lead, qa-white, qa-black`; `qa-white, qa-black, designer`): `squad-process compose` for manager, dev, team-lead, qa-whitebox, qa-blackbox, ba, tech-lead.

| Check | Saw | Result |
|---|---|---|
| Compose, 4 shapes x 7 roles | exit 0 everywhere | PASS |
| `squad-process team --home` | prints each team; undecided when no `team:` | PASS |
| `duties:` line | S: manager/dev/dev/ticket/manager...; M: qa-white, qa-black checks; L: team-lead, tech-lead, ba; with designer ui-check qa-black | PASS |
| Done text | S has TEAM-3 (no QA) | PASS |
| `squad-process lint` | exit 0 | PASS |

Not retested (unchanged by the merge, passed per task): 03 converter, 09 report and rollup (my tasks' evidence). A try of `adopt` on a hand-made fake squad failed on my fake `process.md` (version 1, no line map); my setup, not a product finding.
