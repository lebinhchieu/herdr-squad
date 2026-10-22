# Promotion: knowledge goes up to the project

## PROMO-1 Promotion
roles: manager
aware: tech-lead
topic: promotion

A task, reviewed and merged like any other, writes what must outlive a scope or goal into the project docs before it closes.

## PROMO-2 Keep promote.md
roles: tech-lead
when: size = L
topic: promotion

Keep `promote.md` in your scope folder while the work runs: each lasting decision, glossary term, business rule or ADR candidate, with its `project.md` target file and the exact wording. In a goal the facts go to `shared/decisions.md` instead ([PROMO-6]).

## PROMO-3a Business rules, BA
roles: ba
when: size = L
topic: promotion

Hand the Tech Lead the lasting business rules and glossary terms the scope found, one line each, so they reach `promote.md` (or, in a goal, `shared/decisions.md`). Business knowledge belongs in the project docs, not in the squad.

## PROMO-3b Promote.md, S
roles: manager
when: size = S
topic: promotion

Before the last task passes, check the Developer's `promote.md` ([PROMO-2]; the `Duties:` line carries it): it holds the lasting business rules and glossary terms the ticket shows, with no BA to hand them over.

## PROMO-4 Promotion of a lone scope
roles: manager
aware: tech-lead
when: goal = no
topic: promotion

The scope's last task: a Developer commits `promote.md` to the project docs on the integration branch, by the project's rule for editing those files (`project.md`); the PO merges it with the code. With nothing to promote, `promote.md` says so and there is no task.

## PROMO-5 Promotion task, Developer
roles: team-lead
when: size = L
topic: promotion

A promotion task commits `promote.md` into the project docs, following the rule `project.md` names for editing them. It is handed in like any task.

## PROMO-5b Promotion task, S and M
roles: manager
when: size in S, M
topic: promotion

Cite [PROMO-5] in the task file of a promotion task; its Developer commits `promote.md` into the project docs, and at M QA whitebox then checks it ([PROMO-8]).

## PROMO-6 Promotion of a goal
roles: manager
aware: tech-lead
when: goal = yes
topic: promotion

- Scopes do not promote at their own close; lasting facts go to `shared/decisions.md`.
- Once, in the last scope, a promotion task turns `decisions.md` and the summaries into project-doc edits: the owner of `promote.md` ([SIZE-22]) writes `goals/<goal>/promote.md`, a Developer commits it on that scope's integration branch.
- The goal Manager adds the promotion task in the last scope; when it passes, it adds `promoted: <date> <commit>` to `goal.md`.

## PROMO-7 Abandoned goal
roles: manager
when: goal = yes
topic: promotion

An abandoned goal keeps its knowledge in `goals/_done/<goal>/shared/`. `squad-close --goal` refuses while `decisions.md` has entries and `goal.md` has no `promoted:` line, unless the PO overrides with `--force`.

## PROMO-8 Check a promotion
roles: qa-whitebox
when: size in M, L
topic: promotion

Check the project-doc edits of a promotion task like any other change: they match `promote.md`, follow the project's rule for editing those files, and contain nothing the scope did not decide.
