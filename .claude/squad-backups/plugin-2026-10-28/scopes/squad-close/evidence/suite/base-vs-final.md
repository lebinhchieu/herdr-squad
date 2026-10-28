# Suite failures: base 5adfc45 vs final 6ebcfbd
Run from `tests/` (`python3 -B -m unittest test_qab_optional test_squadinbox`):
| sha | tests | failures | names |
|---|---|---|---|
| 5adfc45 (base) | 68 | 55 | 54× test_qab_optional.NoLineUnchanged.test_every_role_matches_the_4901cab_golden (subtests per role/size/design); 1× test_squadinbox.NoBytecodeTest.test_no_pyc |
| 6ebcfbd (final) | 68 | 55 | same 54 + same 1 |
Full-suite receipt on 6ebcfbd (clean=yes): suite-default.txt, `FAILED (files=2: test_squadinbox, test_qab_optional)`; 1400 tests, all other files pass.
Verdict: pre-existing; not caused by squad-close. Manager takes a PO waiver + separate fix ticket (ANSWER 02).
