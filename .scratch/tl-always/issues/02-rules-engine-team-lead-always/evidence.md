# 02 Rules engine: team-lead always present: evidence
## Review

AC trace (`cd tests; python3 -m unittest <file>`; greps from the repo root). See `## Checks` in checks.md.

- AC1 | `test_squadrules.py::TeamLeadImplicitTest::test_team_lead_token_is_ignored_and_never_a_fact` | `python3 -m unittest test_squadrules`
- AC2 | `test_squadrules.py::TeamLeadImplicitTest::test_handin_target_is_team_lead_without_a_qa`; `test_team_duties.py` (64 teams, 12 duties) | same
- AC3 | `test_squadrules.py::LintClassTest::test_old_when_keys_are_a_lint_error_naming_rule_and_new_key` (rows `plan-owner = manager`, `team-lead = yes|no`) | same
- AC4 | `test_squadupgrade.py::OldWhenLanguage::test_removed_team_lead_conditions_are_listed_with_their_translation` (four conditions, exit 3 as `size`, nothing written) | `python3 -m unittest test_squadupgrade`
- AC5 | `test_squad_team.py::RespawnListTest::test_team_lead_is_always_on_the_team` | `python3 -m unittest test_squad_team`
- AC6 | `grep -rn "plan-owner" bin/ templates/ agents/ hooks/ skills/`: only `squadrules.py:52`, `squadupgrade.py:85,93` and the changelog; `grep -rn "team-lead = " templates/`: empty; `squad-process lint` exit 0 | repo root
- AC6b | `grep -rn "handin-target = manager" templates/`: empty (only `_removed.md` text); citations `[REV-1]`, `[LC-20a]`, `[ITER-6a]` gone from templates/ bin/ tests/ | repo root
- AC7 | `squad-process who MSG-5`, `who WHO-1e`: no `plan-owner =` or `team-lead =` line | repo root
- AC8 | `test_dev_rules_size.py` (LC-20e, REV-13c), `test_squadcompose.py` and `test_sizes.py` `duties:` assertions | OK
- AC9 | `test_windows_safe`, `test_utf8_helpers`, `test_instructions` | see `## Behaviour`
- AC10 | touched files plus grep hits, 284 tests | see `## Behaviour`

## Behaviour

- Engine: `plan-owner` left `DUTIES`; `handin-target` chain is `qas, team-lead`. `team-lead` moved to `IMPLICIT_ROLES`; `resolve_duties` adds it to every team; `parse_team` skips a `team-lead` token. `OLD_WHEN_KEYS` gained `plan-owner` and `team-lead` with a pointer. `squad-team add|remove team-lead` exits 2 "always on the team". `squad-process upgrade --check` lists `plan-owner = team-lead|manager` and `team-lead = yes|no` (drop the condition / drop the operation); the `team-lead = yes` alternative hint is gone.
- Merge (SQ-6b): 03 (e27e14f) and 04 (218a666) merged first. Conflicts: `_removed.md` kept both tombstone sets; `spawning.md`, `starting.md` took 04's deletions; `test_rules_contract`, `test_rules_wording`, `test_small_files_equivalence` combined (WHO-1a/3a/8a stay removed by 03, START-2a, FILE-5a, PROMO-5b, ITER-3b by 04); `starting.md` cited `[LC-6b]` (gone since v20) -> `[LC-6]`.
- AC6b (Tech Lead ANSWER, ticket updated): tombstoned LC-20a -> LC-20e, REV-1 -> REV-1b, REV-13a -> REV-13c, ITER-6a -> ITER-6b (`removed in v20`). REV-1b now carries REV-1's full text (self-contained). EVID-3a and EVID-9d had no twin for a team without QA, so they are kept and retargeted (`roles: team-lead`, `when: handin-target = team-lead`, heading "Team Lead"). Their hash changed on purpose; no `_removed.md` entry. `spawning.md` and `sizes.md` citations moved to ITER-6b and REV-1b.
- Tests edited: test_squadrules, test_squadupgrade, test_squad_team (synthetic rules on `tech-lead = yes|no`), test_squadcompose, test_sizes, test_team_duties (64 teams, 12 duties), test_rules_contract (counts 64 -> 32), test_rules_wording, test_dev_rules_size, test_small_files_equivalence; rulesview.py docstring.
- Results: `cd tests && python3 -m unittest test_rules_contract test_rules_wording test_sizes test_small_files_equivalence test_squadcompose test_squadrules test_squadupgrade test_team_cli test_team_duties test_squad_team test_dev_rules_size test_windows_safe test_utf8_helpers test_instructions`: 284 tests OK (includes the three SQ-10 files). No test skipped. Full suite not run (Tech Lead's).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squadrules TeamLeadImplicitTest OK | - | - |
| AC2 | test_squadrules TeamLeadImplicitTest, test_team_duties OK | - | - |
| AC3 | test_squadrules old-key test (plan-owner, team-lead rows) OK | - | - |
| AC4 | test_squadupgrade test_removed_team_lead_conditions... OK | - | - |
| AC5 | test_squad_team test_team_lead_is_always_on_the_team OK | - | - |
| AC6 | grep over bin/ templates/ agents/ hooks/ skills/ empty but pointers; lint exit 0 | - | - |
| AC6b | grep `handin-target = manager` templates/ empty; lint exit 0 | - | - |
| AC7 | `squad-process who MSG-5 / WHO-1e`: 0 hits | - | - |
| AC8 | test_dev_rules_size, test_squadcompose, test_sizes OK | - | - |
| AC9 | windows_safe, utf8_helpers, instructions OK | - | - |
| AC10 | 284 targeted tests OK | - | - |
