# 02 Goal-status line names the goals and has no bare type word
Status: building (plugin-dev-tl-wake-status-3)
Duties: plan-owner=team-lead, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Files: bin/squad-watchdog (team_lead_nudge_text, the goal-status sentence near line 333), tests/test_squad_watchdog.py; this ticket file committed to .scratch/tl-wake-status/issues/02-goal-status-line-names-goals.md
Depends: 01 (passed). Base: branch squad/plugin/tl-wake-status/plugin-dev-tl-wake-status-1 at b779afd (unmerged). Plan: `$SCOPE_DIR/iterations/2.md`.
Evidence: .scratch/tl-wake-status/issues/02-goal-status-line-names-goals/evidence.md

## What and why
Two QA follow-ups of 01, Chieu chose to fix them (E2 (b)). The Team Lead nudge asks for "one line (`STATUS`)": a `STATUS` with no task id breaks MSG-2, and the asked line does not name which goal it is about.

## Business AC
- AC1 Scope home, live Team Lead, an `in progress` goal and no open ticket: the nudge asks the Team Lead to send the Manager one line per open goal, naming its id, in the form `goal <id> done` or `goal <id> blocked: <reason>`, with each open (not `blocked`) goal id filled in, e.g. `goal 1 done`. The word `STATUS` no longer appears in the nudge.
- AC2 Everything else 01 built stays: open tickets listed, the line asked only when no ticket is open, `blocked` goals only named as the Manager's, "you never edit goals.md", Manager wording and fallback unchanged.

## Technical AC
- AC3 The 01 tests for AC1/AC2 are updated to the new text (pin the goal id in the asked line and the absence of `STATUS`); no new test file; `tests/test_squad_watchdog.py` all pass.
- AC4 SQ-10: run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and the `grep -rl "squad-watchdog\|team_lead_nudge" tests/` hits; quote results in `## Behaviour`.
- AC5 No new version bump: 0.10.3 from 01 is unreleased and covers this scope. If the docstring "Who is told" quotes the asked line, update it to match.
- AC6 Live check (QA blackbox): as 01 AC9, `squad-watchdog tick` on a scratch scope home; `watchdog.log` shows the nudge with `goal 1 done` / `goal 1 blocked: <reason>` and no `STATUS`.

## Evidence
`evidence.md` next to the committed ticket; QA cells assembled (EVID-2d) before the Developer is retired.
