# 03 evidence

## Behaviour
Fixes the 55 baseline failures (54 golden subtests + `test_no_pyc`). No product behaviour changed (tests/fixtures only).

### AC1 (suite) — root causes
**Golden, 54 subtests.** Bisect (`git archive <sha>`, `python3 -B -m unittest test_qab_optional.NoLineUnchanged.test_every_role_matches_the_4901cab_golden` from tests/): `60d7f7a` OK, `2602f80` OK, `5adfc45` FAILED (failures=54). `git show --stat 5adfc45`: only `.claude-plugin/plugin.json` (0.4.1 → 0.5.0). The compose header line `plugin: 0.5.0 unpinned · …` embeds that version, so every hash moved. Not a rules change.
Fix: `normalise()` rewrites `^plugin: <x.y.z>(?= )` to `GOLDEN_VERSION = "0.4.1"` (the version the golden was hashed with). Only that token is masked; golden unchanged for 42 of 54 keys.
After the mask, 12 keys still failed: `manager/*` and `team-lead/*` (S/M/L × design no/yes). Diff of composed output, `2602f80` vs now (manager M/no): only task 02's intended closing text: lifetime row "Lives with the scope; stays, chat-only, after the close until the PO retires it", CLOSE-1 "The Manager stays … The PO ends it with `squad-retire <manager>`", CLOSE-2 "retires the scope's agents except the Manager …", CLOSE-5 "retires every agent, the Managers last". team-lead differs only in the lifetime row. Every changed line is from 02. Those 12 hashes in `tests/fixtures/qab/golden.json` refreshed (T2); the other 42 untouched.
**Mask hides nothing else (proof).**
- append `x` to `templates/squad/process/closing.md` → `NoLineUnchanged` FAILED (failures=6).
- bump `plugin.json` version to 0.5.1 → `NoLineUnchanged` OK (bump ignored, as intended). Both reverted.

### `test_no_pyc` (T3)
Assertion unchanged. Cause: test helpers spawn `python` without `-B`, so a direct `python3 -m unittest` run writes `bin/__pycache__`. `tests/run_suite.py:46` sets `PYTHONDONTWRITEBYTECODE=1`, so the runner doesn't, but a test run by hand left the stray files. Found by bisecting per test method (`QabNo.test_m_without_qa_blackbox_has_no_ba_in_rev_21` → 6 pyc) and per file (`test_sizes`). Fixed the sources: `-B` added in `tests/rulesview.py:20`, `tests/test_dev_rules_size.py:30`, `tests/test_qab_optional.py` (3 spawns). After: clean tree, `python3 -B -m unittest test_sizes test_dev_rules_size test_qab_optional test_squadinbox` → 111 OK, `ls bin/__pycache__` → none.

### AC2
01/02 code and rules untouched (diff: 4 files under tests/). No test deleted or weakened; the one golden change is stated above.

## Tests
From `tests/`: test_qab_optional, test_squadinbox, test_sizes, test_dev_rules_size: 111 OK. Full `--tz` run: QA whitebox's (SUITE-2c).
