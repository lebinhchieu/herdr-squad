# 02 Process rules, Manager text, `design:` line in the scope template

Status: ready-for-agent
Blocked by: none
Task ID: UXD-02

**The squad's rules say when the Designer joins, what it delivers, where the design lives and who checks the build against it.** Spec: `.scratch/ui-ux-design-role/spec.md` (all decisions).

## Files (only these)

- `templates/squad/process.md`
- `agents/manager.md`
- `templates/scope/scope.md`
- `templates/squad/project.md`
- `tests/test_instructions.py`

## What to change

- **`templates/squad/process.md`** (small edits, keep the file's style):
  - Reading table: a row `UI/UX Designer | the UI tasks and their AC, the UI conventions row of project.md, this file's Messages, Cost rules, Safety`.
  - Files table and the folder tree: `ui-design/<task>.md` (`.html` optional), owner Designer, "the design of one UI task".
  - Names: add `ux` to the role-short list; Lifetimes table: Designer, one session per scope, retired once every design is final.
  - Sizes: after the table, a short `design:` paragraph: line in `scope.md`, `yes|no`, default `no`, adds the Designer to a size S, M or L scope; **set by the Manager only when the PO asks; the Manager never proposes it**; the PO's answer is logged in the iteration file.
  - Duty table: two new rows, `UI/UX design (only when design: yes)`: S, M, L = Designer (no `design: yes` = none, the ticket as written); `Built UI vs the design`: S = Developer screenshots each screen/state in `dev-evidence.md`, Tech Lead checks; M, L = QA blackbox.
  - Task lifecycle: a UI ticket with a `Design:` line does not leave `ready` until its design is `Status: final`.
  - Who decides: row `UI design (screens, states, flows)` | Designer | Manager | n/a.
- **`agents/manager.md`:** `designer` in the roles list and `ux` in the names list; one bullet: spawn the Designer only when `scope.md` has `design: yes`, never suggest it, spawn it after the Tech Lead's plan names the UI tasks and before their Developers, retire it per the Lifetimes row.
- **`templates/scope/scope.md`:** add the line `design: no` right after `qa: full`. Do not add a `{{placeholder}}` (a test limits placeholders to `name`, `brief`, `touches`, `goal`).
- **`templates/squad/project.md`:** add a row `UI conventions / design system | <style guide, component folder, palette file; or none>` (what the Designer reuses).
- **`tests/test_instructions.py`:** add tests that (a) `process.md` mentions `design: yes`, `ui-design/` and `ux`, (b) `scope.md` template has the line `design: no`, (c) `manager.md` lists `designer`.

## AC

1. Each bullet above is present; wording short, no new section longer than a paragraph or table row.
2. `squad-start` still creates a scope folder from the template (`tests/test_squad_start.py` and `tests/test_templates.py` unchanged and green) and the new `design: no` line is in it.
3. Existing tests in `tests/test_instructions.py` stay green: no stale token (`XL`, `scopes.md`, ...) is introduced.
4. Statements in the three files agree with the spec: Manager never proposes `design: yes`; the Designer delivers a design only and does not check the build.
5. Full suite green, receipt saved in `$SCOPE_DIR/evidence/UXD-02/`.

## Technical notes

- Do not edit `.claude/squads/squad-board/process.md` (the live copy): the Manager syncs it after the PO merges (spec, Compatibility).
- Do not touch `agents/designer.md`, `bin/`, other role files or the other test files: tickets 01 and 03 own them.
- Hand in: `HANDIN UXD-02: ...` to the Tech Lead with `dev-evidence.md` (diff stat, suite output).
