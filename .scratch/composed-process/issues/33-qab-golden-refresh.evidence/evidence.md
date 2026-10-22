# 33 evidence

## Behaviour
- AC1: `git diff 88f5834..HEAD --stat` → ticket, evidence, `tests/fixtures/qab/golden.json` only.
- AC2: golden regenerated with `compose`/`normalise` from `tests/test_qab_optional.py`; 54 keys, order, format unchanged. 26 hash lines changed (52 diff lines); the other 28 keys' hashes are identical (roles unaffected by REV-22/SIZE-2/SIZE-22).
- AC3: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_qab_optional test_sizes test_dev_rules_size` → `Ran 56 tests in 64.329s OK`. `bin/squad-process lint` exit 0. `__pycache__` removed.
- AC5: `git diff 853b0a4 HEAD -- templates/squad/process/` shows only review.md (REV-22: Opus → Sonnet review subagent, `effort: high`) and sizes.md (SIZE-2/SIZE-22: S row and "Code check" row Opus → Sonnet). No other rule file differs, so the golden changes only because of those rules.
- AC4: no full suite run.

## Review
Mechanical regeneration, no logic. Self-check: test passes against the regenerated golden; diff touches hashes only.
