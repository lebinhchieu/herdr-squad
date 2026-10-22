# 04 Suite fixes evidence

## Behaviour
Test-only; no change in bin/ or templates/.
- `test_utf8_helpers` spawn test and `test_squadsettings` `spawn()` helper now pass `--prompt hello`, so 02's warning no longer fires; warning counts untouched.
- `tests/fixtures/qab/golden.json`: 12 hashes refreshed (manager and tech-lead x S/M/L x qab yes/no); other roles unchanged.
- Golden diff is only 02's wording: composing at af6da79 (before ITER-6/6c) vs now, per section: manager adds ITER-6c, changes ITER-6 + header; tech-lead changes the index only. No other section differs.
- Run from tests/, all OK: test_utf8_helpers 12, test_squadsettings 25, test_qab_optional 13, test_squad_spawn 67, test_squad_start 48, test_squad_respawn 16, test_squad_close 79, test_squadrules 51, test_templates 10, test_squadruntime 64, test_squadadopt 28.
- Not mine, untouched: test_squadinbox test_no_pyc, test_process_conversion, test_po_inbox_mod test_plugin_test_passes.

## QA whitebox

### 04 / scope suite, final sha f2bb9c1 — receipt suite2/
- 04 code: test-only (--prompt in 2 spawn calls; 12 golden hashes manager/tech-lead S/M/L x qab yes/no); bin/ and templates/ untouched; golden verified by test_qab_optional passing in the suite. T1-T4 met.
- Suite (`--tz`, tree clean): FAILED files=3 of the run:
  - test_squadinbox test_no_pyc, test_process_conversion: waived by Manager (fail on main).
  - test_squad_report_cli Refusals.test_no_messages_no_transcripts_builds_empty_report: report.html compared byte-for-byte across two builds; `generated_at` straddled a second (…:35:17Z vs …:35:18Z). Passes alone on the sha and on main. Timing flake, squad-report untouched by this scope. NOT in the Manager's waiver: needs a ruling.
  - test_po_inbox_mod passed in the suite this time and alone (490 pass).
- All 02-caused failures from ea196bb are gone (test_utf8_helpers, test_squadsettings, test_qab_optional green).
