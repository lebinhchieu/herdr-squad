# 04 Suite fixes evidence

## Behaviour
Test-only; no change in bin/ or templates/.
- `test_utf8_helpers` spawn test and `test_squadsettings` `spawn()` helper now pass `--prompt hello`, so 02's warning no longer fires; warning counts untouched.
- `tests/fixtures/qab/golden.json`: 12 hashes refreshed (manager and tech-lead x S/M/L x qab yes/no); other roles unchanged.
- Golden diff is only 02's wording: composing at af6da79 (before ITER-6/6c) vs now, per section: manager adds ITER-6c, changes ITER-6 + header; tech-lead changes the index only. No other section differs.
- Run from tests/, all OK: test_utf8_helpers 12, test_squadsettings 25, test_qab_optional 13, test_squad_spawn 67, test_squad_start 48, test_squad_respawn 16, test_squad_close 79, test_squadrules 51, test_templates 10, test_squadruntime 64, test_squadadopt 28.
- Not mine, untouched: test_squadinbox test_no_pyc, test_process_conversion, test_po_inbox_mod test_plugin_test_passes.
