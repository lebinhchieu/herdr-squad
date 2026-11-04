# 18 promotion
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Rules: [PROMO-5] and [PROMO-4] apply (run `squad-process rule PROMO-5`).
Status: ready-for-agent
Iteration: 2 (last task of the scope)
Blocked by: every other ticket passed

## What the PO gets
What must outlive the scope is in the project docs (README section for `squad-board`, any ADR or glossary change not yet in 01).

## Rules
- Commit `promote.md` content into the project docs on the integration branch; QA whitebox checks it ([PROMO-8]). With nothing left to promote, `promote.md` says so and this task is dropped.
- Business AC: none.

## Touched files
- Edit: `README.md`, `docs/` pages named by `promote.md`. No code.

## Comments
