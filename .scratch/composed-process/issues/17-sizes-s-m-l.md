Status: ready-for-agent
Type: task
Task ID: 17
Touches: `templates/squad/process/sizes.md`, `templates/squad/process/review.md`, `templates/squad/process/suites.md`, `templates/squad/process/spawning.md`, `CLAUDE.md` (Running tests: suite owner), `tests/test_sizes.py` (new)
Does not touch: `agents/*` (cards hold no process after 06), `bin/squadrules.py` (`size` stays S, M, L)
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_sizes test_squadrules test_squadcompose`
Blocked by: 03, 04

# 17: New sizes: S = Manager + Developers, M = + both QAs, L = every role

**Done when the size rules define the three new sizes, every Tech Lead, Team Lead and BA duty has a named owner at each size, and compose output per role and size matches.**

## PO request (2026-10-21, updated: no XS)
| Size | Roles |
|---|---|
| S | Manager, Developers |
| M | Manager, Developers, QA whitebox, QA blackbox |
| L | Manager, BA, Team Lead, Tech Lead, QA whitebox, QA blackbox, Developers |

The Designer still joins any size only with `design: yes`.

## PO decisions (round 1, 2026-10-22): spec D9-D14
- **S done:** the Developer's checks + `evidence.md` + one fresh-context Opus review subagent before HANDIN (its output goes in `evidence.md` under `## Review`). The Manager only confirms both exist.
- **S and M:** the Manager plans and spawns Developers (an exception to "never does a role's work"). Developers write design notes in the task file.
- **M:** QA whitebox writes the technical AC (agreed with the Developer) and keeps `promote.md`. Business AC = the ticket as written, tested by QA blackbox. A business doubt moves the scope to L. **S:** the Developer keeps `promote.md`.
- **Full suite:** S the Developer, M QA whitebox, L the Tech Lead, once on the final sha. "The size's suite owner" replaces "only the Tech Lead".
- **Every risk flag forces L.**
- **Signals:** as spec D14.

## Technical AC
1. For each size, `who` shows an owner for: plan and Developer spawning, technical AC, business AC, code check, behaviour check, full suite, `promote.md`, migrations. A test fails when any duty has no owner at any size.
2. Risk flags force the size Q5 names (rule plus test).
3. `CLAUDE.md` → Running tests names the size's suite owner instead of "only the Tech Lead".
4. Team Lead rules carry `when: size = L`. Every Team Lead duty at S and M has a Manager variant.
5. Scopes open under the old meanings (old S = Tech Lead + Developers; old M = all) keep their pinned rules until they close (D6). The evidence lists them.
