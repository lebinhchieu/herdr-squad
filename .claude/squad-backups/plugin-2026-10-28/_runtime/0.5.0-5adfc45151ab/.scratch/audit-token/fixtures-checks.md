# What each fixture's checks.py tests (plain language)

Each `fixtures/<c>/` holds `prompt.md`, `input/` (the files the model sees), `checks.py`, `selftest/good.txt` + `bad.txt`. A defect = one failed check; no judge-LLM.

| Fixture | Checks (each failed one is a defect) |
|---|---|
| receipt | Bad receipt (sha differs in the last 2 chars, last line FAILED). Expect sha_match=false, clean=true, ok_line=false, verdict=FAIL; reply must be JSON. Catches an always-PASS answer. |
| receipt2 | Good receipt (sha identical, clean=yes, last line OK, decoy test names containing "failure"/"FAIL"). Expect sha_match=true, clean=true, ok_line=true, verdict=PASS. Catches an always-FAIL answer. No clean=no case (run cap). |
| usage | 24 rows, 6 roles: top role by cost, its cost (within 0.02 USD) and the total (within 0.02 USD) recomputed from input/ with the prices in checks.py. |
| usage2 | Same with 40 rows, cache-read heavy; the top role by cost is not the largest-token role. |
| repoq | Callers of config.load: exactly src/client.py and src/jobs.py (report.py only imports DEFAULTS, util.py only mentions load() in a comment); timeout_s = 45 (docs/notes.md has a stale 30). |
| repoq2 | Same with decoys: alias import in jobs.py (must be found), reload() in cache.py, load() in a docstring, download( in util.py, callers in scripts/ and tests/ (outside src/), stale 30 and 60 in docs. |

Self-test (`python3 -I scripts/selftest_checks.py`): good.txt scores no defect, bad.txt at least one, for every fixture. usage/repoq answers are single-valued by design; a constant answer cannot pass them.
