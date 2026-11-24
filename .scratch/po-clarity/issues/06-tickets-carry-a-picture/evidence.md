# Evidence 06

## Behaviour

Rule `LC-9c` (manager, tech-lead, ba, architect; no `when:`, so `squad-process who LC-9c` prints no lines, it is unconditional). New `templates/squad/ticket.md`, changelog v29 entry, no version bump (rides 05).

- `python3 bin/squad-process lint` → exit 0 (first draft failed the 60-word limit; shortened).
- `sc.find_rule(..., 'LC-9c').roles` → `['manager', 'tech-lead', 'ba', 'architect']`.
- `cd tests && python3 -m unittest test_processlint test_instructions test_rules_wording test_windows_safe test_utf8_helpers` → Ran 105 tests, OK (SQ-10 trio included).
- Template has Problem / Change / AC / Comments, plus `Aim:`, `Estimate:`, `Depends on:`; the rule names it.

## QA whitebox

### QA whitebox, ticket 06 (rule + template), sha 6bab9f1

Verdict: PASS. Diff vs `5c0d5cd`: LC-9c in `templates/squad/process/lifecycle.md`, new `templates/squad/ticket.md`, changelog v29, ticket Duties/Files lines. No version file touched (rides 05).
Ran (detached worktree): `squad-process lint` exit 0; test_processlint, test_instructions, test_rules_wording, test_windows_safe, test_utf8_helpers, plus the files that read templates and rules (test_templates, test_rules_contract, test_squadrules, test_team_duties, test_architect_handoff, test_promotion_0_6_0): 211 run, 1 red. LC-9c roles load as manager, tech-lead, ba, architect (T06-1).
Template has Problem / Change / AC / Comments plus `Aim:`, `Estimate:`, `Depends on:` (T06-4); one changelog entry, no bump (T06-6).

#### Follow-ups (not FAIL)
1. Base failure, same on `5c0d5cd`: `test_templates.TemplateLayersTest.test_designer_may_write_only_ui_design_files` (an extra `Edit(//tmp/**)` allow in the designer settings). Not caused by 06. SQ-17 grep over `_done` iterations: 0 hits; Tech Lead to list it as "Known failing on base".
2. `squad-process who LC-9c` prints nothing (no `when:`, so unconditional); the technical AC line T06-1 expected it to list the roles. Roles verified through `load_rules` instead.
3. The ticket's AC2/AC3 moved to ticket 07 (Manager split); not judged here.

## QA blackbox

### QA blackbox, task 06: tickets carry a picture (sha 6bab9f1)

Scope of 06 after the Manager's split (iterations/1.md, Decisions "FINAL 06 split"): AC1 (lint, rule attaches to four roles), AC4 (changelog, no bump). AC2 (board render) and AC3 (renderMd tests) moved to ticket 07. No screen to walk (ui-design/06.md: none).

| AC | live | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 lint | live | `python3 bin/squad-process lint` in the Developer's worktree | exit 0 | pass |
| AC1 attaches to four roles | live | `squad-process compose <role> --home <scope> --out /tmp/...` for manager, tech-lead, ba, architect, qa-blackbox, qa-whitebox, team-lead, designer; counted `## LC-9c` | present in manager, tech-lead, ba, architect (1 each); absent in the other four | pass |
| Rule text | live | `squad-process rule LC-9c` | picture when the change has a shape, five forms named (wireframe, `diagram` fence max 44 cols, table, before/after, none for rule/test fix); Problem max 3 sentences plus picture; points at `templates/squad/ticket.md` | pass |
| Template | live | read `templates/squad/ticket.md` | sections Problem (picture hint) / Change / AC / Comments; header has `Aim:` (60 chars, no bare IDs), `Estimate:`, `Depends on:` (the 04 AC5 lines) | pass |
| AC4 | live | read changelog diff, diff stat | v29 entry with why lines and deploy/rollback; no plugin version file touched; says the bump rides 05 | pass (bump moved to 05 by the Manager) |

#### Follow-ups (not FAILs)
- Changelog v29 is the next number on this base; upstream-proposals also adds changelog entries, so the number may collide at merge ([SQ-7]).
- The rule shortens the ticket's five-row table into one sentence; the table itself lives only in the template comment.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 bin/squad-process lint` exit 0; `find_rule('LC-9c').roles` = manager, tech-lead, ba, architect | `python3 bin/squad-process lint` (exit 0); `load_rules(templates/squad/process)` LC-9c roles = manager, tech-lead, ba, architect; `cd tests; python3 -m unittest -q test_processlint test_instructions test_rules_wording test_templates test_rules_contract test_squadrules test_team_duties` | `python3 bin/squad-process lint` exit 0; `squad-process compose <role> --home <scope> --out /tmp/x` for 8 roles: LC-9c only in manager, tech-lead, ba, architect. qa-b.md rows AC1 |
| AC4 | `skills/squad-process-update/changelog.md` v29 entry, no version file touched; 105 tests OK (processlint, instructions, rules_wording, windows_safe, utf8_helpers) | `git diff 5c0d5cd 6bab9f1 --stat` touches no version file; `grep -n '^## v29' skills/squad-process-update/changelog.md` | read changelog diff and `git diff --stat`: v29 entry present, no version file touched. qa-b.md row AC4 |
| Template | `grep -c '^## ' templates/squad/ticket.md` = 4 sections and `Aim:`/`Estimate:`/`Depends on:` lines present | `sed -n 1,27p templates/squad/ticket.md`; rule LC-9c names it | - |
