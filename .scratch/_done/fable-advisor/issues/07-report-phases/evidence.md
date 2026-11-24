# 07 evidence

## Behaviour
`squad-report` now writes, per ticket, `phases` (7 fixed keys) and `data["phases_note"]`; `data["digest_phases"]` holds the same table; `squad-report query <scope> phases` prints it; the task drawer in `report.html` shows it.

| phase | source field | measurable |
|---|---|---|
| spawn | dev-role `Turn` (ts, tokens, cost) before the first ticket message the dev sent or received | yes; with no ticket message, all dev turns |
| build | dev turns from that message to the first HANDIN (no HANDIN yet: all later) | yes |
| handin | dev turns after the first HANDIN, outside a rework window | yes if a HANDIN exists |
| check_qa_whitebox / check_qa_blackbox | turns of agents whose roster role has `whitebox` / `blackbox`, outside rework | yes if that QA has turns on the ticket, else n/a |
| returns | any agent's turns between a FAIL and the next HANDIN (`messages.jsonl`) | yes if a FAIL exists, else n/a |
| other | turns of any other role (manager, lead, unknown) | yes if any |

A phase is a time window cut by messages, not a recorded marker. A phase with no turns is `null` (n/a), never 0. Every turn of the ticket lands in exactly one phase, so the phase sums equal the ticket totals.

Real run (read-only, output in scratchpad), `squad-report fable-advisor` and `update-not-deny`: for every ticket, phase tokens == ticket tokens and phase cost == ticket cost (diff 0.0). `fable-advisor` ticket 01: spawn 13 turns, build 13, handin 7, whitebox check 18, blackbox n/a, returns n/a, other 4. `update-not-deny` (older roster roles): only handin and other have turns; the rest n/a.

Tests: `test_squadreport_tasks` (hand-computed fixture: build 1 turn $2.00, whitebox check 1 turn $0.25, returns 2 turns $0.75 = the rework cost; ticket 09 with turns and no message lands in spawn), `test_squadreport_digest` (table matches tasks; data file without `phases` gives all n/a), `test_squad_report_query` (`phases` lines, old data still answers).

## Review
AC trace
- AC1 | tests/test_squadreport_tasks.py::test_phases_partition_ticket_turns; drawer table in templates/report/report.js | `cd tests; PYTHONPATH=. python3 -m unittest test_squadreport_tasks`
- AC2 | tests/test_squadreport_digest.py::PhaseTable; tests/test_squad_report_query.py::test_phases_lines_and_old_data | same, those modules
- AC3 | no new hex in the diff (`git diff main -U0 templates | grep -c '#[0-9a-f]\{6\}'` = 0); existing report tests pass; new tests above | run list below
Tech AC T1 evidence table above; T2 real runs above; T3 test loops all rows and keys; T4 query old-data test; T5 no new hex; T6 digest test (cap untouched, no free text); T7 run list; T8 no new dependency; T9 sums asserted equal.
Run: `cd tests; PYTHONPATH=. python3 -m unittest test_squadreport_tasks test_squadreport_digest test_squadreport_collect test_squadreport_rollup test_squadreport_rollup_ui test_squad_report_query test_squadreport_ui test_squad_report_cli test_squadreport_html test_squadreport_embed`
