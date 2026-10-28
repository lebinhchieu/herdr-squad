# QA whitebox 04 — sha 29edfe9: PASS
- Diff 8e10686..29edfe9: plugin.json 0.6.0 -> 0.5.2 + ticket/evidence only (T1).
- git grep 0.6.0: only tests/test_squadadopt.py:312 fixture + historic 03 text. 0.5.1: historic text only. marketplace.json has no version. Nothing else keys off it (AC1).
- Full suite --tz on clean clone of 29edfe9, python3 -B: OK; receipt suite-default.txt (sha line clean=yes) (T2).
