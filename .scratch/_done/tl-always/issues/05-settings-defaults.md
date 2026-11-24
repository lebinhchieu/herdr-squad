# 05 Settings defaults
Status: ready
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: templates/squad/settings/manager.json, templates/squad/settings/team-lead.json; tests/test_model_effort_settings.py (extend)
Depends: - (group A, parallel with 01, 03, 04, 06). Goal: `../iterations/1.md`; brief `../scope.md`.
Evidence: .scratch/tl-always/issues/05-settings-defaults/evidence.md

## What and why
manager.json: opus medium. team-lead.json: sonnet low. Tests pin both.

## Design notes (Tech Lead)
The settings live in `templates/squad/settings/` (the bare `settings/manager.json` in the brief is this file); `squad-start` and `squad-spawn` read `model` and `effortLevel` from it with a squad's own `settings/<role>.json` and `scope.md` `model <role>:` lines winning (ADR 0010, 0008). Today: manager `sonnet high`, team-lead `sonnet medium`.
Change two keys, nothing else in either file (permissions, `advisorModel: opus` stay): `manager.json` -> `"model": "opus", "effortLevel": "medium"`; `team-lead.json` -> `"model": "sonnet", "effortLevel": "low"`.
SQ-1: deletes nothing. Readers of the values: `bin/squad-start` (`--dry-run` prints them), `bin/squad-spawn`; no code edit needed. Existing squads with their own `settings/manager.json`/`team-lead.json` keep their old defaults (not touched here; the Manager tells Chieu at check-in; `.claude/squads/*/settings/*.local.json` are overlays, untouched).

Technical AC:
- AC1 `jq -r '.model,.effortLevel' templates/squad/settings/manager.json` prints `opus`, `medium`; `team-lead.json` prints `sonnet`, `low`; `git diff` of the two files shows only those two lines each.
- AC2 One new test row (extend `tests/test_model_effort_settings.py`, which already loops over all ROLES) pins both defaults by role; the test fails if either value is reverted.
- AC3 `squad-start --dry-run` on a scratch squad (as `tests/test_squad_start.py` builds it) reports `opus`/`medium` from `template`; a `squad-spawn team-lead ... --dry-run` reports `sonnet`/`low`. Evidence: the two outputs.
- AC4 Targeted tests: test_model_effort_settings.py, test_squadsettings.py, test_team_models.py, test_squad_start.py, test_templates.py, test_team_lead_perms.py (all hit the settings files); the existing assertions that read the old defaults (grep `--model sonnet --effort medium` rows are for `dev`, leave them) are updated only where they pin manager or team-lead. SQ-10 does not apply (no `bin/` edit). No test newly skipped.
Compatibility (LC-12): none (defaults only; flags, squad settings and `scope.md` lines still win). Rollback = revert the two lines.

## Evidence
`evidence.md` next to the ticket (path in Evidence: line, Tech Lead).
