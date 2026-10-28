# Teams and duty owners

## SIZE-1 Proposing the team
roles: manager
topic: sizes

The Manager proposes every optional role, picks and non-picks, in one table in one inbox item, with a signal per row and the team's models ([START-3b]). Nothing is spawned before the PO confirms; `team:` in `scope.md` records the confirmed team. Each scope of a goal gets its own table. When signals disagree, task count loses; when unsure, add the role.

| Role | Propose when | If the signals are silent |
|---|---|---|
| BA | open business question, unclear or contradicting AC, an outside decision maker's answer needed, output other teams see | out: the ticket is the AC |
| Tech Lead | a risk flag, cross-repo work, design choices several Developers depend on | out: the Developer's design notes |
| Team Lead | 4 or more tasks, order matters, parallel Developers | out: the Manager plans |
| QA whitebox | any task changes code or tests | in; out only for 2 tasks or fewer, one repo, no user-visible change, no risk flag, existing tests cover it |
| QA blackbox | a task changes what a person observes (screen, CLI or hook output, exit code, generated file or report, message to the PO), or a Designer is on the team | out: state "no observable change" |
| Designer | UI screens, states or flows are built or changed | out |
| Architect | an irreversible choice is likely (data model, new dependency, vendor), or a contract across components must be set before the plan | out |

- **Risk flags:** DB migration or data change, breaking API or contract change, security or permissions: Tech Lead and QA whitebox. Anything another team will see: also the BA. A business doubt: the BA. The PO may confirm without them; log that override in the iteration file.
- **A request for a role in the brief** counts as a confirmed pick and still appears in the table. A bigger job than one scope can finish under the Developer cap is a goal, not a bigger team.

## SIZE-2 Done, both QAs
roles: manager, ba, team-lead, tech-lead
when: qa-white = yes and qa-black = yes
topic: sizes

Done = every checker on the team has passed the task: QA whitebox PASS and QA blackbox PASS, and with a Designer the built-UI check ([SIZE-10b]). One PASS is never enough, nor are the Developer's own checks. Link each task's `evidence.md` in the plan.

## SIZE-5a Business AC, ticket
roles: manager
when: business-ac = ticket
topic: sizes

Business AC are the ticket as written. A business doubt: add the BA ([SIZE-13]).

## SIZE-5c Business AC, tested by QA blackbox
roles: qa-blackbox
aware: qa-whitebox
when: business-ac = ticket and qa-black = yes
topic: sizes

Business AC are the ticket as written, and you test against them. One a person cannot observe is a finding.

## SIZE-5b Business AC, BA
roles: ba
when: business-ac = ba and qa-black = yes
topic: sizes

The BA owns the business AC and writes them with QA blackbox.

## SIZE-6a Plan owner, Manager
roles: manager
when: plan-owner = manager
topic: sizes

The Manager owns the plan, task order and Developer spawning, in the plan file format every team uses: an exception to "never does a role's work". Each task file cites the on-demand rules its Developer needs: [GOAL-6b] integration, [PROMO-5] promotion, [REV-15] report deliverable.

## SIZE-6b Plan owner, Team Lead
roles: team-lead
when: plan-owner = team-lead
topic: sizes

The Team Lead owns the plan, task order and assignment, in the same plan file and format the Manager uses. A task of those kinds cites its rule in the task file ([GOAL-6b], [PROMO-5], [REV-15]) because the Developer does not carry them.

## SIZE-6c Developer duties
roles: manager
when: plan-owner = manager
topic: sizes

Start each task file with `Duties:` (a respawned Developer reads it), copied from the `duties:` line of your header: who owns design notes, technical AC, business AC, `promote.md` and the full suite for this team. A risk flag, user-visible change or business doubt found while building: `BLOCKED <task>` ([SIZE-14]).

## SIZE-7a Code and test check, Manager
roles: manager
when: code-check = manager
topic: sizes

Confirm `evidence.md` and its `## Review` exist ([REV-1]); do not redo the Developer's checks.

## SIZE-7b Code and test check, QA whitebox
roles: qa-whitebox
when: code-check = qa-white
topic: sizes

QA whitebox checks the code and the tests of every task ([REV-2]).

## SIZE-8a Behaviour check, Manager
roles: manager
when: behaviour-check = manager
topic: sizes

No QA is on the team: confirm `evidence.md` `## Behaviour` holds Playwright or API evidence of each AC.

## SIZE-8b Behaviour check, QA blackbox
roles: qa-blackbox
when: behaviour-check = qa-black
topic: sizes

QA blackbox checks the behaviour of every task on the running app.

## SIZE-9 UI design
roles: designer
when: design = yes
topic: sizes

The Designer designs the screens, states and flows of the scope's UI tasks.

## SIZE-9a Architecture
roles: architect
when: architecture = yes
topic: sizes

Deliver `$SCOPE_DIR/architecture.md` with a `Status: draft|final` line, holding:
- the components and modules the scope touches
- boundaries and seams
- contracts and data shapes
- constraints the plan and the technical design must follow
- each irreversible choice (data model, new dependency, vendor) with its options and your recommendation

Draft ADR text in `$SCOPE_DIR/tasks/` ([FILE-11]). Before you recommend an irreversible choice, consult the advisor and leave the [LC-25] note. You write no code and check no built code.

## SIZE-10a Built UI against the design, Manager
roles: manager
when: ui-check = manager and design = yes
topic: sizes

Confirm `evidence.md` holds a screenshot of each screen and state of the design.

## SIZE-10b Built UI against the design, QA blackbox
roles: qa-blackbox
when: ui-check = qa-black and design = yes
topic: sizes

QA blackbox walks every screen and state of the design on the built UI.

## SIZE-11a Outside questions, Manager
roles: manager
when: doubt-owner = manager
topic: sizes

Write a question for an outside decision maker to the open-points place `project.md` names, never to that person; add the BA ([SIZE-13]).

## SIZE-11b Outside questions, BA
roles: ba
when: doubt-owner = ba
topic: sizes

The BA writes a question for an outside decision maker to the open-points place `project.md` names, never to that person, with the BA's proposed answer. The BA marks the affected work blocked and tells the plan owner.

## SIZE-13 Adding a role
roles: manager
topic: sizes

- **Add:** on a late signal the Manager adds the role on its own: business doubt (BA), risk flag or migration (Tech Lead, QA whitebox if absent), user-visible change (QA blackbox), 4 or more tasks or order that matters (Team Lead). UI work (Designer) and an irreversible choice (Architect) wait for the PO's yes. Report it at the check-in.
- Run `squad-team add <role>` (`--po-ok` for the Designer or Architect, after the PO's yes): it edits `team:` and prints who to respawn. Write the `## Handover` when a duty owner changes, brief the joiner with it, respawn the listed roles, log the change in the iteration file.

## SIZE-14 Late signal found while building
roles: manager
topic: sizes

A user-visible change, business doubt or risk flag found while building reaches you as `BLOCKED <task>` from the Developer, or as `ASK` from a checker. Add the role it needs ([SIZE-13]); the duty owner chain ([SIZE-22]) names who acts meanwhile.

## SIZE-16 Handover
roles: manager
topic: sizes

- **Handover on adding a role:** the Manager writes a `## Handover` section in the scope plan (decided, built, open); a joining role starts from it, and the Manager's briefing to each joining role points at it.
- Built work passes the new team's checks before it counts as done.
- The Manager logs every team change in `scope.md` and the iteration file.

## SIZE-17a Joining a team, BA
roles: ba
when: ba = yes
topic: sizes

Joining a scope already under way: start from the plan's `## Handover` section; the business AC so far were the ticket as written, so check them first.

## SIZE-17b Joining a team, Team Lead
roles: team-lead
when: team-lead = yes
topic: sizes

Joining a scope already under way: take over the existing plan file from the Manager (same format) and read its `## Handover` section first.

## SIZE-17c Joining a team, QA whitebox
roles: qa-whitebox
when: qa-white = yes
topic: sizes

Joining a scope already under way: work already built goes through your full check before it counts as done. Start from the plan's `## Handover` section.

## SIZE-17d Joining a team, QA blackbox
roles: qa-blackbox
when: qa-black = yes
topic: sizes

Joining a scope already under way: test everything already built against the business AC; the Developer's `evidence.md` `## Behaviour` does not count as your check.

## SIZE-17e Joining a team, Tech Lead
roles: tech-lead
when: tech-lead = yes
topic: sizes

Joining a scope already under way: start from the plan's `## Handover` section; the technical AC so far were written by QA whitebox with the Developers, or by the Developers alone, so check them first.

## SIZE-18 Extra hands
roles: manager
when: plan-owner = team-lead
topic: sizes

Add a second BA, Tech Lead or QA when the scope is large.

## SIZE-21a Spawning the confirmed team
roles: manager
topic: sizes

Spawn only the roles in `team:` of `scope.md`, plus Developers and the Token Coach. `squad-spawn` refuses a role not on the team; its duties pass along the chain ([SIZE-22]) and are never dropped.

## SIZE-22 Duty owner chains
roles: manager
topic: sizes

The first present role in each chain owns the duty. Every chain ends at the Manager, a Developer or the ticket, so no duty is orphaned. The `duties:` line of your header gives the owners for this team.

| Duty | Owner chain |
|---|---|
| Plan, Developer spawning, routine messages, 3 returns | Team Lead, then Manager |
| Design notes | Tech Lead, then Developer (inside `architecture.md` with an Architect) |
| Technical AC | Tech Lead, then QA whitebox with the Developer, then Developer |
| Business AC | BA (with QA blackbox when present), then the ticket as written |
| Code check | QA whitebox, then Developer's `## Review` confirmed by Tech Lead, then by Manager |
| Behaviour check | QA blackbox, then QA whitebox checking `## Behaviour`, then Manager confirming `evidence.md` |
| Built-UI check (with a Designer) | QA blackbox, then Manager confirming the screenshots |
| Hand in to | the QAs on the team, then Team Lead, then Manager |
| Full suite, `promote.md` | Tech Lead, then QA whitebox, then Developer |
| Migration, contract change, risk flag | Tech Lead, then Manager (adds the Tech Lead) |
| Business doubt, outside question | BA, then Manager (adds the BA) |
| Irreversible design choice | Architect, then Tech Lead, then Manager propose; the PO decides every time |

You escalate each irreversible choice to the PO ([WHO-2e]).

## SIZE-23b Technical AC, QA whitebox
roles: qa-whitebox
when: tech-ac = qa-white
topic: sizes

Write the technical AC before work starts (tests that must exist, lint clean, patterns followed, security checks, performance limits) and agree them with the Developer in the task file.

## SIZE-23c Architecture in the technical AC, QA whitebox
roles: qa-whitebox
when: qa-white = yes and architecture = yes
topic: sizes

Check each task's diff against `architecture.md`; a difference is a finding. When you own the technical AC, add "conforms to `architecture.md`" to it.

## SIZE-23d Architecture in the technical AC, Tech Lead
roles: tech-lead
when: tech-ac = tech-lead and architecture = yes
topic: sizes

Put "conforms to `architecture.md`" in each task's technical AC and check the diff against it; a difference is a finding.

## SIZE-24b promote.md, QA whitebox
roles: qa-whitebox
when: promote-owner = qa-white
topic: sizes

Keep `promote.md` as in [PROMO-2], including the lasting business rules and glossary terms the ticket and the tests show.
