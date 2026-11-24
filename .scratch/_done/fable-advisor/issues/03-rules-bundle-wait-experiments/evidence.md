# 03 evidence
## Behaviour
Three rules added: LC-6c (bundle, Manager and Team Lead), COST-8b (long PO wait, Manager), ITER-18 (rule experiment, Manager and Coach). Lint passes. Cache lifetime: 1h, from `CACHE_TTL_S = 3600` in `bin/squadtranscript.py` and the session's 1h TTL; not checked against Claude docs, and COST-8b says so.
Dev rules are unchanged (the three rules are not attached to dev); Manager composed size grew 842 B and its test bases were raised.
## Review
AC1 | tests/test_rules_wording.py SmallRulesTest | `PYTHONPATH=tests python3 tests/test_rules_wording.py`
AC2 | same test (COST-8b) | same
AC3 | same test (ITER-18) | same
AC4 | lint + test_rules_contract + test_squadrules | `python3 bin/squad-process lint --plugin-root .`
