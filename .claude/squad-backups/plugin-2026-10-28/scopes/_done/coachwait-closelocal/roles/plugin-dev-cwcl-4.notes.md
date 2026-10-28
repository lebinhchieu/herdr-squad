
## Ticket 04 (done)
- Branch squad/plugin/coachwait-closelocal/plugin-dev-cwcl-4: code f2bb9c1, evidence b19c37c. QA whitebox PASS; qab not needed (test-only).
- Fixes: --prompt in test_utf8_helpers spawn test and test_squadsettings spawn() helper; 12 manager/tech-lead hashes in tests/fixtures/qab/golden.json refreshed (ITER-6/6c wording only).
- Run unittest from tests/ (cwd matters for imports). Golden refresh: recompute sha256 of normalise(compose(...)) per key.
- Not mine: test_squadinbox test_no_pyc, test_process_conversion, test_po_inbox_mod test_plugin_test_passes.
