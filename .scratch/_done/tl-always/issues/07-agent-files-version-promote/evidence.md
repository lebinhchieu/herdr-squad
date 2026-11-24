# 07 Agent files, version 0.10.0, integration: evidence

## Review
AC trace:
- AC1 | `grep -rn "0\.9\.6" .claude-plugin/` (empty); plugin.json 0.10.0; changelog `## v20` | grep, see Behaviour
- AC2 | `python3 bin/squad-process lint` (exit 0); grep `plan-owner` bin/ templates/ agents/ hooks/ skills/ | run in worktree
- AC3 | `python3 bin/squad-process compose manager|team-lead|dev --home <scratch scope, team: tech-lead, qa-white>` | below
- AC4 | `python3 bin/squad-process upgrade --check --squad-dir .claude/squads/<plugin|board|accounts>` | below
- AC5 | `git merge-base --is-ancestor <sha> HEAD` for the six shas; the five 03/04 test files; `_removed.md` tombstones once | below
- AC6 | `grep -n "exist only" agents/team-lead.md` (empty); test_instructions, test_rules_contract | `cd tests; python3 -m unittest ...`
- AC6b | CONTEXT.md line 12 | grep below
- AC6c | `grep -n plan-owner CONTEXT.md docs/adr/0030-*.md` | below
- AC7 | Tech Lead, full run after Chieu's yes (not run here)

Checks: see `## Checks`.

## Behaviour
Integration (SQ-6b): merged in order 03 e27e14f, 04 218a666, 02 f146fcf, 01 35be59b, 05 1580999, 06 7d15752; each is an ancestor of HEAD. Conflicts (03/04: `_removed.md`, spawning.md, starting.md, test_rules_contract, test_rules_wording, test_small_files_equivalence; 02: `_removed.md`, test_rules_contract, test_small_files_equivalence) resolved by hand. No conflict markers (`grep -rn '<<<<<<<'` over bin templates tests agents hooks skills docs CONTEXT.md .scratch/tl-always: none). Ticket files `.scratch/tl-always/issues/NN-*.md` exist once each.

Merge fixes (listed for QA whitebox):
- `_removed.md`: 04's tombstones said `removed in v14`; set to `v20` (the release). Each ID appears once (`grep '^## ' | sort | uniq -d` empty). LC-20c (v9) `replaced_by` LC-20a, which 02 tombstones, now says LC-20b.
- `starting.md` line 74: `[LC-6b]` -> `[LC-6]` (03 removed LC-6b; 04 still cited it). `test_small_files_equivalence.py`: `M/manager` expectation is the IDs still present (`WHO-1a`, `START-2a` etc. are gone); `CHANGED_IDS` is 02's. `test_old_language_inventory.py`: the `bin/squad-log-message` allow line removed (03 dropped the `size:` comment). `tests/squadtest.py` `_build`: stubs for the new `replaced_by` IDs (MSG-4b 7b 8b 11b 19, REV-1b, REV-13c) in the fixture plugin copy, like the existing REV-14a stub.
- Note: the installed runtime's `squad-process lint` (pinned 0.9.5) runs the old rules; the lint and compose below run `python3 bin/squad-process` from this worktree. The old lint did not catch the LC-20c `replaced_by` that compose rejected; the new `lint` (worktree) is clean after the fix.

Tests (from `tests/`, `python3 -B -m unittest ...`): the 03/04 shared five (test_rules_contract test_rules_wording test_architect_handoff test_dev_rules_size test_small_files_equivalence) plus test_squad_log_message test_squad_usage_hook test_model_effort_settings test_sizes test_squad_start test_squad_team test_squad_watchdog test_squadcompose test_squadrules test_squadupgrade test_team_duties; the grep hits for `_removed`/changelog/CONTEXT.md (test_old_language_inventory test_processlint test_templates test_squadruntime test_promotion_0_6_0 test_squadinbox test_squadscaffold test_squadsettings); and the SQ-10 three (test_windows_safe test_utf8_helpers test_instructions): 485 tests OK in the last run, 460 OK in the earlier one. The full suite is not run here (Tech Lead, after Chieu's yes).

### AC3: compose on a team without `team-lead` (`team: tech-lead, qa-white`, no pin)
```
$ python3 bin/squad-process compose manager --home <scratch> --out <scratch>/manager.md  -> exit 0
  grep -c 'plan-owner=' manager.md: 0   duties: duties: design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket,
$ python3 bin/squad-process compose team-lead --home <scratch> --out <scratch>/team-lead.md  -> exit 0
  grep -c 'plan-owner=' team-lead.md: 0   duties: duties: design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket,
$ python3 bin/squad-process compose dev --home <scratch> --out <scratch>/dev.md  -> exit 0
  grep -c 'plan-owner=' dev.md: 0   duties: 
team-lead.md has WHO-1e, LC-15, LC-16, LC-17 in its rules line: WHO-1e LC-15 LC-16 LC-17 
manager.md has the Team Lead rows: 1
```

### AC2: lint and grep
```
lint exit 0
grep plan-owner bin templates agents hooks skills (files): bin/squadupgrade.py bin/squadrules.py skills/squad-process-update/changelog.md 
grep 0.9.6 .claude-plugin/: 0 hits; version:   "version": "0.10.0",
agents/team-lead.md 'exist only': 0
```

### AC6b, AC6c
```
12:The role that runs one scope (a lone task) or one goal (several scopes): proposes the team, owns the plan (which tasks, their order, the iteration goal) and settles disputes. The Manager spawns the pod; the Team Lead spawns and retires only Developers and k
92:The role that owns one duty (business AC, code check, behaviour check, suite run and so on) on a given team: the first present role in that duty's fallback c
grep plan-owner docs/adr/0030-*.md CONTEXT.md: only the history lines:
docs/adr/0030-team-lead-always.md:8:The Team Lead was optional, so every rule that named the plan owner needed
docs/adr/0030-team-lead-always.md:11:- The Team Lead is always on the team. `plan-owner` is no longer a duty o
CONTEXT.md:28:Was the role that owned the plan, a Team Lead or, without one, the Manager (the `plan-owner` dut
```

### AC4: upgrade --check (worktree engine, 0.10.0)
```
### plugin
upgrade: plugin 0.9.5 804c29c77df36798f9c3aafb9906746cd4efd353 -> 0.10.0 a3d085cf41b45d6e8258200a27b74dd440e244af
plugin changes: added 1, changed 30, removed 35, retargeted 32
overlay: 19 operations: 19 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
review (not blocking):
  SQ-3b (topic cost): the plugin changed COST-13b Nothing left to do, Team Lead plans
  SQ-3c (topic cost): the plugin changed COST-13b Nothing left to do, Team Lead plans
  SQ-10 (topic review): the plugin changed REV-1b Confirmation, Team Lead
  SQ-10 (topic review): the plugin changed REV-14a Diff check
  SQ-3d (topic cost): the plugin changed COST-13b Nothing left to do, Team Lead plans
  SQ-14 (topic cost): the plugin changed COST-13b Nothing left to do, Team Lead plans
nothing needs a decision.
exit 0
### board
upgrade: plugin 0.6.7 67d3543eecb12a8f0683bfe0f5896cc867d78ed3 -> 0.10.0 a3d085cf41b45d6e8258200a27b74dd440e244af
plugin changes: added 12, changed 98, removed 38, retargeted 32
overlay: 9 operations: 9 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
review (not blocking):
exit 0
### accounts
upgrade: plugin 0.7.6 c41d76a9c2ca617318d984e8857e93f417fdd46a -> 0.10.0 a3d085cf41b45d6e8258200a27b74dd440e244af
plugin changes: added 11, changed 72, removed 38, retargeted 37
overlay: 0 operations: 0 unaffected, 0 re-targeted, 0 dropped, 0 need a decision
nothing needs a decision.
exit 0
```
Each squad ends `nothing needs a decision`; the plugin squad overlay: 19 operations, 0 need a decision (no COST-5a citation note appeared; the review lines are non-blocking). The `SQ-n ... plugin changed` lines of the board squad are non-blocking review lines, left out above.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | grep 0.9.6 in .claude-plugin/ empty; evidence Behaviour | `grep -rn 0.9.6 .claude-plugin/` empty; plugin.json 0.10.0; changelog v20 read | - |
| AC2 | `python3 bin/squad-process lint` exit 0; grep plan-owner | lint exit 0; grep plan-owner: only squadrules.py:52, squadupgrade.py:85,93 and changelog | - |
| AC3 | compose manager/team-lead/dev, evidence AC3 | compose x3 on `team: tech-lead` scratch scope: rc 0, no `plan-owner` in output | - |
| AC4 | upgrade --check x3, evidence AC4 | run by me on plugin, board, accounts: rc 0, 0 need a decision each | - |
| AC5 | is-ancestor x6; five shared test files OK; uniq -d empty | is-ancestor 01,02,04,05,06 true; 03 e27e14f true (tip 639e0c9 superseded per Tech Lead); no `## ` duplicates, no conflict markers in _removed.md; 530 tests OK | - |
| AC6 | test_instructions, test_rules_contract OK | no "exist only when" in agents/team-lead.md; both files OK at 24bbb35 | - |
| AC6b | CONTEXT.md line 12 | line 12 read: Team Lead spawns and retires only Developers | - |
| AC6c | grep plan-owner CONTEXT.md | Duty owner entry has no plan duty; plan-owner left only in the retired "Plan owner" entry and ADR 0030 history | - |
| AC7 | Tech Lead (full run) | not mine (Tech Lead) | - |

## QA whitebox

### QA whitebox 07, sha 24bbb35 (c2826ff plus a one-line frontmatter fix)

Checks per AC: see `checks.md` (my column).
- Tests: 17 changed test files plus test_squadruntime, test_instructions, test_windows_safe, test_utf8_helpers: 530 OK at c2826ff; test_instructions and test_rules_contract 33 OK again at 24bbb35 (only agents/team-lead.md changed).
- Real samples (REV-4): `upgrade --check` on plugin (0.9.5), board (0.6.7), accounts (0.7.6) squads: rc 0, "0 need a decision", nothing written.
- Agent cards: team-lead.md body and (after 24bbb35) description no longer say it owns the plan or exists only when listed; manager.md owns the plan, points to SPAWN-12.
- Integration: 01, 02, 04, 05, 06 are ancestors; 03 at e27e14f (final per Tech Lead; the branch tip 639e0c9 is the superseded ticket-copy drop).
PASS.

#### Follow-ups (not FAIL)
- `squad-evidence checks evidence.md` exits 1 until my column is added to the `## Checks` table (empty QA whitebox cells at evidence.md:90-98). My column is in `$SCOPE_DIR/evidence/07/checks.md`; the Developer's `squad-evidence add` copies it. AC7 stays the Tech Lead's.
- AC6c: `plan-owner` still appears in CONTEXT.md:28 and ADR 0030 as retirement history; the ticket's intent (no plan duty in Duty owner) holds.
- squad overlay rules SQ-6 and SQ-6b still say "plan owner" (this repo's own overlay, not the plugin); the Manager edits it.

## QA blackbox

### 07 QA blackbox (sha c2826ff)
Worktree .worktrees/plugin/tl-always/plugin-dev-tl-always-07, live runs, scratch squads removed.

| QA-b AC | how | saw | result |
|---|---|---|---|
| QA-b AC1 | live: grep 0.9.6 in .claude-plugin; plugin.json; changelog | no 0.9.6, version 0.10.0, v20 with added/changed/removed + Deploy | pass |
| QA-b AC2 | live: `squad-process lint` (0); grep plan-owner bin templates agents hooks skills | lint 0; only squadupgrade.py:85,93, squadrules.py:52 (pointers) | pass |
| QA-b AC3 | live: compose manager, team-lead, dev on scratch `team: tech-lead, qa-white` | 0 `plan-owner=`, 0 "plan owner"; Team Lead text "never reorders the plan"; Manager text has SPAWN-12 and the plan/dispute rules | pass |
| QA-b AC4 | live: `upgrade --check` plugin / board / accounts | all exit 0, "nothing needs a decision" | pass |
| QA-b AC5 | live: 292 tests (rules_contract, wording, architect_handoff, dev_rules_size, small_files_equivalence, instructions, windows_safe, utf8_helpers, upgrade, rules, compose, squad_team, sizes, log_message) | OK; `_removed.md`: no conflict markers, no duplicate heading | pass |
| QA-b AC6 | live: grep "exist only or only when" agents/team-lead.md | none; body says "You are always on the team ... never reorders" | pass for the literal AC |
| AC6b/AC6c | live: read CONTEXT.md Manager and Duty owner | Manager: "The Manager spawns the pod; the Team Lead spawns and retires only Developers"; Duty owner has no plan | pass |
| What ("Agent files match the new roles") | live: read agents/team-lead.md line 3 | frontmatter `description:` still says "Owns the delivery plan, task order and assignment for one scope." | FAIL |

#### Re-check sha 24bbb35 (changed file: agents/team-lead.md only)
| What | how | saw | result |
|---|---|---|---|
| Agent files match new roles | live: read line 3 | description: "Coordinates the pod for one scope: spawns and retires Developers, assigns tasks per the Manager's plan, tracks, runs health checks"; no "Owns the delivery plan" | pass |
| Re-check AC2 | live: `squad-process lint` | exit 0 | pass |
| Re-check AC3 | live: compose manager/team-lead/dev on scratch squad | 0 "plan owner"/"plan-owner" in each | pass |
| Re-check AC4 | live: `upgrade --check` plugin/board/accounts | exit 0 each, "nothing needs a decision" | pass |
| Tests | test_rules_wording, test_rules_contract | see run | pass |
