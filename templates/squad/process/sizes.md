# Sizes

## SIZE-1 Choosing a size
roles: manager
topic: sizes

The Manager proposes each scope's size with its signals, the PO confirms it at the goal check, and `size:` in `scope.md` records it. Scopes of a goal can differ. Work bigger than one L scope is a goal. The size proposal carries the team's models ([START-3b]).

## SIZE-2 The three sizes
roles: manager, ba, team-lead, tech-lead
topic: sizes

| Size | Roles | Use when | Done = |
|---|---|---|---|
| **S** Quick fix | Manager, Developers | 1–2 tasks, one repo, nothing user-visible, no risk flag, existing tests cover it | The Developer's checks + `evidence.md` + `## Review` (one fresh-context Opus review subagent before `HANDIN`); the Manager only confirms both exist |
| **M** Feature | + QA whitebox, QA blackbox | 1–6 tasks, user-visible, clear ticket or AC, no business question, no risk flag | QA whitebox PASS + QA blackbox PASS |
| **L** Full pod | Every role: + BA, Team Lead, Tech Lead | Business questions, any risk flag, cross-repo, ordering matters | QA whitebox PASS + QA blackbox PASS |

## SIZE-3 Design flag
roles: manager
topic: sizes

A `design:` line in `scope.md` (`yes|no`, default `no`) adds the Designer to a scope of any size. The Manager sets `design: yes` only when the PO asks; it never proposes it. It logs the answer in the iteration file.

## SIZE-4 Signals and risk flags
roles: manager
topic: sizes

- **Signals:** tasks, repos touched, user-visible change, open questions, risk flags; when they disagree, task count loses.
- **Every risk flag forces L:** DB migration or data change, breaking API or contract change, security or permissions, anything another team will see.
- When unsure, size up.

## SIZE-5a Business AC, S
roles: manager
when: size = S
topic: sizes

Business AC are the ticket as written. A business doubt moves the scope to L ([SIZE-13]).

## SIZE-5c Business AC, M
roles: manager, qa-blackbox
aware: qa-whitebox
when: size = M
topic: sizes

Business AC are the ticket as written, and QA blackbox tests against them. A business doubt moves the scope to L ([SIZE-13]).

## SIZE-5b Business AC, L
roles: ba
when: size = L and qa-b = yes
topic: sizes

The BA owns the business AC and writes them with QA blackbox.

## SIZE-6a Plan owner, S and M
roles: manager
when: size in S, M
topic: sizes

The Manager owns the plan, task order and Developer spawning, in the plan file format used in every size: an exception to "never does a role's work". Each task file cites the on-demand rules its Developer needs: [GOAL-6b] integration, [PROMO-5] promotion, [REV-15] report deliverable.

## SIZE-6c Developer duties, S
roles: manager
when: size = S
topic: sizes

Manager: start each task file with `Duties:` (a respawned Developer reads it): put design notes in the task file; technical AC are yours; business AC are the ticket; keep `promote.md`; risk flag, user-visible change or business doubt: `BLOCKED <task>` ([SIZE-14]).

## SIZE-6d Developer duties, M
roles: manager
when: size = M
topic: sizes

Manager: start each task file with `Duties:`: put design notes in the task file; technical AC are QA whitebox's; business AC are the ticket; risk flag or business doubt: `BLOCKED <task>` ([SIZE-14]).

## SIZE-6b Plan owner, L
roles: team-lead
when: size = L
topic: sizes

The Team Lead owns the plan, task order and assignment, in the same plan file and format in every size. A task of those kinds cites its rule in the task file ([GOAL-6b], [PROMO-5], [REV-15]) because the Developer does not carry them.

## SIZE-7a Code and test check, S
roles: manager
when: size = S
topic: sizes

Confirm `evidence.md` and its `## Review` exist ([REV-1]); do not redo the Developer's checks.

## SIZE-7b Code and test check, M and L
roles: qa-whitebox
when: size in M, L
topic: sizes

QA whitebox checks the code and the tests of every task ([REV-2]).

## SIZE-8a Behaviour check, S
roles: manager
when: size = S
topic: sizes

There is no QA blackbox: confirm `evidence.md` `## Behaviour` holds Playwright or API evidence of each AC.

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
roles: manager
when: size = S and design = yes
topic: sizes

Confirm `evidence.md` holds a screenshot of each screen and state of the design.

## SIZE-10b Built UI against the design, M and L
roles: qa-blackbox
when: size in M, L and design = yes
topic: sizes

QA blackbox walks every screen and state of the design on the built UI.

## SIZE-11a Outside questions, S and M
roles: manager
when: size in S, M
topic: sizes

Write a question for an outside decision maker to the open-points place `project.md` names, never to that person; the scope moves to L.

## SIZE-11b Outside questions, L
roles: ba
when: size = L
topic: sizes

The BA writes a question for an outside decision maker to the open-points place `project.md` names, never to that person, with the BA's proposed answer. The BA marks the affected work blocked and tells the Team Lead.

## SIZE-12 Duties of a missing role
roles: manager
topic: sizes

When a role is left out at a size, its duties move to the role named for that size ([SIZE-22]); they are never dropped.

## SIZE-13 Moving up
roles: manager
topic: sizes

- **Up:** the Manager moves a scope up on its own when a business doubt, risk flag, user-visible change or more tasks appear, and reports it at the check-in. S to M: a user-visible change. Business doubt, risk flag, cross-repo or ordering: straight to L.
- It writes the `## Handover` section in the plan, spawns the missing roles (S to M: QA whitebox, QA blackbox; to L: BA, Team Lead, Tech Lead) with a briefing that points at it, and logs the move in `scope.md` and the iteration file.

## SIZE-14 Behaviour change found in S
roles: manager
when: size = S
topic: sizes

A user-visible change found while building moves the scope to M; a business doubt or risk flag moves it to L. The Developer tells you with `BLOCKED <task>`.

## SIZE-15 Moving down
roles: manager
topic: sizes

**Down:** only at an iteration boundary, with the PO's OK. The Manager retires the roles that drop out (L to M: BA, Team Lead, Tech Lead; M to S: both QAs) and keeps the plan.

## SIZE-16 Handover
roles: manager
topic: sizes

- **Handover on moving up:** the Manager writes a `## Handover` section in the scope plan (decided, built, open); a joining role starts from it, and the Manager's briefing to each joining role points at it.
- Built work passes the new size's checks before it counts as done.
- The Manager logs every size change in `scope.md` and the iteration file.

## SIZE-17a Joining after a move up, BA
roles: ba
topic: sizes

Joining a scope that moved up: start from the plan's `## Handover` section; the business AC so far were the ticket as written, so check them first.

## SIZE-17b Joining after a move up, Team Lead
roles: team-lead
topic: sizes

Joining because a scope moved up: take over the existing plan file from the Manager (same format) and read its `## Handover` section first.

## SIZE-17c Joining after a move up, QA whitebox
roles: qa-whitebox
topic: sizes

Joining a scope that moved up: work already built goes through your full check before it counts as done. Start from the plan's `## Handover` section.

## SIZE-17d Joining after a move up, QA blackbox
roles: qa-blackbox
topic: sizes

Joining a scope that moved up from S: test everything already built against the business AC; the Developer's `evidence.md` `## Behaviour` does not count as your check.

## SIZE-17e Joining after a move up, Tech Lead
roles: tech-lead
topic: sizes

Joining a scope that moved up to L: start from the plan's `## Handover` section; the technical AC so far were written by QA whitebox with the Developers, so check them first.

## SIZE-18 Extra hands
roles: manager
when: size = L
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

With `qa-b: no` there is one checker, QA whitebox: Done = QA whitebox PASS. Wherever a rule says "both checkers", "both QAs", "QA whitebox + QA blackbox" or "PASS + QA blackbox PASS" ([SIZE-2], the task-done owner table, the merge and check-in rules), read QA whitebox alone. It checks the Developer's `## Behaviour` against the business AC.

## SIZE-21a Spawn without QA blackbox, M
roles: manager
when: size = M and qa-b = no
topic: sizes

You spawn Developers, `qa-whitebox` and `token-coach`, not QA blackbox. A user-visible change found later: set `qa-b: yes` in `scope.md`, respawn the Developers and QA whitebox (their composed rules change), spawn QA blackbox with a briefing that points at the built tasks, and note it in the iteration file.

## SIZE-21b Spawn without QA blackbox, L
roles: manager
when: size = L and qa-b = no
topic: sizes

You spawn `ba`, `team-lead`, `tech-lead`, `qa-whitebox` and `token-coach`, not QA blackbox. A user-visible change found later: as [SIZE-21a], with the Team Lead's Developers respawned.

## SIZE-22 Duty owners by size
roles: manager
topic: sizes

| Duty | S | M | L |
|---|---|---|---|
| Plan, Developer spawning | Manager | Manager | Team Lead |
| Design notes | Developer | Developer | Tech Lead |
| Technical AC | Developer | QA whitebox with the Developer | Tech Lead with QA whitebox |
| Business AC | ticket as written | ticket as written | BA with QA blackbox |
| Code check | Developer + Opus review subagent | QA whitebox | QA whitebox |
| Behaviour check | Developer's `evidence.md` | QA blackbox | QA blackbox |
| Hand in to / done told to | Manager / Manager | QAs / Manager | QAs / Team Lead |
| Full suite | Developer | QA whitebox | Tech Lead |
| `promote.md` | Developer | QA whitebox | Tech Lead, BA |
| Migration, contract change, risk flag, business doubt | Manager moves to L | Manager moves to L | Tech Lead, BA |
| Irreversible design choice | Manager | Manager | Tech Lead |
| 3 returns | Manager | Manager | Team Lead |

## SIZE-23b Technical AC, M
roles: qa-whitebox
when: size = M
topic: sizes

Write the technical AC before work starts (tests that must exist, lint clean, patterns followed, security checks, performance limits) and agree them with the Developer in the task file.

## SIZE-24b promote.md, M
roles: qa-whitebox
when: size = M
topic: sizes

Keep `promote.md` as in [PROMO-2], including the lasting business rules and glossary terms the ticket and the tests show.
