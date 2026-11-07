# 17 foundation (technical task, no business AC)
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs; never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: -
Feature: shared helpers (`architecture.md` M0)

## What the PO gets
Nothing visible. The shared helpers every board reader uses, built once first, so the readers can run in parallel.

## Rules
- Three helpers: `squadboard_time.py` (ISO string in, epoch out, offset aware), `squadboard_git.py` (the git calls: worktree list, branch refs, last commit time; a missing `git` returns unknown, never raises), `squadtickets.py` (the ticket folder finder, moved out of `squadreport_tasks.py` `_find_tickets`; `squadreport_tasks.py` imports it, behaviour unchanged).
- Python stdlib only; `pathlib`; no `fcntl` (ADR 0011).
- Technical AC (QA whitebox writes the final list): `test_squadreport_tasks.py` still passes unchanged; each helper has one test file; a missing `git` or ticket folder gives an `unknown` value, not an exception.
- Business AC: none (QA blackbox: "no observable change").

## Touched files
Module M0.
- New: `bin/squadboard_time.py`, `bin/squadboard_git.py`, `bin/squadtickets.py`.
- Edit: `bin/squadreport_tasks.py` (import `squadtickets`).
- Tests (new): `tests/test_squadboard_time.py`, `tests/test_squadboard_git.py`, `tests/test_squadtickets.py`; `tests/test_squadreport_tasks.py` must still pass.

## Comments
