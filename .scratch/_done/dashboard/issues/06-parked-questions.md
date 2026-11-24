# 06 parked questions
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Status: ready-for-agent
Iteration: 1
Blocked by: 02, 03, 01
Feature: 13 (`tasks/features.md`)

## What the PO gets
Park a question to clear "Needs you" without answering it.

## Rules
- `squad-inbox park|unpark|resolve` write `open-questions.md` in the folder of the question's level (scope, goal or squad); entries `## Q<n>` with `Status: parked | resolved`, `Parked:`, text, optional `Blocks:`, `From:`, `Resolved:`. Hand edits are read; a broken entry is skipped with a warning.
- Parking does not answer; the blocked work stays blocked. The page reads these files and never writes them; it shows the park/unpark/resolve command text as copy-only.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T06.AC1** Given 3 open questions and the PO parks 1 with the command, then Needs you lists 2 open and "Parked (1)", the needs-you count is 2, and the parked row names what it blocks and since when.
- **T06.AC2** Given `unpark`, then the count is 3.
- **T06.AC3** Given `resolve`, then the row leaves Parked.
- **T06.AC4** Given a parked question in S3 and the choice S1, then it does not show; a squad-level parked question shows under every choice; a goal choice includes its scopes' parked questions; closed scopes are read from `_done/`.
- **T06.AC5** Given a file with one broken entry, then "open-questions.md unreadable: <path>" shows and the other entries still show.
- **T06.AC6** Given a parked row, then the command text for unpark and resolve is shown and the copy control puts exactly that text on the clipboard.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Modules M4 + the `tickets:` line of M11 (one Developer: both edit `agents/manager.md` and the process).
- New: none.
- Edit: `bin/squadinbox.py` (`park`, `unpark`, `resolve`), `bin/squad-inbox` only if flags need wiring, `agents/manager.md`, `templates/squad/process/*.md` + the process version bump (ADR 0005), `templates/scope/scope.md` (the optional `tickets: <feature-slug>` line, M11), `docs/adr/0007-inbox-sits-on-escalations.md` is edited by ticket 01, not here.
- Tests (new): `tests/test_squadinbox_park.py`. Run `grep -rl` over `tests/` for every changed template text and run each hit (goldens included), per `CLAUDE.md`.
- Ticket 07 reads the `tickets:` line; it does not edit the template.

## Comments
