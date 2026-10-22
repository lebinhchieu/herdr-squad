# 03 Hand-off lines in the Developer, QA blackbox and Tech Lead roles, README

Status: ready-for-agent
Blocked by: none
Task ID: UXD-03

**The roles that consume a design know where it is and what to do with it.** Spec: `.scratch/ui-ux-design-role/spec.md` (decisions 1-4).

## Files (only these)

- `agents/dev.md`
- `agents/qa-blackbox.md`
- `agents/tech-lead.md`
- `README.md`
- `tests/test_designer_handoff.py` (new)

## What to change (one or two lines per role, in the file's own style)

- **`agents/dev.md`:** if the ticket has a `Design:` line, read `$SCOPE_DIR/ui-design/<task>.md` (and the `.html` prototype if present) before building the UI; do not start the UI part while its `Status:` is not `final`; build every screen and state in it. In an S scope, save in `dev-evidence.md` one screenshot per screen and state next to the design item it answers; a difference from the design is an `ASK` to the Tech Lead, not a silent choice.
- **`agents/qa-blackbox.md`:** in the reading step add `$SCOPE_DIR/ui-design/<task>.md` when the ticket cites it; walk every screen and state of the design on the running app; a difference is a FAIL like any AC miss. (Designs are not code: this does not break "stay blind to the code".)
- **`agents/tech-lead.md`:** when `scope.md` has `design: yes`: plan the UI tasks to start after their design is final; put `Design: ui-design/<task>.md` and the AC "built UI matches the design: every screen and state" in each UI ticket; answer the Designer's feasibility `ASK`s; in S, check the Developer's screenshots against the design in `tl-review.md`; write any business doubt the Designer raises to `escalations.md`.
- **`README.md`:** the role list in the first paragraph gets "an optional UI/UX Designer (only when the PO sets `design: yes`)"; the line `The 8 role definitions` becomes 9; one sentence under the roles/size description saying what the Designer delivers (a design before build, no post-build check).
- **`tests/test_designer_handoff.py`:** a new test file; assert that `dev.md`, `qa-blackbox.md` and `tech-lead.md` each mention `ui-design/`, that `tech-lead.md` mentions `design: yes`, and that `README.md` says 9 role definitions and mentions the Designer.

## AC

1. Each bullet above is present in the named file and nowhere else.
2. No other line of `dev.md`, `qa-blackbox.md`, `tech-lead.md` changes (surgical).
3. `tests/test_instructions.py` (unchanged by you) and the new test file are green; full suite green, receipt in `$SCOPE_DIR/evidence/UXD-03/`.
4. The role files agree with the spec: the Designer never checks the built UI; S check = Developer screenshots + Tech Lead; M, L check = QA blackbox.

## Technical notes

- Do not edit `CONTEXT.md` (ticket 05 promotes the glossary term), `process.md`, `agents/designer.md`, `agents/manager.md`, `bin/` or other tests.
- Hand in: `HANDIN UXD-03: ...` to the Tech Lead with `dev-evidence.md` (diff stat, suite output).
