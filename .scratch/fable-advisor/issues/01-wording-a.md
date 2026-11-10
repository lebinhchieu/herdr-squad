# 01: Wording fixes A (done/passed, reuse, dead clause, unattached rules)
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: W (one Developer, tickets 01, 02, 03 in order, same worktree)
Files: `templates/squad/process/*.md`, tests `tests/test_rules_wording.py`, `tests/test_rules_contract.py`
Source: `$SCOPE_DIR/tasks/review-findings.md` findings 1, 6, 8, 9 (read them; each names the rules).

## Business AC
1. "done" means merged only; wherever a rule means checked-and-passed it says "passed" (finding 1 list: LC-1, SIZE-16, SIZE-17c, START-1, START-19, TEAM-7, SPAWN-8a/8b, GOAL-3b/3c, COST-8). `grep` shows no remaining "done" meaning passed in `templates/squad/process/`.
2. REV-5a and EVID-5 are attached to the Developer (`roles:` line not empty); REV-22, LC-19, LC-19b still resolve to them.
3. START-5 / START-2a allow one Developer session for a queued run of tasks in one area, matching COST-6a, LC-6b and SPAWN-5a.
4. The clause "never suggest it to the PO" is gone from SPAWN-4/4a.
5. `squad-process lint` is clean; `tests/test_rules_wording.py` and `tests/test_rules_contract.py` pass, none skipped.
Also: this Developer's first task commits all drafts from `$SCOPE_DIR/tasks/NN-*.md` to `.scratch/fable-advisor/issues/` (FILE-11).

## Technical AC (QA whitebox; agreed with dev-w in design notes, amend there)
T1. Scope of edit: `git diff --name-only <base>..HEAD` lists only `templates/squad/process/*.md`, the two rules tests, and the ticket drafts under `.scratch/fable-advisor/issues/` (no `bin/`, no `agents/`, no `process.local.md`).
T2. Finding 1: the Developer lists every "done" hit in `templates/squad/process/` (`grep -nwi done`) in `evidence.md` with a keep/change verdict per hit. Kept hits mean merged (LC-27) or a project's own "done" test (LC-18). No rule ID in the finding 1 list is left unchecked.
T3. REV-5a and EVID-5: `roles:` is `dev` (or the file's equivalent value), and `python3 bin/squad-process rule REV-22`, `LC-19`, `LC-19b` still print and their `[REV-5a]`/`[EVID-5]` pointers resolve. A composed Developer rules file contains both rules (use `tests/rulesview.py` `composed("dev", ...)`).
T4. START-5/START-2a: wording matches COST-6a, LC-6b, SPAWN-5a; each is quoted in `evidence.md` next to the changed line. No rule outside the finding is reworded.
T5. SPAWN-4/4a: `grep -rn "never suggest it to the PO" templates/` returns nothing; SIZE-1 still says to propose optional roles.
T6. Tests: one new assertion per AC 1-4 in `tests/test_rules_wording.py` or `tests/test_rules_contract.py` (extend, no new file), each fails on the old text (Developer shows the failing run on the base commit, or states how it was checked). No matrices, no test of trivial text.
T7. Run: `python3 tests/test_rules_wording.py`, `tests/test_rules_contract.py`, `squad-process lint`, plus every hit of `grep -rl '<each changed rule ID or phrase>' tests/`. None skipped. Full suite not run by the Developer.
T8. Draft commit: the ten `NN-*.md` plus `review-findings.md` and `improvement-ideas.md` reach `.scratch/fable-advisor/issues/` (ticket files) with `Status:` lines intact and no content change except the Technical AC sections. Ticket drafts commit separately from the wording edit (own commit).
T9. Defect class carried forward (LC-8b): a changed rule keeps its ID; no rule is deleted or renumbered.
