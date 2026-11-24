# 07 Designer settings test expects the /tmp allow

Status: ready-for-agent (draft by the Tech Lead, 2026-11-24; the Developer commits it as `.scratch/upstream-proposals/issues/07-designer-tmp-test.md`, FILE-11)

Spec: `.scratch/upstream-proposals/spec.md`. Base: the 06 branch at 39039b3.

## Problem

`tests/test_templates.py::TemplateLayersTest::test_designer_may_write_only_ui_design_files` fails on main (c853707 and on the 06 branch). Commit bd2563c ("Allow every role to work anywhere under /tmp", plugin 0.10.6) added `Read(//tmp/**)`, `Edit(//tmp/**)` and `Write(//tmp/**)` to `templates/squad/settings/designer.json`. It updated the architect test (`tests/test_architect_handoff.py:29` lists `Edit(//tmp/**)`) and `test_squadsettings.py::test_every_role_works_anywhere_in_tmp`, but not the designer test. The test is stale; the settings are right.

## Decision (Tech Lead)

Change the test, never the designer settings. Why: bd2563c is the PO's intent (every role works under /tmp), `test_every_role_works_anywhere_in_tmp` asserts it for every settings file including `designer.json`, and the architect test already lists the /tmp entries the same way. Making the designer settings drop them would break that test and SAFE-11. The designer's real limit (write `ui-design/` only inside the squad folders, deny the rest of `.claude/squads/`) is kept: the test still lists the two ui-design entries and the deny checks.

## Change

In `test_designer_may_write_only_ui_design_files`, the sorted list of `Write(`/`Edit(` allows must equal:
`Edit(//tmp/**)`, `Edit(/.claude/squads/*/scopes/*/ui-design/**)`, `Write(//tmp/**)`, `Write(/.claude/squads/*/scopes/*/ui-design/**)`.
Rename nothing; add a comment: "/tmp is open to every role (bd2563c, SAFE-11)". Keep every other assertion in the test.

## Files (LC-9)

- `tests/test_templates.py` only (about 4 lines). No rule, no `templates/`, no `bin/`, no version, no changelog entry (06 already carries the bump and changelog; this ticket touches no plugin file). No `LIMIT` change.
- Harness: `tests/test_templates.py`; readers of the same settings file: `tests/test_squadsettings.py`, `tests/test_architect_handoff.py`, `tests/test_team_lead_perms.py`.

## AC

- AC1: `python3 -m unittest test_templates` (from `tests/`) passes, 8 tests, none skipped or deleted.
- AC2: the test still fails if `designer.json` gains any `Write(`/`Edit(` allow other than the four above (the Developer shows this once: add a throwaway entry in a scratch copy under `/tmp`, run, remove it; quote the failure line; never commit it).
- AC3: `git diff 39039b3 HEAD --stat` lists `tests/test_templates.py` and this ticket's evidence only, no `templates/squad/settings/` file.
- AC4: targeted tests pass: `test_templates`, `test_squadsettings`, `test_architect_handoff`, `test_team_lead_perms` plus every hit of `grep -rl 'designer' tests/*.py`; the three SQ-10 files are not required (no `bin/`, no printed text, no role-attached text), but quote them if run.
- AC5: no rule text changes, so `python3 bin/squad-process lint` is unchanged: exit 0.

## Duties

Evidence: `.scratch/upstream-proposals/issues/07-designer-tmp-test/evidence.md` (Behaviour: the AC1 and AC2 output). Hand in to both QAs. After 07 passes, the Tech Lead sets the `base-failures.md` row to "fixed by 07"; the full `--tz` run then goes on 07's final sha and must have no failure.

## Comments
- 2026-11-24 Developer: taking the ticket; test-only change, designer.json untouched.
- 2026-11-24 Developer: the ticket's list order was not the sorted order ('.' sorts before '/'); the same four entries are listed in sorted order.
