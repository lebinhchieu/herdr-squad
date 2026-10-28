# 01 QA whitebox, sha 31678a7 — PASS
- T1 bin/squad-close:48-50 same rule as squad-respawn:20-22; no parser; squadruntime.py untouched.
- T2/T3 tests/test_squad_close.py: composed (flat, scope, goal), legacy, neither (flat/scope/goal) assert archive + retire effects. I ran old script + new tests: 5 fails (composed only); new script: 79 OK.
- T4 `bash -n` clean; diff = squad-close, its test, ticket, evidence only. T5 only the guard + message changed.
- Non-blocking: evidence.md Behaviour says "73 tests OK", later "79" (stale number). Fix in a doc-only commit.
