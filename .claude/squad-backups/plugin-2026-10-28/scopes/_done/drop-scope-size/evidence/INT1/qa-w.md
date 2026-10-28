# QA whitebox INT1 — PASS on e3cc702 (code 8546384)
- Merges 03 (64871b4), 05 (9ffa44f), 09: only new code is tests/test_process_conversion.py (+4/-1): accepts IDs tombstoned in `_removed.md` for the historic v6 mapping row. Narrow, correct reason (SIZE-3 tombstoned by 05); e3cc702 adds evidence only.
- Suite receipt covers 8546384 (clean=yes, 1677 OK): read, not re-run (SUITE-6). I re-ran test_process_conversion, test_squad_migrate, test_instructions: 64 OK. Lint exit 0, empty.
