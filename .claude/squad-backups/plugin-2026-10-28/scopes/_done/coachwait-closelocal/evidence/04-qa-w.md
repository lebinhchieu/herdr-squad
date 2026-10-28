# 04 / scope suite, final sha f2bb9c1 — receipt suite2/
- 04 code: test-only (--prompt in 2 spawn calls; 12 golden hashes manager/tech-lead S/M/L x qab yes/no); bin/ and templates/ untouched; golden verified by test_qab_optional passing in the suite. T1-T4 met.
- Suite (`--tz`, tree clean): FAILED files=3 of the run:
  - test_squadinbox test_no_pyc, test_process_conversion: waived by Manager (fail on main).
  - test_squad_report_cli Refusals.test_no_messages_no_transcripts_builds_empty_report: report.html compared byte-for-byte across two builds; `generated_at` straddled a second (…:35:17Z vs …:35:18Z). Passes alone on the sha and on main. Timing flake, squad-report untouched by this scope. NOT in the Manager's waiver: needs a ruling.
  - test_po_inbox_mod passed in the suite this time and alone (490 pass).
- All 02-caused failures from ea196bb are gone (test_utf8_helpers, test_squadsettings, test_qab_optional green).
