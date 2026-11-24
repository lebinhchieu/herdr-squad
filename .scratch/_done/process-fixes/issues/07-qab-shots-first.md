# Task 07: Fix 4: QA blackbox checks from the Developer's committed shots first

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`.

Status: ready
Source: process audit finding 4 (`git show squad/plugin/process-audit/plugin-dev-process-audit-6:.scratch/process-audit/report.md`, read only finding 4). Chieu E1 (a): lands in the plugin rule, not an overlay.
Files: templates/squad/process/review.md (REV-9, REV-11 if needed), tests that quote them (golden/composed outputs)
Ticket: commit this file's content as `.scratch/process-fixes/issues/07-qab-shots-first.md` in your first commit.
Base: main. Work in your own worktree (squad-spawn --repo). No merge, no version bump (task 09 does it).

## AC
- AC1 REV-9 says: QA blackbox first checks each business AC from the Developer's committed shots and text in `evidence.md` `## Behaviour` (EVID-2a). It runs the app only for an AC whose shot is missing, unclear, or shows the wrong state, and for the unhappy paths no shot covers.
- AC2 REV-11: `qa-b.md` says per AC whether it was checked from a committed shot or by a live run (one word).
- AC3 Wording is short, one rule stated once (no copy into other files), uses only existing rule IDs for pointers.
- AC4 Rule lint passes (`squad-process lint` / the repo's rule tests); touched tests and `grep -rl 'REV-9\|REV-11' tests/` hits pass; nothing newly skipped.
- AC5 Evidence note: the exact before/after rule text, so Chieu can approve the wording.

## Design notes
Dev writes them here before building (touched files, test harness).
