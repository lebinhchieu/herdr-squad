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
| AC1 | grep 0.9.6 in .claude-plugin/ empty; evidence Behaviour | | - |
| AC2 | `python3 bin/squad-process lint` exit 0; grep plan-owner | | - |
| AC3 | compose manager/team-lead/dev, evidence AC3 | | - |
| AC4 | upgrade --check x3, evidence AC4 | | - |
| AC5 | is-ancestor x6; five shared test files OK; uniq -d empty | | - |
| AC6 | test_instructions, test_rules_contract OK | | - |
| AC6b | CONTEXT.md line 12 | | - |
| AC6c | grep plan-owner CONTEXT.md | | - |
| AC7 | Tech Lead (full run) | | - |
