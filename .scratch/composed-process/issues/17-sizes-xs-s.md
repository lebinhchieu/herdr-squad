Status: needs-info
Type: task
Task ID: 17
Touches: `templates/squad/process/sizes.md`, `templates/squad/process/review.md`, `templates/squad/process/suites.md`, `templates/squad/process/spawning.md`, `bin/squadrules.py` (`size` values add XS), `CLAUDE.md` (Running tests: suite owner), `tests/test_sizes_xs_s.py` (new)
Does not touch: `agents/*` (cards hold no process after 06)
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_sizes_xs_s test_squadrules test_squadcompose`
Blocked by: 03, 04; PO answers to round 1 Q1–Q6 (`../round1-sizes-advisor.html`)

# 17: Sizes XS and S without a Tech Lead

**Done when the size rules define XS (Manager + Developers) and S (Manager + Developers + both QAs), every Tech Lead duty has a named owner in each, and compose output per role matches.**

## PO request (2026-10-21)
- XS: Manager, Developers.
- S: Manager, Developers, QA whitebox, QA blackbox.
- M and L: per round 1 Q5.

## Open until the PO answers round 1 (recommended defaults in brackets)
- Q1 XS done: [Developer checks + `evidence.md` + one fresh-context Opus review subagent before HANDIN; the Manager confirms both exist]
- Q2 planning: [the Manager plans in XS and S, with an exception to "the Manager never does a role's work"; Developers write design notes in the task file]
- Q3 S technical AC and `promote.md`: [QA whitebox; a migration or breaking change is a risk flag, so the scope goes to M]
- Q4 full suite: [S: QA whitebox; XS: the Developer, once on the final sha; the rule becomes "the size's suite owner"]
- Q5 M and L: [unchanged]
- Q6 XS vs S signals: [XS: 1 task, nothing user-visible, no risk flag, covered by existing tests. S: 1–3 tasks, may be user-visible, clear ticket. When unsure, size up]

## Technical AC
1. `size` accepts XS, S, M and L in `when:`; lint rejects other values.
2. For each size, `who` shows an owner for: plan, technical AC, code check, behaviour check, full suite, `promote.md`. A test fails when any duty has no owner at any size.
3. Risk flags still force at least M (rule plus test).
4. `CLAUDE.md` → Running tests names the size's suite owner instead of "only the Tech Lead".
5. Existing scopes recorded as `size: S` (old meaning: Tech Lead + Developers) are listed in the evidence, with the PO's choice of how to read them. Recommended: an open scope keeps its pinned rules (D6), so nothing changes until it closes.
