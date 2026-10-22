# 07 Two retro rules in `agents/dev.md`

Status: done
Blocked by: none (base: main at dd88dec)
Files: `agents/dev.md`, `tests/test_instructions.py`. Nothing else: not `templates/squad/process.md`, not the QA role files.
Size: M. This is the scope's last task and its integration branch (one task, no separate integration task). The PO approved the change (iterations/1.md, "Role-instruction changes proposed").

Two things went wrong in this scope. A Developer's report lived only in its worktree, which QA blackbox cannot read. A fix landed after a PASS and no QA saw it.

## Business AC
- A QA blackbox can always open the Developer's report or document deliverable in the evidence folder, at the sha that was handed in.
- A commit made after a PASS is seen by both QAs before the task counts as done.

## Technical AC
- **D1 Evidence copy.** One bullet in `## What you do` of `agents/dev.md`, next to the **Hand in** bullet: a report or doc deliverable (an audit, a study, a design note) is also copied into `$SCOPE_DIR/evidence/<task>/` at the sha handed in, and the `HANDIN` names the copied path. Reason as one short clause (QA blackbox cannot read worktrees).
- **D2 Diff check.** One bullet next to D1: any commit after a PASS goes back to both QAs as `HANDIN <task>: diff check <passed sha>..<new sha>`; they check that diff only, not the whole task again. Say who acts (the Developer), when (before telling the Team Lead the task is done) and the outcome.
- **D3 No duplication.** `process.md` does not say either rule today (checked: Task lifecycle has "a blackbox return is merged in afterwards" and "QA checks the receipt (same sha as the HANDIN)", neither covers a post-PASS commit or a copied report). Do not edit `process.md`. Where a rule leans on it, add a pointer of at most one clause (`process.md` → Task lifecycle, Safety), never a copy. Re-grep `process.md` for "evidence" and "after a PASS" on the final sha and say in `dev-evidence.md` what you found.
- **D4 Writing rules dev.md already uses.** One rule per bullet, who acts, when, the limit; no history, dates or incident names; at most 60 words per bullet; no new section. Match the tone of the neighbouring bullets. `agents/dev.md` stays under about 720 words (689 now).
- **D5 Tests.** Add one test to `tests/test_instructions.py` (existing style): `agents/dev.md` contains both rules (the copied-evidence path `evidence/<task>/` with "handed in" or "hand in", and the words "diff check" with "both QAs"). Existing tests stay green, in particular `tests/test_instructions.py`, `tests/test_process_citations.py` (a `process.md` → <Section> citation must resolve), `tests/test_process_writing.py`.
- **D6 Overlap (remove-board).** Checked by the Tech Lead: remove-board edits `agents/manager.md` only (its issue 05, Part B), and its R-15 asks that no `agents/*.md` mentions a board. `agents/dev.md` has no board word today. Do not add one. `dev-evidence.md` lists `git diff --stat main` and repeats `git grep -n -i -w board -- agents/dev.md` (no output expected). If `agents/dev.md` also changed on main since dd88dec, say so.
- **D7 Suite.** Per CLAUDE.md "Running tests": `python3 tests/run_suite.py --receipt <dir> --tz` once on the final sha (the sha the PO merges: nothing skipped), in the background, receipt saved in the evidence folder.
- **D8 Ticket files.** Commit this ticket and set its `Status:` to `done` with a `## Comments` line on the branch. The root copy of `.scratch/audit-token/issues/07-*.md` is removed by the PO before the merge, as for AT-04.
- **D9 Real check.** In `dev-evidence.md`, quote the two new bullets and count their words.

## Out of scope
QA role files (`agents/qa-*.md`): the `HANDIN … diff check` line tells them what to do. Any `process.md` change. Anything on trial overrides.

## Comments
- Dev: both bullets added to agents/dev.md, test added; suite receipt in evidence/AT-07/.
