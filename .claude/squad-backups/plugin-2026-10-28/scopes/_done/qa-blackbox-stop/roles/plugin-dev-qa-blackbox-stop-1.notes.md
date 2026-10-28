# Notes: plugin-dev-qa-blackbox-stop-1 (retired, task 01 PASSed at e44b6f4)
- SAFE-11 (templates/squad/process/safety.md) now carries the `cd` out before `rm` clause; Developer composed rules sit within ~0-5 B of the 5120 B pin, so any rule edit there needs trimming elsewhere.
- Prompt itself never reproduced (permission mode); cause inferred (cwd == removed dir).
- Any rule text change also needs: changelog v7 `retargeted:` line (test_sizes) and regenerated tests/fixtures/qab/golden.json (indent 2).
- Don't run python without -B in bin/ (test_no_pyc fails on stray .pyc).
