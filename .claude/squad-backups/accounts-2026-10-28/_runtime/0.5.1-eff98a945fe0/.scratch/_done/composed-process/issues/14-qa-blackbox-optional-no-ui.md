Status: ready-for-agent
Type: task
Task ID: 14
Touches: `templates/squad/process/sizes.md`, `templates/squad/process/review.md`, `templates/squad/process/evidence.md` (variants `when: qa-b = no`), `tests/test_qab_optional.py` (new)
Does not touch: `bin/` (the `qa-b` key is already in 02's grammar and 04's facts), `agents/*`
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_qab_optional test_squadcompose`
Blocked by: 03, 04

# 14: `qa-b: no` for scopes no user can see

**Done when an M or L scope may run without QA blackbox, only when no task changes what a user sees, and the behaviour check moves as it does in S.**

## Why
Review finding 9: refine-process and extractor-role needed hand-built custom pods without QA blackbox, because process and doc changes have no running app to test.

## What
- **Rules:**
  - the Manager may propose `qa-b: no` with that signal, and the PO confirms it at the goal check;
  - a user-visible change found later turns it back to `yes`, and QA blackbox checks what was already built;
  - with `qa-b: no`: the Developer writes `## Behaviour`, QA whitebox checks it, and Done = QA whitebox PASS. These are variants of the existing rules.
- **Spawning rule:** the Manager does not spawn QA blackbox when `qa-b: no`.

## Technical AC
1. Compose at M with `qa-b: no`: qa-blackbox rules are absent from the Manager's spawn list; dev gets the `## Behaviour` variant; qa-whitebox gets the behaviour-check variant (test).
2. Compose at M with no `qa-b` line is unchanged from before this ticket (test against the 03 output).
3. Lint passes.
