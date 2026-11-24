# 10 po-inbox timing: evidence

## Behaviour

- AC2 (alone, `SQUAD_*` unset): `python3 -m unittest test_po_inbox_mod`: 3 tests OK; `claude plugin test: 648 pass, 0 fail (not skipped)`.
- AC3 (final edits, nproc 16, busy-loop PIDs 570649-570664 stopped by `kill`): 5 passes, 2 concurrent copies each, all 10 copies green, each `648 pass, 0 fail (not skipped)`.
- AC4 (scratch `/tmp/q10`, never committed): quadratic `parseBody` stand-in fails `linear > 2,000 rows x 20 cells: under 200 ms` (Expected < 200, Received 836.42); with `NOISE_MS` 100 a second stand-in fails `a far-away opener ...` (Expected < 1038.94, Received 1314.45) and `bullets nested to depth 2,500` (Received 2134.79).
- After merging task 11 (f8358d2; merge adds only 11's files): test_session_lookup, the 8 hook tests and test_po_inbox_mod: 131 tests OK.
- Details and rulings: the ticket's Comments.
