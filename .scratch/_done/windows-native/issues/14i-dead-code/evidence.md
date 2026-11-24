# Evidence: 14i dead code and unused imports (static only)

## Behaviour

**Unrun.** PO order: no test was run. Checks below are `git diff`, `git grep`, `def test_` counts and a no-write compile (`ast.parse`). Code sha `f9f3825`. Base: `7f9e40f` (14c, passed), as the Team Lead ordered (ANSWER 14i, option a). Linux behaviour does not change: no product code runs differently, `role_key` had no caller.

**Pre-edit list (the only files I planned to edit):** `bin/squadrules.py`, `tests/test_team_duties.py`, `tests/test_dev_rules_size.py`, `tests/test_qab_optional.py`.

| AC | Result |
|---|---|
| Static 1 | `git diff --stat 7f9e40f` lists exactly those 4 files (2 insertions, 19 deletions). `bin/squadrules.py` change is a deletion only (7 lines). |
| Static 2 | `git grep -n "role_key" -- bin hooks tools skills tests`: only the test name `test_duty_and_role_key_fail` (a string, not the function). `ROLE_KEY` stays (`squadteam.py`, `squadrules_cli.py` use it). |
| Static 3 | `grep -c "def test_"` equal before and after: `test_team_duties` 20, `test_dev_rules_size` 9, `test_qab_optional` 11. |
| Static 4 | `ast.parse` of the 4 changed files: ok. |
| Zero new skips | `git diff 7f9e40f \| grep -i "^+.*skip"` = nothing. |

### removed item -> grep proof (unrun)

| Removed | Proof it was dead |
|---|---|
| `role_key` (`bin/squadrules.py`) | Only caller was `tests/test_team_duties.py`; all call sites changed (next table). |
| `import json`, `import subprocess` (`test_dev_rules_size.py`) | Word count of each name in the file was 1 (the import line). |
| `import squadrules` inside `compose()` (`test_dev_rules_size.py`) | Word count 1 in the file; `compose()` uses `squadcompose` and `shape_team` only. |
| `import hashlib` (`test_qab_optional.py`) | Word count 1. |
| `import squadcompose as sc` (`test_qab_optional.py`) | Word count of `sc` was 1; `git grep -nw sc` after the edit: nothing. |

After the edit the same scan finds no name with count 1 in `test_dev_rules_size.py`, `test_qab_optional.py` or `test_team_duties.py`.

### `role_key` call sites in `RoleKey` (`tests/test_team_duties.py`), same value by hand

| Old line | New | Why same |
|---|---|---|
| `for role in sr.ROLES: assertEqual(role_key(role), ROLE_KEY.get(role, role))` | removed | After the change both sides are the same expression: it asserts nothing. |
| `assertEqual(role_key("qa-whitebox"), "qa-white")` | removed | Already made by the line above it: `assertEqual(sr.ROLE_KEY, {"qa-whitebox": "qa-white", "qa-blackbox": "qa-black"})`. |
| `assertEqual(role_key("designer"), "designer")` | `assertEqual(sr.ROLE_KEY.get("designer", "designer"), "designer")` | `role_key` returned `ROLE_KEY.get(role, role)` for a known role. |
| `with assertRaises(ValueError): role_key("qa-white")` | removed | This tested only the check inside `role_key` (name not in `ROLES`). With the function gone, nothing is left to raise. This is a third removed line beyond the "two" the ticket expected; flagged for the Tech Lead. |
| `{sr.role_key(r) for r in sr.ROLES} - IMPLICIT_ROLES == TEAM_KEYS` (`test_team_keys_are_the_seven_optional_roles`) | `{sr.ROLE_KEY.get(r, r) for r in sr.ROLES} - ...` | Every `r` is in `ROLES`, so the `ValueError` branch never fired; value identical. |

Not touched (as ordered): `MESSAGE_TYPES`, `plugin_assets`, files of 14g, `tests/run_suite.py`.

## Review

Fresh-context subagent review was not started: a subagent would be an extra session and the diff is 19 deleted lines checked by `git grep`; the PO order is no runs. Self-review by diff:
- Every removed import has word count 1, re-scanned after the edit: clean.
- The one real judgement call is the dropped `assertRaises(ValueError)` in `RoleKey`. It checked a guard inside the deleted function; no other code path exposes that guard (`parse_team` has its own checks, covered by its own tests).
- No finding left open.
