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
- AC11 | `test_squadupgrade.py::OldWhenLanguage::test_old_root_keeps_removed_when_keys_as_text`; real sample in `## Behaviour` | `python3 -m unittest test_squadupgrade`
- AC10 | touched files plus grep hits, 284 tests | see `## Behaviour`

## Behaviour

- Engine: `plan-owner` left `DUTIES`; `handin-target` chain is `qas, team-lead`. `team-lead` moved to `IMPLICIT_ROLES`; `resolve_duties` adds it to every team; `parse_team` skips a `team-lead` token. `OLD_WHEN_KEYS` gained `plan-owner` and `team-lead` with a pointer. `squad-team add|remove team-lead` exits 2 "always on the team". `squad-process upgrade --check` lists `plan-owner = team-lead|manager` and `team-lead = yes|no` (drop the condition / drop the operation); the `team-lead = yes` alternative hint is gone.
- Merge (SQ-6b): 03 (e27e14f) and 04 (218a666) merged first. Conflicts: `_removed.md` kept both tombstone sets; `spawning.md`, `starting.md` took 04's deletions; `test_rules_contract`, `test_rules_wording`, `test_small_files_equivalence` combined (WHO-1a/3a/8a stay removed by 03, START-2a, FILE-5a, PROMO-5b, ITER-3b by 04); `starting.md` cited `[LC-6b]` (gone since v20) -> `[LC-6]`.
- AC6b (Tech Lead ANSWER, ticket updated): tombstoned LC-20a -> LC-20e, REV-1 -> REV-1b, REV-13a -> REV-13c, ITER-6a -> ITER-6b (`removed in v20`). REV-1b now carries REV-1's full text (self-contained). EVID-3a and EVID-9d had no twin for a team without QA, so they are kept and retargeted (`roles: team-lead`, `when: handin-target = team-lead`, heading "Team Lead"). Their hash changed on purpose; no `_removed.md` entry. `spawning.md` and `sizes.md` citations moved to ITER-6b and REV-1b.
- Tests edited: test_squadrules, test_squadupgrade, test_squad_team (synthetic rules on `tech-lead = yes|no`), test_squadcompose, test_sizes, test_team_duties (64 teams, 12 duties), test_rules_contract (counts 64 -> 32), test_rules_wording, test_dev_rules_size, test_small_files_equivalence; rulesview.py docstring.
- Results: `cd tests && python3 -m unittest test_rules_contract test_rules_wording test_sizes test_small_files_equivalence test_squadcompose test_squadrules test_squadupgrade test_team_cli test_team_duties test_squad_team test_dev_rules_size test_windows_safe test_utf8_helpers test_instructions`: 284 tests OK (includes the three SQ-10 files). No test skipped. Full suite not run (Tech Lead's).
- AC11 (return): `squadupgrade.load_plugin(root, old=True)` loads the pinned OLD root with `sr.load_rules(..., old_root=True)`: a rule's `when:` stays text, unchecked. The new root and `squad-process lint` stay strict (test asserts `UpgradeError` without `old=True`). Real sample, `python3 bin/squad-process upgrade --check --squad-dir <repo>/.claude/squads/plugin` (pin 0.9.5 804c29c, pinned runtime as old root), exit 0 (was 2 with 79 lines):

```
upgrade: plugin 0.9.5 804c29c77df36798f9c3aafb9906746cd4efd353 -> 0.9.6 6f968003c33933b30d16ae0eefad92a999a4244b
plugin changes: added 1, changed 30, removed 35, retargeted 32
overlay: 19 operations: 19 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
review (not blocking):
  SQ-2 (topic review): the plugin changed REV-1b Confirmation, Team Lead
  ... (10 more review lines)
nothing needs a decision.
```
Targeted run after the fix: `cd tests && python3 -m unittest test_squadupgrade test_squadrules test_squadcompose test_squad_team test_sizes test_rules_contract test_windows_safe test_utf8_helpers test_instructions`: 216 tests OK.

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
| AC11 | test_squadupgrade test_old_root_keeps_removed_when_keys_as_text OK; real sample exit 0 | - | - |
| AC10 | 284 targeted tests OK | - | - |

## QA whitebox

### QA whitebox 02, sha 6f96800 (03 e27e14f and 04 218a666 merged in)

Read: bin diff (squadrules, squadcompose, squadteam, squadrules_cli, squadupgrade, squad-log-message, squad-usage-hook), templates (_removed.md, evidence.md, review.md), tests.

| AC | how I checked | result |
|---|---|---|
| AC1 | python: parse_team("ba, team-lead") == parse_team("ba"); team_facts equal; no team-lead/plan-owner key | pass |
| AC2 | resolve_duties([]) has no plan-owner; handin-target team-lead (no QA), qas (with qa-white) | pass |
| AC3 | OLD_WHEN_KEYS pointers; test_squadrules.py:197 covers the lint reject | pass (tests green) |
| AC4 | test_squadupgrade.py:190 loops the four old conditions, exit 3, snapshot unchanged | pass |
| AC5 | live on tmp scope.md: `squad-team add/remove team-lead` exit 2 "always on the team"; `add ba` on `team-lead, qa-white` writes `team: ba, qa-white`, `spawn: ba`, no spawn/retire for team-lead | pass |
| AC6 | grep plan-owner in bin/ templates/ agents/ hooks/ skills/: only squadrules.py:52, squadupgrade.py:85,93 and changelog.md history; `grep "team-lead = " templates/` empty; `squad-process lint` exit 0 | pass |
| AC6b | `handin-target = manager` grep empty (templates, bin, hooks, agents). LC-20a, REV-1, REV-13a, ITER-6a tombstoned (v20, why, replaced_by LC-20e, REV-1b, REV-13c, ITER-6b). EVID-3a, EVID-9d kept and retargeted to team-lead per the Tech Lead's later ANSWER (2 of the six: no twin, text would be lost); REV-1b self-contained, no `[REV-1]` citation left in templates/bin/hooks/agents | pass (as amended by the Tech Lead ANSWER) |
| AC7-AC8 | covered by test_rules_contract, test_dev_rules_size, test_sizes, test_squadcompose, green | pass |
| AC9 | test_windows_safe, test_utf8_helpers, test_instructions in the 284 run | pass |
| AC10 | Dev's 14 files + grep hits (all 8 hit files are within them, test_architect_handoff too): 284 OK. Also ran test_squad_log_message, test_squad_usage_hook, test_architect_handoff (touched by the diff): 48 OK | pass |

`squad-evidence checks` on evidence.md: exit 0.

PASS.

#### Follow-ups (not FAIL)
- bin/squad-log-message and bin/squad-usage-hook are edited (plan-owner readers dropped) though neither is in the ticket's Files line or the Tech Lead's "no reader" note; the edits are correct and their tests pass. Tech Lead to record in the ticket.
- The scratch line "squad-team: scope.md not changed: disk full" in test output is a test's expected stderr, not a failure.
- `squad-evidence check --base HEAD~1` needs the ticket file on the branch (Dev's note); expected, per 03.

## QA blackbox

### 02 QA blackbox (sha 6f96800)
Worktree .worktrees/plugin/tl-always/plugin-dev-tl-always-02; scratch squads in mktemp (removed after).

| AC | how | saw | result |
|---|---|---|---|
| AC1/AC2 | live: unit tests test_squadrules, test_squadcompose (224 tests OK); compose dev on `team: tech-lead` | rules list has HANDIN to the Team Lead, REV-13c, LC-20e; no plan-owner text | pass |
| AC3 | live: scratch overlay with `when: plan-owner = team-lead`, `= manager`, `team-lead = no`, `= yes`; `squad-process lint --squad-dir` | `process.local.md:<line>: MSG-6: when key 'plan-owner' is gone ...` with pointer, exit 1; repo templates `lint` exit 0 | pass |
| AC4 | live: `squad-process upgrade --check` with an add-only overlay of the four old conditions, old root = parseable tree | each op printed `LOC-n (line N): <old> -> <translation>`; file unchanged (cmp); exit 2 | pass |
| AC5 | live: `squad-team add/remove team-lead` on scratch scope; `add ba` on `team: team-lead, qa-white` | both exit 2 "always on the team"; `add ba` wrote `team: ba, qa-white`, report lists `spawn: ba`, never team-lead as spawn/retire | pass |
| AC6 | live: grep plan-owner in bin templates agents hooks skills; grep `team-lead = ` / `handin-target = manager` in templates | only squadupgrade.py:85,93 and squadrules.py:52 (pointers); others empty; lint rc 0 | pass |
| AC6b | live: grep tombstones | LC-20a, REV-1, REV-13a, ITER-6a tombstoned v20; EVID-3a, EVID-9d kept (per corrected AC) | pass |
| AC7 | live: `squad-process who MSG-5` / `WHO-1e` | print nothing (no conditioned variants, so no plan-owner/team-lead keys) | pass |
| AC8/AC9/AC10 | live: unittest test_squadrules, _squadcompose, _sizes, _squad_team, _squadupgrade, _rules_contract, _dev_rules_size, _windows_safe, _utf8_helpers, _instructions | 224 tests OK | pass |

#### Follow-up found (not a written AC of 02)
`squad-process upgrade --check --squad-dir .claude/squads/plugin` (pin 0.9.5, the real squad) now exits 2 with 79 lines: the 0.9.x rule files in the old root carry `plan-owner` / `handin-target = manager` and the new engine rejects them while reading the old root, so no overlay listing is printed. Same failure on the base engine for a `size =` old rule, so it is the existing behaviour from 0018, not new. But ADR 0030 says upgrade --check lists the stale ops, and ticket 07 AC4 expects this command to run on the plugin squad. Needs a decision before 07.
