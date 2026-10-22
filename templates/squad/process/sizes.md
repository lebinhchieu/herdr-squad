# Sizes

## SIZE-1 Choosing a size
roles: manager
topic: sizes

The Manager proposes each scope's size with its signals, the PO confirms it at the goal check, and `size:` in `scope.md` records it. Scopes of a goal can differ. Work bigger than one L scope is a goal.

## SIZE-2 The three sizes
roles: manager, ba, team-lead, tech-lead
topic: sizes

| Size | Roles | Use when | Done = |
|---|---|---|---|
| **S** Quick fix | Manager, Tech Lead, Developers | 1–2 tasks, one repo, clear ticket, no new user-visible flow or risk flag | Tech Lead review PASS (`tl-review.md`) |
| **M** Feature | + BA, QA whitebox, QA blackbox, Team Lead | One scope, user-visible behaviour, spec or AC exist, about 3–6 tasks | QA whitebox PASS + QA blackbox PASS |
| **L** Full pod | As M | Unclear requirements or open questions, many tasks, cross-repo, ordering matters | QA whitebox PASS + QA blackbox PASS |

## SIZE-3 Design flag
roles: manager
topic: sizes

A `design:` line in `scope.md` (`yes|no`, default `no`) adds the Designer to a scope of any size. The Manager sets `design: yes` only when the PO asks; it never proposes it. It logs the answer in the iteration file.

## SIZE-4 Signals and risk flags
roles: manager
topic: sizes

- **Signals:** tasks, repos touched, user-visible change, open questions, risk flags; when they disagree, task count loses.
- **Risk flags force at least M:** DB migration or data change, breaking API or contract change, security or permissions, anything another team will see. A security fix with no behaviour change may stay S when the Manager states the reason as a signal and the PO confirms.
- When unsure, size up.

## SIZE-5a Business AC, S
roles: tech-lead
when: size = S
topic: sizes

Business AC are the ticket as written. A business doubt moves the scope to M ([SIZE-13]).

## SIZE-5b Business AC, M and L
roles: ba
when: size in M, L and qa-b = yes
topic: sizes

The BA owns the business AC and writes them with QA blackbox.

## SIZE-6a Plan owner, S
roles: tech-lead
when: size = S
topic: sizes

The Tech Lead owns the plan, in the plan file format used in every size. Each task file cites the on-demand rules its Developer needs: [GOAL-6b] integration, [PROMO-5] promotion, [REV-15] report deliverable.

## SIZE-6b Plan owner, M and L
roles: team-lead
when: size in M, L
topic: sizes

The Team Lead owns the plan, task order and assignment, in the same plan file and format in every size. A task of those kinds cites its rule in the task file ([GOAL-6b], [PROMO-5], [REV-15]) because the Developer does not carry them.

## SIZE-7a Code and test check, S
roles: tech-lead
when: size = S
topic: sizes

The Tech Lead reads the diff, runs the tests and lint, and checks the Developer's evidence ([REV-1]).

## SIZE-7b Code and test check, M and L
roles: qa-whitebox
when: size in M, L
topic: sizes

QA whitebox checks the code and the tests of every task ([REV-2]).

## SIZE-8a Behaviour check, S
roles: tech-lead
when: size = S
topic: sizes

There is no QA blackbox: the Developer saves Playwright or API evidence of each AC in `evidence.md`, and the Tech Lead checks it.

## SIZE-8b Behaviour check, M and L
roles: qa-blackbox
when: size in M, L and qa-b = yes
topic: sizes

QA blackbox checks the behaviour of every task on the running app.

## SIZE-9 UI design
roles: designer
when: design = yes
topic: sizes

The Designer designs the screens, states and flows of the scope's UI tasks, in every size.

## SIZE-10a Built UI against the design, S
roles: tech-lead
when: size = S and design = yes
topic: sizes

The Developer screenshots each screen and state in `evidence.md`; the Tech Lead checks them against the design.

## SIZE-10b Built UI against the design, M and L
roles: qa-blackbox
when: size in M, L and design = yes
topic: sizes

QA blackbox walks every screen and state of the design on the built UI.

## SIZE-11a Outside questions, S
roles: tech-lead
when: size = S
topic: sizes

The Tech Lead writes a question for an outside decision maker to the open-points place `project.md` names; the scope moves to M.

## SIZE-11b Outside questions, M and L
roles: ba
when: size in M, L
topic: sizes

The BA writes a question for an outside decision maker to the open-points place `project.md` names, never to that person, with the BA's proposed answer. The BA marks the affected work blocked and tells the Team Lead.

## SIZE-12 Duties of a missing role
roles: manager
topic: sizes

When a role is left out at a size, its duties move to the role named for that size; they are never dropped.

## SIZE-13 Moving up
roles: manager
topic: sizes

- **Up:** the Manager moves a scope up on its own when a business gap, risk flag, user-visible change or more tasks appear, and reports it at the check-in.
- It asks the Tech Lead for the `## Handover` section, spawns the missing roles (S to M: the Team Lead) with a briefing that points at it, and logs the move in `scope.md` and the iteration file. M to L changes no role.

## SIZE-14 Behaviour change found in S
roles: tech-lead
when: size = S
topic: sizes

A behaviour change or business doubt found in review moves the scope to M: tell the Manager.

## SIZE-15 Moving down
roles: manager
topic: sizes

**Down:** only at an iteration boundary, with the PO's OK. The Manager retires the roles that drop out (M to S: the Team Lead) and the plan returns to the Tech Lead.

## SIZE-16 Handover
roles: tech-lead, manager
topic: sizes

- **Handover on moving up:** the Tech Lead writes a `## Handover` section in the scope plan (decided, built, open); a joining Team Lead takes the plan over from it; the Manager's briefing to each joining role points at it.
- Built work passes the new size's checks before it counts as done.
- The Manager logs every size change in `scope.md` and the iteration file.

## SIZE-17a Joining after a move up, BA
roles: ba
topic: sizes

Joining a scope that moved up from S: start from the plan's `## Handover` section; the business AC so far were taken from the ticket as written, so check them first.

## SIZE-17b Joining after a move up, Team Lead
roles: team-lead
topic: sizes

Joining because a scope moved up from S: take over the existing plan file from the Tech Lead (same format) and read its `## Handover` section first.

## SIZE-17c Joining after a move up, QA whitebox
roles: qa-whitebox
topic: sizes

Joining a scope that moved up: work already built goes through your full check before it counts as done. Start from the plan's `## Handover` section.

## SIZE-17d Joining after a move up, QA blackbox
roles: qa-blackbox
topic: sizes

Joining a scope that moved up from S: test everything already built against the business AC; the Developer's `evidence.md` `## Behaviour` does not count as your check.

## SIZE-18 Extra hands
roles: manager
topic: sizes

Add a second BA, Tech Lead or QA when a scope is large.

## SIZE-19 QA blackbox off
roles: manager
topic: sizes

Propose `qa-b: no` (M or L, never with `design: yes`) when no task changes what a person using the product observes (a screen, CLI or hook output, exit code, generated file or report, message to the PO). State that signal; the PO confirms it at the goal check; `qa-b:` in `scope.md` records it.

## SIZE-20 Done without QA blackbox
roles: manager, ba, team-lead, tech-lead
when: size in M, L and qa-b = no
topic: sizes

With `qa-b: no` the M and L rows of [SIZE-2] read: Done = QA whitebox PASS. QA whitebox checks the Developer's `## Behaviour` against the business AC.

## SIZE-21 Spawn without QA blackbox
roles: manager
when: size in M, L and qa-b = no
topic: sizes

You spawn `ba`, `team-lead`, `tech-lead`, `qa-whitebox` and `token-coach`, not QA blackbox. A user-visible change found later: set `qa-b: yes` in `scope.md`, respawn the Developers and QA whitebox (their composed rules change), spawn QA blackbox with a briefing that points at the built tasks, and note it in the iteration file.
