# CLAUDE.md

## Agent skills

### Issue tracker

Issues and specs live as local markdown in `.scratch/` (committed with the repo).

- One feature per directory: `.scratch/<feature-slug>/`.
- The spec is `.scratch/<feature-slug>/spec.md`.
- Tickets go one per file at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`. Never put several tickets in one file.
- Triage state is a `Status:` line near the top of each file, using a label from the table below.
- Comments and history go at the bottom of the file, under `## Comments`.
- **"Publish to the issue tracker"** means: create the file under `.scratch/<feature-slug>/`.
- **"Fetch the relevant ticket"** means: read the file at the path or number the user gives.
- **Wayfinding (`/wayfinder`):**
  - The map is `.scratch/<effort>/map.md`.
  - Each child ticket is `issues/NN-<slug>.md`, with a `Type:` line (research / prototype / grilling / task) and a `Status:` line (claimed / resolved).
  - Blocking is a `Blocked by: NN, NN` line. A ticket is unblocked once everything it lists is resolved.
  - The frontier is the open, unblocked, unclaimed tickets; the lowest number goes first.
  - To claim, set `Status: claimed` before any work.
  - To resolve, add `## Answer`, set `Status: resolved`, and add a pointer to the map's Decisions-so-far.

### Triage labels

The default vocabulary, written as the `Status:` value:

| Label | Meaning |
|---|---|
| `needs-triage` | Maintainer needs to evaluate this issue |
| `needs-info` | Waiting on the reporter for more information |
| `ready-for-agent` | Fully specified, ready for an AFK agent |
| `ready-for-human` | Requires human implementation |
| `wontfix` | Will not be actioned |

### Domain docs

Single-context: one `CONTEXT.md` and `docs/adr/` at the repo root.

- Before exploring, read `CONTEXT.md` and any ADRs in `docs/adr/` that touch the area you're working in. If they don't exist, carry on and don't mention it. `/domain-modeling` creates them when terms or decisions get settled.
- Use the glossary's terms in issue titles, test names and proposals. A concept missing from the glossary is either invented language or a real gap; note the gap for `/domain-modeling`.
- If your output contradicts an ADR, say so explicitly instead of overriding it.

## Running tests

- Runner: `python3 tests/run_suite.py --receipt <dir> --if-changed <task base>`. Integration and promotion tasks and the sha the PO merges use `--tz` instead: nothing skipped.
- Start it in the background and wait as in the Suites bullet of `agents/dev.md`. Never `pgrep -f` or `pkill -f run_suite`: it kills other agents' runs.
- Commit every fix before a run; never kill and restart one.
- Interim, until scope board-flakes closes: if `test_board_sequence` and `test_board_page` are the only failures, a solo pass of each, saved next to the receipt, counts as green.
