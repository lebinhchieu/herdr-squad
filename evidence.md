# legacy-team-prune evidence (static, TEST FREEZE: no test run)

## Behaviour
`legacy_team` and `_first_token` are gone from `bin/squadrules.py`. Six test sites now call `shape_team` in `tests/rulesview.py`.

Side by side, the lines that decide a team (old -> new):
- S: no tokens -> `set()`
- M: `{qa-white}` plus `qa-black` if qa-b yes -> same
- L: M plus `ba, team-lead, tech-lead` -> same set
- design yes adds `designer`; architecture yes adds `architect` -> same
- result ordered by `TEAM_KEYS` -> same

By hand, the calls the sites use:
- `SHAPE_ARGS["M"] = ("M",)` -> `[qa-white, qa-black]` in TEAM_KEYS order
- `SHAPE_ARGS["Lgoal"] = ("L",)` -> `[ba, team-lead, tech-lead, qa-white, qa-black]` in TEAM_KEYS order
- `("S","yes","no","no")` (`_size_shapes`) -> `[]`

Not kept (by design): free text, blank size (old gave None), bad flag (old ValueError). Bad size now raises KeyError.

## Static checks
1. `git grep -n "legacy_team\|_first_token" -- bin tests docs CONTEXT.md CLAUDE.md skills templates agents hooks` -> only `tests/test_squadcompose.py:382` (the needle). Nothing in `bin/`. test_team_duties, test_sizes, test_team_lead_role untouched.
2. No-write compile of the 7 files -> COMPILE_OK.
3. `git diff --stat f25e49c..HEAD`: only the 7 files; `bin/squadrules.py` 32 deletions, 0 insertions.
4. `git grep -nE "size:|'size'|\"size\"|qa-b\b" -- bin/squadrules.py | wc -l` -> 4 (allow-list now 4).
5. `def test_` counts equal to f25e49c: dev_rules_size 9/9, qab_optional 11/11, small_files_equivalence 2/2, squadcompose 42/42, old_language_inventory 2/2.
7. No new skip, no new test file, no `bin/` change except the deletion.
