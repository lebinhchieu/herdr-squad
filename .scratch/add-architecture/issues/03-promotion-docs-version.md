# 03 Docs, ADR, process version and promotion
Status: ready-for-agent
Type: task
Blocked by: 02

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; before HANDIN run `grep -rl '<touched path or changed string>' tests/` and run every hit (goldens included). QA whitebox runs the full suite once on the final sha. Commit this task file as the ticket at `.scratch/add-architecture/issues/NN-<slug>.md`, evidence at `.../NN-<slug>/evidence.md`. Brief: `$SCOPE_DIR/scope.md`, design `$SCOPE_DIR/tasks/architect-design.md` (the spec; PO confirmed it as written), plan `$SCOPE_DIR/iterations/1.md`. Defect class: none yet. Cite [PROMO-5] (promotion task: commit `promote.md` into the project docs by `/domain-modeling`; QA whitebox then checks it, [PROMO-8]) and [GOAL-6b]-style integration is not needed (lone scope). Run the full suite with `--tz` is QA whitebox's job on the final sha. Base: the passed sha of 02.

Touched files: `CONTEXT.md` (new term **Architect**, **architecture flag**; rewrite the Tech Lead `_Avoid_: architect` line; Designer/design flag cross-refs), new `docs/adr/0017-architect-role.md` (decision: optional role, PO-only flag, above Tech Lead, proposes irreversible choices, PO decides; notes that it amends the owner rows of ADR 0016), `README.md` (roles/flags), the process version bump and history snapshot per ADR 0005 (`skills/squad-process-update/changelog.md`, `skills/squad-process-update/history/`, version marker; check how the last bump was done), `$SCOPE_DIR/promote.md` kept by the Developer. Tests: whichever version/snapshot test exists (grep).

## Business AC
1. CONTEXT.md and ADR 0017 describe the role, flag and boundary vs Tech Lead consistently with the rules from 02; no contradiction with ADR 0010/0016 left unexplained.
2. README mentions the Architect and `architecture:` next to the Designer and `design:`.
3. Process version bumped with a history snapshot and changelog entry as ADR 0005 requires; a scope pinned to the old version is unaffected.
4. `promote.md` committed into the project docs as above; nothing else promoted.

## Technical AC (QA whitebox; agreed unless the Developer counters here)
T1. Version/snapshot tests pass; every grep hit under `tests/` for changed strings run.
T2. Glossary terms are used verbatim in the ADR; `grep -n -i architect CONTEXT.md` shows no stale `_Avoid_` for Tech Lead.
T3. Diff lists only the files above plus ticket/evidence files.

## Design notes
(Developer fills in.)
